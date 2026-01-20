# AI-Powered Contract Risk Analysis System

## Overview
This system is an **enterprise internal platform** for analyzing legal contracts using **governed AI**.

The system:
- Identifies risky clauses
- Detects missing mandatory clauses
- Compares against company-approved templates
- Provides explainable AI results
- Enforces mandatory human review

⚠️ **This system never auto-approves contracts.**

---

## Key Principles
- Explainable AI
- Human-in-the-loop
- Audit-ready
- On-premise deployable
- Japanese enterprise compliance mindset

---

## Tech Stack
**Backend**
- Python / FastAPI
- PostgreSQL
- SQLAlchemy
- PyTorch / Transformers

**Frontend**
- React + TypeScript
- TailwindCSS (restricted palette)

**Infrastructure**
- Docker / Docker Compose
- Kubernetes (optional)
- Fully offline capable

---

## Getting Started (Local)

```bash
cp .env.example .env
make build
make up

