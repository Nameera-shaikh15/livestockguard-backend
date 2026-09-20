from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models.animal import AnimalModel
from app.models.analysis import AnalysisModel
from app.models.alert import AlertModel
from app.schemas.animal import AnimalCreate


# Animal CRUD
def get_animal(db: Session, animal_id: str) -> Optional[AnimalModel]:
    return db.query(AnimalModel).filter(AnimalModel.animal_id == animal_id).first()


def get_animals(db: Session, skip: int = 0, limit: int = 100) -> List[AnimalModel]:
    return db.query(AnimalModel).offset(skip).limit(limit).all()


def create_animal(db: Session, animal: AnimalCreate) -> AnimalModel:
    db_animal = get_animal(db, animal.animal_id)
    if db_animal:
        # Update fields if already exists
        if animal.species:
            db_animal.species = animal.species
        if animal.age is not None:
            db_animal.age = animal.age
        if animal.farm_id is not None:
            db_animal.farm_id = animal.farm_id
        db.commit()
        db.refresh(db_animal)
        return db_animal

    db_animal = AnimalModel(
        animal_id=animal.animal_id,
        species=animal.species,
        age=animal.age,
        farm_id=animal.farm_id,
        current_status="NORMAL"
    )
    db.add(db_animal)
    db.commit()
    db.refresh(db_animal)
    return db_animal


def update_animal_status(db: Session, animal_id: str, status: str) -> Optional[AnimalModel]:
    db_animal = get_animal(db, animal_id)
    if db_animal:
        db_animal.current_status = status
        db.commit()
        db.refresh(db_animal)
    return db_animal


# Analysis CRUD
def create_analysis(db: Session, analysis_data: Dict[str, Any]) -> AnalysisModel:
    db_analysis = AnalysisModel(
        analysis_id=analysis_data["analysis_id"],
        animal_id=analysis_data["animal_id"],
        risk_score=analysis_data["risk_score"],
        risk_level=analysis_data["risk_level"],
        modalities_analyzed=analysis_data["modalities_analyzed"],
        indicators=analysis_data["indicators"],
        explanation=analysis_data["explanation"],
        recommendation=analysis_data["recommendation"],
        created_at=analysis_data.get("created_at", datetime.utcnow())
    )
    db.add(db_analysis)
    
    # Update animal current_status if higher risk
    update_animal_status(db, analysis_data["animal_id"], analysis_data["risk_level"])

    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_animal_analyses(db: Session, animal_id: str) -> List[AnalysisModel]:
    return db.query(AnalysisModel)\
             .filter(AnalysisModel.animal_id == animal_id)\
             .order_by(desc(AnalysisModel.created_at))\
             .all()


# Alert CRUD
def create_alert(db: Session, alert_data: Dict[str, Any]) -> AlertModel:
    db_alert = AlertModel(
        alert_id=alert_data["alert_id"],
        animal_id=alert_data["animal_id"],
        analysis_id=alert_data["analysis_id"],
        risk_level=alert_data["risk_level"],
        risk_score=alert_data["risk_score"],
        indicators=alert_data["indicators"],
        explanation=alert_data["explanation"],
        status="ACTIVE",
        created_at=alert_data.get("created_at", datetime.utcnow())
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alerts(db: Session, status: Optional[str] = None) -> List[AlertModel]:
    query = db.query(AlertModel)
    if status:
        query = query.filter(AlertModel.status == status)
    return query.order_by(desc(AlertModel.created_at)).all()


def get_alert(db: Session, alert_id: str) -> Optional[AlertModel]:
    return db.query(AlertModel).filter(AlertModel.alert_id == alert_id).first()


def resolve_alert(db: Session, alert_id: str) -> Optional[AlertModel]:
    db_alert = get_alert(db, alert_id)
    if not db_alert:
        return None

    if db_alert.status == "ACTIVE":
        db_alert.status = "RESOLVED"
        db_alert.resolved_at = datetime.utcnow()
        db.flush()  # Flush pending status change to DB session before counting remaining active alerts
        
        # Check if animal has any remaining ACTIVE alerts
        active_alerts_left = db.query(AlertModel)\
            .filter(AlertModel.animal_id == db_alert.animal_id, AlertModel.status == "ACTIVE")\
            .count()
        
        if active_alerts_left == 0:
            update_animal_status(db, db_alert.animal_id, "NORMAL")
            
        db.commit()
        db.refresh(db_alert)
    return db_alert



# Dashboard Summary
def get_dashboard_summary(db: Session) -> Dict[str, Any]:
    total_animals = db.query(AnimalModel).count()
    normal_count = db.query(AnimalModel).filter(AnimalModel.current_status == "NORMAL").count()
    attention_count = db.query(AnimalModel).filter(AnimalModel.current_status == "ATTENTION").count()
    high_risk_count = db.query(AnimalModel).filter(AnimalModel.current_status == "HIGH_RISK").count()
    
    resolved_alerts_count = db.query(AlertModel).filter(AlertModel.status == "RESOLVED").count()
    
    recent_alerts_models = db.query(AlertModel)\
                             .order_by(desc(AlertModel.created_at))\
                             .limit(5)\
                             .all()
    
    recent_alerts = []
    for a in recent_alerts_models:
        recent_alerts.append({
            "alert_id": a.alert_id,
            "animal_id": a.animal_id,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "status": a.status,
            "explanation": a.explanation,
            "created_at": a.created_at.isoformat() if a.created_at else None
        })

    return {
        "total_animals": total_animals,
        "normal": normal_count,
        "attention": attention_count,
        "high_risk": high_risk_count,
        "resolved_alerts": resolved_alerts_count,
        "recent_alerts": recent_alerts
    }
