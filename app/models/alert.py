from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database.database import Base


class AlertModel(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, index=True)
    animal_id = Column(String, ForeignKey("animals.animal_id"), nullable=False, index=True)
    analysis_id = Column(String, ForeignKey("analyses.analysis_id"), nullable=False, index=True)
    risk_level = Column(String, nullable=False)  # ATTENTION, HIGH_RISK
    risk_score = Column(Integer, nullable=False)
    indicators = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False, index=True)  # ACTIVE, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    animal = relationship("AnimalModel", back_populates="alerts")
    analysis = relationship("AnalysisModel", back_populates="alert")
