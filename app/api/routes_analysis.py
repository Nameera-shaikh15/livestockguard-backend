import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database.database import get_db
from app.database import crud
from app.schemas.animal import AnimalCreate
from app.schemas.analysis import (
    AnalysisResponse,
    SingleModalityImageResponse,
    SingleModalityVideoResponse,
    SingleModalityAudioResponse,
    EnvironmentalAnalysisResponse,
    IndicatorSchema
)
from app.services.vision_service import vision_service
from app.services.video_service import video_service
from app.services.audio_service import audio_service
from app.services.environment_service import environment_service
from app.services.risk_engine import risk_engine
from app.services.explanation_service import explanation_service

router = APIRouter(tags=["Analysis"])


# Single Modality Image
@router.post("/analyze/image", response_model=SingleModalityImageResponse)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    animal_id: str = Form(...),
    species: str = Form(...),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None)
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="Image file must be provided.")
    
    contents = await image.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    indicators_raw = await vision_service.analyze_image(
        image_bytes=contents,
        animal_id=animal_id,
        species=species,
        temperature=temperature,
        humidity=humidity
    )

    indicators = [IndicatorSchema(**ind) for ind in indicators_raw]
    return SingleModalityImageResponse(
        animal_id=animal_id,
        modality="image",
        indicators=indicators
    )


# Single Modality Video
@router.post("/analyze/video", response_model=SingleModalityVideoResponse)
async def analyze_video_endpoint(
    video: UploadFile = File(...),
    animal_id: str = Form(...),
    species: str = Form(...)
):
    if not video.filename:
        raise HTTPException(status_code=400, detail="Video file must be provided.")

    contents = await video.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Video size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    result = video_service.analyze_video(
        video_bytes=contents,
        animal_id=animal_id,
        species=species
    )

    behaviour_indicators = [IndicatorSchema(**ind) for ind in result["behaviour_indicators"]]
    return SingleModalityVideoResponse(
        animal_id=animal_id,
        modality="video",
        frames_analyzed=result["frames_analyzed"],
        behaviour_indicators=behaviour_indicators
    )


# Single Modality Audio
@router.post("/analyze/audio", response_model=SingleModalityAudioResponse)
async def analyze_audio_endpoint(
    audio: UploadFile = File(...),
    animal_id: str = Form(...),
    species: str = Form(...)
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file must be provided.")

    contents = await audio.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    result = audio_service.analyze_audio(
        audio_bytes=contents,
        animal_id=animal_id,
        species=species
    )

    indicators = [IndicatorSchema(**ind) for ind in result["indicators"]]
    return SingleModalityAudioResponse(
        animal_id=animal_id,
        modality="audio",
        anomaly_score=result["anomaly_score"],
        indicator=result["indicator"],
        extracted_features=result["extracted_features"],
        indicators=indicators
    )


# Farm Condition / Environment Analysis
@router.post("/analyze/environment", response_model=EnvironmentalAnalysisResponse)
async def analyze_environment_endpoint(
    temperature: float = Form(...),
    humidity: float = Form(...)
):
    if temperature < -30.0 or temperature > 60.0:
        raise HTTPException(status_code=400, detail="Invalid temperature value. Must be between -30°C and 60°C.")
    if humidity < 0.0 or humidity > 100.0:
        raise HTTPException(status_code=400, detail="Invalid humidity percentage. Must be between 0% and 100%.")

    result = environment_service.analyze_environment(temperature=temperature, humidity=humidity)
    structured_indicators = [IndicatorSchema(**ind) for ind in result["structured_indicators"]]
    
    return EnvironmentalAnalysisResponse(
        temperature=result["temperature"],
        humidity=result["humidity"],
        risk_score=result["risk_score"],
        indicators=result["indicators"],
        structured_indicators=structured_indicators,
        explanation=result["explanation"]
    )


# Complete Multimodal Analysis Pipeline Endpoint
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_multimodal_endpoint(
    animal_id: str = Form(...),
    species: str = Form(...),
    age: Optional[float] = Form(None),
    farm_id: Optional[str] = Form(None),
    activity_level: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    temperature: Optional[float] = Form(None),
    humidity: Optional[float] = Form(None),
    db: Session = Depends(get_db)
):
    # Step 1: Register or get animal profile
    animal_schema = AnimalCreate(
        animal_id=animal_id,
        species=species,
        age=age,
        farm_id=farm_id
    )
    crud.create_animal(db, animal_schema)

    # Step 2: Extract indicators across available modalities
    all_indicators: List[Dict[str, Any]] = []
    modality_results_map: Dict[str, Any] = {}
    
    visual_score: Optional[float] = None
    behaviour_score: Optional[float] = None
    audio_score: Optional[float] = None
    env_score: Optional[float] = None

    # Image processing
    if image and image.filename:
        img_bytes = await image.read()
        if len(img_bytes) > 0:
            vision_inds = await vision_service.analyze_image(
                image_bytes=img_bytes,
                animal_id=animal_id,
                species=species,
                temperature=temperature,
                humidity=humidity
            )
            all_indicators.extend(vision_inds)
            concerning_v = [ind for ind in vision_inds if not ind["name"].startswith("normal_")]
            if concerning_v:
                visual_score = float(max(ind["confidence"] for ind in concerning_v) * 100.0)
            else:
                visual_score = 15.0
            modality_results_map["visual"] = {
                "indicators": vision_inds,
                "score": visual_score
            }

    # Video & Activity processing
    if (video and video.filename) or activity_level is not None:
        beh_inds = []
        frames_cnt = 0
        if video and video.filename:
            vid_bytes = await video.read()
            if len(vid_bytes) > 0:
                video_res = video_service.analyze_video(
                    video_bytes=vid_bytes,
                    animal_id=animal_id,
                    species=species
                )
                beh_inds = video_res.get("behaviour_indicators", [])
                frames_cnt = video_res.get("frames_analyzed", 0)

        if activity_level and not beh_inds:
            act_lower = str(activity_level).lower()
            if act_lower in ["low", "reduced", "sluggish", "inactive"]:
                beh_inds.append({
                    "modality": "behaviour",
                    "name": "reduced_activity",
                    "confidence": 0.80,
                    "description": f"Activity level reported as '{activity_level}' indicating reduced physical movement."
                })
            elif act_lower in ["normal", "active"]:
                beh_inds.append({
                    "modality": "behaviour",
                    "name": "normal_activity_level",
                    "confidence": 0.90,
                    "description": f"Activity level reported as '{activity_level}' within normal range."
                })

        if beh_inds:
            all_indicators.extend(beh_inds)
            concerning_b = [ind for ind in beh_inds if not ind["name"].startswith("normal_")]
            if concerning_b:
                behaviour_score = float(max(ind["confidence"] for ind in concerning_b) * 100.0)
            else:
                behaviour_score = 10.0
            modality_results_map["video"] = {
                "frames_analyzed": frames_cnt,
                "activity_level_input": activity_level,
                "indicators": beh_inds,
                "score": behaviour_score
            }

    # Audio processing
    if audio and audio.filename:
        aud_bytes = await audio.read()
        if len(aud_bytes) > 0:
            audio_res = audio_service.analyze_audio(
                audio_bytes=aud_bytes,
                animal_id=animal_id,
                species=species
            )
            aud_inds = audio_res.get("indicators", [])
            all_indicators.extend(aud_inds)
            audio_score = float(audio_res["anomaly_score"] * 100.0)
            modality_results_map["audio"] = {
                "anomaly_score": audio_res["anomaly_score"],
                "extracted_features": audio_res.get("extracted_features", {}),
                "indicators": aud_inds
            }

    # Environment processing
    if temperature is not None and humidity is not None:
        if temperature < -30.0 or temperature > 60.0 or humidity < 0.0 or humidity > 100.0:
            raise HTTPException(status_code=400, detail="Invalid temperature or humidity parameters.")
        env_res = environment_service.analyze_environment(temperature=temperature, humidity=humidity)
        env_inds = env_res.get("structured_indicators", [])
        all_indicators.extend(env_inds)
        env_score = float(env_res["risk_score"])
        modality_results_map["farm_conditions"] = {
            "temperature": temperature,
            "humidity": humidity,
            "thi": env_res.get("thi"),
            "risk_score": env_res["risk_score"],
            "indicators": env_inds
        }

    # Verify at least one modality was provided
    if visual_score is None and behaviour_score is None and audio_score is None and env_score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one modality (image, video, audio, activity_level, or temperature+humidity) must be provided for analysis."
        )

    # Step 3: Run Multimodal Risk Engine
    risk_output = risk_engine.calculate_risk(
        visual_score=visual_score,
        behaviour_score=behaviour_score,
        audio_score=audio_score,
        environment_score=env_score
    )

    # Step 4: Generate Explanation & Recommendation
    explanation = explanation_service.generate_explanation(
        animal_id=animal_id,
        risk_level=risk_output["risk_level"],
        indicators=all_indicators
    )
    recommendation = explanation_service.generate_recommendation(risk_output["risk_level"])

    # Step 5: Save Analysis to SQLite DB
    analysis_id = f"anls_{uuid.uuid4().hex[:8]}"
    created_at = datetime.utcnow()

    analysis_dict = {
        "analysis_id": analysis_id,
        "animal_id": animal_id,
        "risk_score": risk_output["risk_score"],
        "risk_level": risk_output["risk_level"],
        "modalities_analyzed": risk_output["modalities_analyzed"],
        "indicators": all_indicators,
        "explanation": explanation,
        "recommendation": recommendation,
        "created_at": created_at
    }
    crud.create_analysis(db, analysis_dict)

    # Step 6: Create Alert if risk is ATTENTION or HIGH_RISK
    alert_created = False
    alert_dict = None

    if risk_output["risk_level"] in ["ATTENTION", "HIGH_RISK"]:
        alert_id = f"alt_{uuid.uuid4().hex[:8]}"
        alert_data = {
            "alert_id": alert_id,
            "animal_id": animal_id,
            "analysis_id": analysis_id,
            "risk_level": risk_output["risk_level"],
            "risk_score": risk_output["risk_score"],
            "indicators": all_indicators,
            "explanation": explanation,
            "created_at": created_at
        }
        db_alert = crud.create_alert(db, alert_data)
        alert_created = True
        alert_dict = {
            "alert_id": db_alert.alert_id,
            "animal_id": db_alert.animal_id,
            "analysis_id": db_alert.analysis_id,
            "risk_level": db_alert.risk_level,
            "risk_score": db_alert.risk_score,
            "status": db_alert.status,
            "created_at": db_alert.created_at.isoformat()
        }

    # Step 7: Build response matching standardized schema
    structured_indicators = [IndicatorSchema(**ind) for ind in all_indicators]
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        animal={
            "animal_id": animal_id,
            "species": species,
            "age": age,
            "farm_id": farm_id
        },
        risk={
            "score": risk_output["risk_score"],
            "level": risk_output["risk_level"]
        },
        modalities_analyzed=risk_output["modalities_analyzed"],
        indicators=structured_indicators,
        modality_results=modality_results_map if modality_results_map else None,
        explanation=explanation,
        recommendation=recommendation,
        alert_created=alert_created,
        alert=alert_dict,
        created_at=created_at
    )

