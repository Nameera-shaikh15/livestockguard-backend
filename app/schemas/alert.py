from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    alert_id: str
    animal_id: str
    analysis_id: str
    risk_level: str
    risk_score: int
    indicators: List[Dict[str, Any]]
    explanation: str
    status: str  # ACTIVE, RESOLVED
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResolveResponse(BaseModel):
    message: str
    alert: AlertResponse
