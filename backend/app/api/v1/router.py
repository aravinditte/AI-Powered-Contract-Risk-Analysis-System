from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    contracts,
    risks,
    reviews,
    reports,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["Contracts"])
api_router.include_router(risks.router, prefix="/risks", tags=["Risks"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
