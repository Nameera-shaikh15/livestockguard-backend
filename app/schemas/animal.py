from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AnimalCreate(BaseModel):
    animal_id: str
    species: str
    age: Optional[float] = None
    farm_id: Optional[str] = None


class AnimalResponse(BaseModel):
    animal_id: str
    species: str
    age: Optional[float] = None
    farm_id: Optional[str] = None
    current_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
