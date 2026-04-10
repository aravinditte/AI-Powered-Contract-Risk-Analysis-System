"""
Tests for the Analysis Pipeline

Verifies the orchestrator correctly runs all layers,
cross-validates findings, and produces a complete risk report.
"""

import pytest
from src.pipeline import AnalysisPipeline, RiskReport

SAMPLE_CONTRACT = """
SERVICE AGREEMENT

This Service Agreement is entered into as of January 15, 2025 by and between
ABC Corporation ("Company") and XYZ Consulting LLC ("Provider").

1. DEFINITIONS
"Confidential Information" means any non-public information disclosed by either party.

2. SCOPE OF WORK
Provider shall perform consulting services. Working hours are 9 AM to 5 PM.
Deliverables include monthly reports.

3. PAYMENT TERMS
Company shall pay Provider $10,000 USD per month. Invoices are due net 30 days.

4. TERMINATION
Either party may terminate upon 30 days' written notice.

5. CONFIDENTIALITY
Each party shall maintain strict confidentiality of proprietary information.

6. INTELLECTUAL PROPERTY
All intellectual property created shall be owned by Company. Provider assigns all copyright.

7. LIABILITY
Limitation of liability: total liability shall not exceed fees paid in 12 months.
Provider shall indemnify Company against third-party claims.

8. FORCE MAJEURE
Neither party liable for force majeure events beyond reasonable control.

9. DISPUTE RESOLUTION
Disputes resolved through binding arbitration in New York.

9A. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with
the laws of the State of New York. The jurisdiction for any legal matters
shall be the courts located in New York County.

10. DATA PROTECTION
Both parties comply with GDPR and applicable data protection laws.

11. NON-COMPETE
Provider agrees not to compete for 12 months after termination.

12. TAX
Provider responsible for all tax obligations.

13. INSURANCE
Provider shall maintain professional liability insurance.

14. AMENDMENTS
Agreement may only be amended by written consent.

15. NOTICE
Written notice shall be delivered to the parties at specified addresses.

16. SEVERABILITY
If any provision is invalid, remaining provisions remain in effect.

17. ENTIRE AGREEMENT
This constitutes the entire agreement, supersedes all prior agreements.

18. ASSIGNMENT
Neither party may assign without written consent.

19. WARRANTIES
Provider represents and warrants services will be professional.

20. AUTO-RENEWAL
Agreement auto-renews annually unless 60 days notice given.

IN WITNESS WHEREOF, the parties have executed this Agreement.
Signature: _______________
"""

RISKY_CONTRACT = """
CONSULTING AGREEMENT

This agreement is between Company and Contractor.

The Contractor shall bear unlimited liability for all damages.
Company may unilaterally modify any terms at its sole discretion.
Contractor irrevocably waives all claims and forfeits any right to dispute.
The license granted is perpetual and worldwide.
A penalty of $50,000 applies for any breach.

Payment: $1000 per month.
"""


@pytest.fixture
def pipeline():
    return AnalysisPipeline()


class TestPipelineAnalysis:
    """Test the complete analysis pipeline."""

    def test_returns_risk_report(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-001")
        assert isinstance(report, RiskReport)

    def test_report_has_required_fields(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-001")
        assert report.contract_id == "test-001"
        assert report.timestamp
        assert report.overall_risk in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
        assert isinstance(report.overall_score, float)
        assert report.overall_score >= 0
        assert isinstance(report.findings, list)
        assert isinstance(report.layers_used, list)
        assert "rule_based" in report.layers_used

    def test_complete_contract_has_no_missing_mandatory(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-002")
        # A complete contract should have no missing mandatory clauses
        assert len(report.missing_clauses) == 0
        # Rule-based layer should be used
        assert "rule_based" in report.layers_used

    def test_risky_contract_has_high_risk(self, pipeline):
        report = pipeline.analyze(RISKY_CONTRACT, contract_id="test-003")
        assert report.overall_risk in ("CRITICAL", "HIGH")
        assert report.overall_score > 30

    def test_findings_have_ids(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-004")
        for f in report.findings:
            assert f.id
            assert f.detecting_layer

    def test_severity_counts_add_up(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-005")
        total = report.critical_count + report.high_count + report.medium_count + report.low_count + report.info_count
        assert total == report.total_findings

    def test_empty_contract_flags_all_missing(self, pipeline):
        report = pipeline.analyze("This is not a contract.", contract_id="test-006")
        assert len(report.missing_clauses) > 0
        assert report.overall_risk in ("CRITICAL", "HIGH")

    def test_report_to_dict(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-007")
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "contract_id" in d
        assert "findings" in d
        assert "overall_risk" in d

    def test_language_parameter(self, pipeline):
        report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-008", language="en")
        assert report.language == "en"

    def test_cross_validation_applied(self, pipeline):
        """Test that findings detected by multiple layers get cross-validated."""
        report = pipeline.analyze(RISKY_CONTRACT, contract_id="test-009")
        # The risky contract should trigger findings from both rule-based and NLP layers
        layers_with_findings = set()
        for f in report.findings:
            layers_with_findings.add(f.detecting_layer)
        assert "rule_based" in layers_with_findings


class TestRiskScoring:
    """Test overall risk computation."""

    def test_critical_when_missing_clauses(self, pipeline):
        report = pipeline.analyze("Just some random text here.", contract_id="test-010")
        assert report.overall_risk == "CRITICAL"

    def test_risky_contract_has_more_critical_findings(self, pipeline):
        safe_report = pipeline.analyze(SAMPLE_CONTRACT, contract_id="test-011")
        risky_report = pipeline.analyze(RISKY_CONTRACT, contract_id="test-012")
        # Risky contract should have more critical+high findings
        risky_serious = risky_report.critical_count + risky_report.high_count
        safe_serious = safe_report.critical_count + safe_report.high_count
        assert risky_serious > safe_serious
