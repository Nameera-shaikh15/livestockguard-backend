import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database import crud
from app.schemas.animal import AnimalCreate
from app.schemas.analysis import AnalysisResponse, IndicatorSchema
from app.services.explanation_service import explanation_service

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


DEMO_DATA: Dict[str, Dict[str, Any]] = {
    "Cow-17": {
        "species": "cattle",
        "age": 4.5,
        "farm_id": "GreenValley-Farm",
        "risk_score": 78,
        "risk_level": "HIGH_RISK",
        "modalities_analyzed": ["image", "video", "audio", "environment"],
        "indicators": [
            {
                "modality": "video",
                "name": "reduced_activity",
                "confidence": 0.85,
                "description": "Significantly reduced movement detected across 12 analyzed video frames."
            },
            {
                "modality": "image",
                "name": "unusual_posture_signal",
                "confidence": 0.82,
                "description": "Visual analysis detected abnormal standing posture and stance alignment."
            },
            {
                "modality": "audio",
                "name": "unusual_vocalization_pattern",
                "confidence": 0.74,
                "description": "Elevated RMS vocal energy and high frequency pitch centroid anomaly."
            },
            {
                "modality": "environment",
                "name": "potential_heat_stress_environment",
                "confidence": 0.90,
                "description": "Temperature of 34°C with 72% humidity indicates heat stress risk conditions."
            }
        ],
        "explanation": "Cow-17 was flagged because reduced activity, unusual posture signal, unusual vocalization pattern, and environmental risk were observed during analysis.",
        "alert_created": True,
        "initial_alert_status": "ACTIVE"
    },
    "Goat-08": {
        "species": "goat",
        "age": 2.0,
        "farm_id": "Highland-Pastures",
        "risk_score": 48,
        "risk_level": "ATTENTION",
        "modalities_analyzed": ["video", "image"],
        "indicators": [
            {
                "modality": "video",
                "name": "reduced_activity",
                "confidence": 0.68,
                "description": "Moderate reduction in movement activity recorded during video observation."
            },
            {
                "modality": "image",
                "name": "inactivity_visual_indicator",
                "confidence": 0.62,
                "description": "Static posture observed without routine herd movement."
            }
        ],
        "explanation": "Goat-08 was flagged with ATTENTION status due to reduced movement activity and high posture stillness.",
        "alert_created": True,
        "initial_alert_status": "ACTIVE"
    },
    "Cow-03": {
        "species": "cattle",
        "age": 3.0,
        "farm_id": "GreenValley-Farm",
        "risk_score": 12,
        "risk_level": "NORMAL",
        "modalities_analyzed": ["image", "environment"],
        "indicators": [
            {
                "modality": "image",
                "name": "normal_visual_appearance",
                "confidence": 0.92,
                "description": "Standard standing posture and healthy physical appearance."
            },
            {
                "modality": "environment",
                "name": "normal_environmental_conditions",
                "confidence": 0.90,
                "description": "Comfortable ambient temperature (22°C) and humidity (55%)."
            }
        ],
        "explanation": "Cow-03 showed normal observable physical activity, acoustic patterns, and environmental risk levels.",
        "alert_created": False,
        "initial_alert_status": "NONE"
    },
    "Buffalo-02": {
        "species": "buffalo",
        "age": 5.0,
        "farm_id": "RiverDelta-Ranch",
        "risk_score": 68,
        "risk_level": "HIGH_RISK",
        "modalities_analyzed": ["video", "audio"],
        "indicators": [
            {
                "modality": "video",
                "name": "unusual_erratic_movement",
                "confidence": 0.79,
                "description": "Erratic movement variations detected in temporal video frame diffs."
            },
            {
                "modality": "audio",
                "name": "unusual_vocalization_pattern",
                "confidence": 0.71,
                "description": "High vocalization pitch frequency detected."
            }
        ],
        "explanation": "Buffalo-02 was previously flagged due to erratic movement and vocalization variance. Alert has been RESOLVED.",
        "alert_created": True,
        "initial_alert_status": "RESOLVED"
    }
}


@router.get("/analysis/{animal_id}", response_model=AnalysisResponse)
def get_demo_analysis(animal_id: str, db: Session = Depends(get_db)):
    """
    Demo endpoint returning full standardized AnalysisResponse schema.
    Pre-populated realistic demo analysis for Cow-17, Goat-08, Cow-03, and Buffalo-02.
    Seeds the SQLite database so dashboard summary and alerts reflect realistic states.
    """
    demo = DEMO_DATA.get(animal_id)
    if not demo:
        # Fallback to Cow-17 schema if unknown ID passed
        demo = DEMO_DATA["Cow-17"]
        demo_animal_id = animal_id
    else:
        demo_animal_id = animal_id

    # Seed animal profile into DB
    crud.create_animal(
        db,
        AnimalCreate(
            animal_id=demo_animal_id,
            species=demo["species"],
            age=demo["age"],
            farm_id=demo["farm_id"]
        )
    )

    created_at = datetime.utcnow() - timedelta(minutes=15)
    analysis_id = f"anls_demo_{demo_animal_id.lower().replace('-', '_')}"

    # Check if analysis already exists in DB
    existing_analyses = crud.get_animal_analyses(db, demo_animal_id)
    if not existing_analyses:
        crud.create_analysis(
            db,
            {
                "analysis_id": analysis_id,
                "animal_id": demo_animal_id,
                "risk_score": demo["risk_score"],
                "risk_level": demo["risk_level"],
                "modalities_analyzed": demo["modalities_analyzed"],
                "indicators": demo["indicators"],
                "explanation": demo["explanation"],
                "recommendation": explanation_service.EXACT_RECOMMENDATION,
                "created_at": created_at
            }
        )

        # Seed alert if required
        if demo["alert_created"]:
            alert_id = f"alt_demo_{demo_animal_id.lower().replace('-', '_')}"
            db_alert = crud.create_alert(
                db,
                {
                    "alert_id": alert_id,
                    "animal_id": demo_animal_id,
                    "analysis_id": analysis_id,
                    "risk_level": demo["risk_level"],
                    "risk_score": demo["risk_score"],
                    "indicators": demo["indicators"],
                    "explanation": demo["explanation"],
                    "created_at": created_at
                }
            )

            # Handle RESOLVED demo status
            if demo["initial_alert_status"] == "RESOLVED":
                crud.resolve_alert(db, alert_id)

    # Fetch updated DB state
    db_animal = crud.get_animal(db, demo_animal_id)
    db_analyses = crud.get_animal_analyses(db, demo_animal_id)
    latest_anls = db_analyses[0] if db_analyses else None

    db_alerts = crud.get_alerts(db)
    active_or_demo_alert = next((a for a in db_alerts if a.animal_id == demo_animal_id), None)
    
    alert_dict = None
    if active_or_demo_alert:
        alert_dict = {
            "alert_id": active_or_demo_alert.alert_id,
            "animal_id": active_or_demo_alert.animal_id,
            "analysis_id": active_or_demo_alert.analysis_id,
            "risk_level": active_or_demo_alert.risk_level,
            "risk_score": active_or_demo_alert.risk_score,
            "status": active_or_demo_alert.status,
            "created_at": active_or_demo_alert.created_at.isoformat()
        }

    structured_indicators = [IndicatorSchema(**ind) for ind in demo["indicators"]]

    return AnalysisResponse(
        analysis_id=latest_anls.analysis_id if latest_anls else analysis_id,
        animal={
            "animal_id": demo_animal_id,
            "species": demo["species"],
            "age": demo["age"],
            "farm_id": demo["farm_id"]
        },
        risk={
            "score": demo["risk_score"],
            "level": demo["risk_level"]
        },
        modalities_analyzed=demo["modalities_analyzed"],
        indicators=structured_indicators,
        explanation=demo["explanation"],
        recommendation=explanation_service.EXACT_RECOMMENDATION,
        alert_created=demo["alert_created"],
        alert=alert_dict,
        created_at=created_at
    )
