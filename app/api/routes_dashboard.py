from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database import crud

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary_endpoint(db: Session = Depends(get_db)):
    """
    Get dashboard summary statistics calculated directly from stored database records.
    Returns counts for total_animals, normal, attention, high_risk, resolved_alerts, and recent_alerts.
    """
    return crud.get_dashboard_summary(db)
