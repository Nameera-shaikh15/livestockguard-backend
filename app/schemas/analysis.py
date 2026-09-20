from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class IndicatorSchema(BaseModel):
    modality: str  # image, video, audio, environment, behaviour
    name: str  # e.g., unusual_posture, reduced_activity, unusual_vocalization_pattern, heat_stress_environment
    confidence: float  # 0.0 to 1.0
    description: str


class RiskSummary(BaseModel):
    score: int = Field(ge=0, le=100)
    level: str  # NORMAL, ATTENTION, HIGH_RISK


class AnimalInfo(BaseModel):
    animal_id: str
    species: str
    age: Optional[float] = None
    farm_id: Optional[str] = None


class ModalityResults(BaseModel):
    visual: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    farm_conditions: Optional[Dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    analysis_id: str
    animal: AnimalInfo
    risk: RiskSummary
    modalities_analyzed: List[str]
    indicators: List[IndicatorSchema]
    modality_results: Optional[ModalityResults] = None
    explanation: str
    recommendation: str
    alert_created: bool
    alert: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class SingleModalityImageResponse(BaseModel):
    animal_id: str
    modality: str = "image"
    indicators: List[IndicatorSchema]


class SingleModalityVideoResponse(BaseModel):
    animal_id: str
    modality: str = "video"
    frames_analyzed: int
    behaviour_indicators: List[IndicatorSchema]


class SingleModalityAudioResponse(BaseModel):
    animal_id: str
    modality: str = "audio"
    anomaly_score: float
    indicator: str
    extracted_features: Dict[str, Any]
    indicators: List[IndicatorSchema]


class EnvironmentalAnalysisResponse(BaseModel):
    temperature: float
    humidity: float
    risk_score: int
    indicators: List[str]
    structured_indicators: List[IndicatorSchema]
    explanation: str
