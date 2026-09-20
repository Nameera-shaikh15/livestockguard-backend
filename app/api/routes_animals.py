from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import crud
from app.schemas.animal import AnimalCreate, AnimalResponse
from app.schemas.analysis import AnalysisResponse

router = APIRouter(prefix="/animals", tags=["Animals"])


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
def create_animal(animal: AnimalCreate, db: Session = Depends(get_db)):
    """Create or register an animal profile."""
    if not animal.animal_id or not animal.species:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="animal_id and species are required fields."
        )
    return crud.create_animal(db, animal)


@router.get("", response_model=List[AnimalResponse])
def list_animals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all registered animals."""
    return crud.get_animals(db, skip=skip, limit=limit)


@router.get("/{animal_id}", response_model=AnimalResponse)
def get_animal_detail(animal_id: str, db: Session = Depends(get_db)):
    """Get details for a specific animal."""
    db_animal = crud.get_animal(db, animal_id)
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )
    return db_animal


@router.get("/{animal_id}/history")
def get_animal_history(animal_id: str, db: Session = Depends(get_db)):
    """Return chronological analysis history for a specific animal."""
    db_animal = crud.get_animal(db, animal_id)
    if not db_animal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal with ID '{animal_id}' not found."
        )
    
    analyses = crud.get_animal_analyses(db, animal_id)
    alerts = crud.get_alerts(db)
    animal_alerts = {a.analysis_id: a for a in alerts if a.animal_id == animal_id}

    history = []
    for a in analyses:
        alert_info = animal_alerts.get(a.analysis_id)
        history.append({
            "analysis_id": a.analysis_id,
            "created_at": a.created_at.strftime("%d %b %Y %H:%M") if a.created_at else None,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "modalities_analyzed": a.modalities_analyzed,
            "explanation": a.explanation,
            "alert_status": alert_info.status if alert_info else ("NORMAL" if a.risk_level == "NORMAL" else "NONE"),
            "alert_id": alert_info.alert_id if alert_info else None
        })

    return {
        "animal_id": animal_id,
        "species": db_animal.species,
        "current_status": db_animal.current_status,
        "total_records": len(history),
        "history": history
    }
