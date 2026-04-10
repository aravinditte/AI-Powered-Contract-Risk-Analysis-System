# Database Migrations

This project uses **Alembic** for schema migrations.

## Rules (Enterprise Compliance)

- NEVER auto-create tables in production
- ALL schema changes must be migration-controlled
- Migration scripts must be reviewed before deployment

## Commands

Initialize:
alembic init migrations


Create migration:


alembic revision --autogenerate -m "add contracts table"


Apply migrations:


alembic upgrade head