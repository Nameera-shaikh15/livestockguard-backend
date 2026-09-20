from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base


class AnalysisModel(Base):
    __tablename__ = "analyses"

    analysis_id = Column(String, primary_key=True, index=True)
    animal_id = Column(String, ForeignKey("animals.animal_id"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)  # NORMAL, ATTENTION, HIGH_RISK
    modalities_analyzed = Column(JSON, nullable=False)  # e.g. ["image", "environment"]
    indicators = Column(JSON, nullable=False)  # List of dicts
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    animal = relationship("AnimalModel", back_populates="analyses")
    alert = relationship("AlertModel", back_populates="analysis", uselist=False)
