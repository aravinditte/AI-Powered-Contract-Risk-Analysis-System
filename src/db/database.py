"""
SQLite Database Layer

Handles contract storage, analysis results, review queue,
and audit trail. Uses SQLite for zero-cost local persistence.
"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = str(Path(__file__).parent.parent.parent / "data" / "contracts.db")


def get_db_path() -> str:
    return DB_PATH


def set_db_path(path: str):
    global DB_PATH
    DB_PATH = path


@contextmanager
def get_connection():
    """Get a database connection with WAL mode for concurrent access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contracts (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploaded',
                language TEXT DEFAULT 'en',
                file_size INTEGER,
                text_content TEXT,
                overall_risk TEXT,
                overall_score REAL,
                analysis_date TEXT,
                report_json TEXT
            );

            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                detecting_layer TEXT NOT NULL,
                clause_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                clause_text TEXT,
                explanation TEXT,
                suggested_fix TEXT,
                cross_validated INTEGER DEFAULT 0,
                agreeing_layers TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                reviewer_name TEXT NOT NULL,
                decision TEXT NOT NULL,
                comments TEXT,
                review_date TEXT NOT NULL,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                contract_id TEXT,
                user_name TEXT,
                details TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                content TEXT NOT NULL,
                clause_count INTEGER,
                upload_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_findings_contract ON findings(contract_id);
            CREATE INDEX IF NOT EXISTS idx_reviews_contract ON reviews(contract_id);
            CREATE INDEX IF NOT EXISTS idx_audit_contract ON audit_log(contract_id);
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
        """)


# --- Contract CRUD ---

def create_contract(
    filename: str,
    original_filename: str,
    language: str = "en",
    file_size: int = 0,
    text_content: str = "",
) -> str:
    """Create a new contract record. Returns contract ID."""
    contract_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO contracts (id, filename, original_filename, upload_date, status, language, file_size, text_content)
               VALUES (?, ?, ?, ?, 'uploaded', ?, ?, ?)""",
            (contract_id, filename, original_filename, now, language, file_size, text_content),
        )
    log_audit("CONTRACT_UPLOADED", contract_id, details=f"File: {original_filename}")
    return contract_id


def get_contract(contract_id: str) -> Optional[dict]:
    """Get a contract by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
        return dict(row) if row else None


def list_contracts(status: Optional[str] = None, limit: int = 100, offset: int = 0) -> list[dict]:
    """List contracts with optional status filter."""
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM contracts WHERE status = ? ORDER BY upload_date DESC LIMIT ? OFFSET ?",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contracts ORDER BY upload_date DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]


def update_contract_analysis(
    contract_id: str,
    overall_risk: str,
    overall_score: float,
    report_json: str,
):
    """Update contract with analysis results."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """UPDATE contracts SET status = 'analyzed', overall_risk = ?, overall_score = ?,
               analysis_date = ?, report_json = ? WHERE id = ?""",
            (overall_risk, overall_score, now, report_json, contract_id),
        )
    log_audit("ANALYSIS_COMPLETED", contract_id, details=f"Risk: {overall_risk}, Score: {overall_score}")


def update_contract_status(contract_id: str, status: str):
    """Update contract status."""
    with get_connection() as conn:
        conn.execute("UPDATE contracts SET status = ? WHERE id = ?", (status, contract_id))


# --- Findings CRUD ---

def save_findings(contract_id: str, findings: list[dict]):
    """Save analysis findings for a contract."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        for f in findings:
            row_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO findings (id, contract_id, finding_id, detecting_layer, clause_type,
                   severity, confidence, clause_text, explanation, suggested_fix,
                   cross_validated, agreeing_layers, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row_id, contract_id, f.get("id", ""),
                    f.get("detecting_layer", ""), f.get("clause_type", ""),
                    f.get("severity", ""), f.get("confidence", 0),
                    f.get("clause_text", ""), f.get("explanation", ""),
                    f.get("suggested_fix", ""),
                    1 if f.get("cross_validated") else 0,
                    json.dumps(f.get("agreeing_layers", [])),
                    now,
                ),
            )


def get_findings(contract_id: str) -> list[dict]:
    """Get all findings for a contract."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM findings WHERE contract_id = ? ORDER BY severity, created_at",
            (contract_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["agreeing_layers"] = json.loads(d.get("agreeing_layers", "[]"))
            d["cross_validated"] = bool(d.get("cross_validated"))
            results.append(d)
        return results


# --- Reviews CRUD ---

def create_review(
    contract_id: str,
    reviewer_name: str,
    decision: str,
    comments: str = "",
) -> str:
    """Create a review record. Returns review ID."""
    review_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO reviews (id, contract_id, reviewer_name, decision, comments, review_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (review_id, contract_id, reviewer_name, decision, comments, now),
        )
        new_status = "approved" if decision == "approve" else "rejected" if decision == "reject" else "under_review"
        conn.execute("UPDATE contracts SET status = ? WHERE id = ?", (new_status, contract_id))

    log_audit(
        f"REVIEW_{decision.upper()}",
        contract_id,
        user_name=reviewer_name,
        details=comments,
    )
    return review_id


def get_reviews(contract_id: str) -> list[dict]:
    """Get all reviews for a contract."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE contract_id = ? ORDER BY review_date DESC",
            (contract_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_pending_reviews() -> list[dict]:
    """Get all contracts pending review."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM contracts WHERE status = 'analyzed' ORDER BY analysis_date DESC",
        ).fetchall()
        return [dict(r) for r in rows]


# --- Audit Log ---

def log_audit(
    action: str,
    contract_id: Optional[str] = None,
    user_name: Optional[str] = None,
    details: Optional[str] = None,
):
    """Log an audit event."""
    audit_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO audit_log (id, action, contract_id, user_name, details, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (audit_id, action, contract_id, user_name, details, now),
        )


def get_audit_log(
    contract_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Get audit log entries."""
    with get_connection() as conn:
        if contract_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE contract_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (contract_id, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]


# --- Templates CRUD ---

def create_template(name: str, content: str, description: str = "") -> str:
    """Create a new template. Returns template ID."""
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    clause_count = len([p for p in content.split("\n\n") if len(p.strip()) > 30])
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO templates (id, name, description, content, clause_count, upload_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (template_id, name, description, content, clause_count, now),
        )
    log_audit("TEMPLATE_CREATED", details=f"Template: {name}")
    return template_id


def get_template(template_id: str) -> Optional[dict]:
    """Get a template by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
        return dict(row) if row else None


def list_templates() -> list[dict]:
    """List all active templates."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM templates WHERE is_active = 1 ORDER BY upload_date DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_template(template_id: str):
    """Soft-delete a template."""
    with get_connection() as conn:
        conn.execute("UPDATE templates SET is_active = 0 WHERE id = ?", (template_id,))
    log_audit("TEMPLATE_DELETED", details=f"Template ID: {template_id}")


# --- Statistics ---

def get_statistics() -> dict:
    """Get dashboard statistics."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
        analyzed = conn.execute("SELECT COUNT(*) FROM contracts WHERE status = 'analyzed'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM contracts WHERE status = 'approved'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM contracts WHERE status = 'rejected'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM contracts WHERE status = 'analyzed'").fetchone()[0]

        risk_dist = {}
        for row in conn.execute(
            "SELECT overall_risk, COUNT(*) as cnt FROM contracts WHERE overall_risk IS NOT NULL GROUP BY overall_risk"
        ).fetchall():
            risk_dist[row["overall_risk"]] = row["cnt"]

        total_findings = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        total_reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]

        return {
            "total_contracts": total,
            "analyzed": analyzed,
            "approved": approved,
            "rejected": rejected,
            "pending_review": pending,
            "risk_distribution": risk_dist,
            "total_findings": total_findings,
            "total_reviews": total_reviews,
        }
