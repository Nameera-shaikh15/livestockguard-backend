from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import crud
from app.schemas.alert import AlertResponse, AlertResolveResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse])
def get_all_alerts(db: Session = Depends(get_db)):
    """Retrieve all alerts (active and resolved)."""
    return crud.get_alerts(db)


@router.get("/active", response_model=List[AlertResponse])
def get_active_alerts(db: Session = Depends(get_db)):
    """Retrieve only ACTIVE alerts."""
    return crud.get_alerts(db, status="ACTIVE")


@router.get("/resolved", response_model=List[AlertResponse])
def get_resolved_alerts(db: Session = Depends(get_db)):
    """Retrieve only RESOLVED alerts."""
    return crud.get_alerts(db, status="RESOLVED")


@router.post("/{alert_id}/resolve", response_model=AlertResolveResponse)
def resolve_alert_endpoint(alert_id: str, db: Session = Depends(get_db)):
    """
    Resolve an active alert.
    - Sets alert status to RESOLVED.
    - Records resolved_at timestamp.
    - Preserves original analysis record.
    - Updates animal's current status to NORMAL.
    """
    db_alert = crud.get_alert(db, alert_id)
    if not db_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found."
        )

    resolved_alert = crud.resolve_alert(db, alert_id)
    return AlertResolveResponse(
        message=f"Alert '{alert_id}' has been successfully resolved. Animal '{db_alert.animal_id}' status updated to NORMAL.",
        alert=resolved_alert
    )
