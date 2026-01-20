from fastapi import APIRouter, Depends

from app.core.security import require_roles, Role

router = APIRouter()


@router.get(
    "/export",
    dependencies=[Depends(require_roles([
        Role.COMPLIANCE,
        Role.MANAGER,
        Role.ADMIN,
    ]))],
)
def export_report():
    """
    Exports aggregated risk and review data.
    Format: CSV / PDF (future implementation).
    """

    return {
        "message": "Report generation started",
        "format": "CSV",
    }
