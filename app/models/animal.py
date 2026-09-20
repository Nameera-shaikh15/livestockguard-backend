from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.database import Base


class AnimalModel(Base):
    __tablename__ = "animals"

    animal_id = Column(String, primary_key=True, index=True)
    species = Column(String, nullable=False, index=True)
    age = Column(Float, nullable=True)
    farm_id = Column(String, nullable=True, index=True)
    current_status = Column(String, default="NORMAL", nullable=False)  # NORMAL, ATTENTION, HIGH_RISK
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analyses = relationship("AnalysisModel", back_populates="animal", cascade="all, delete-orphan")
    alerts = relationship("AlertModel", back_populates="animal", cascade="all, delete-orphan")
