from typing import Dict, Any, List, Optional
from app.config import settings


class RiskEngine:
    """
    Multimodal Livestock Health Risk Engine.
    
    Receives available signals from visual, behavioural, audio, and environmental modalities.
    
    IMPORTANT DISCLAIMER:
    The prototype weights (Visual: 25%, Behaviour: 30%, Audio: 20%, Environment: 25%)
    are configurable parameters for early-warning risk scoring. They are NOT clinically or
    scientifically validated medical parameters.
    
    DYNAMIC MISSING MODALITY HANDLING:
    If a modality is omitted from the input, it is completely excluded from score calculations.
    Missing modalities are NEVER assigned artificial or zero scores. Remaining available
    modality weights are re-normalized proportionally to sum to 100%.
    """

    def calculate_risk(
        self,
        visual_score: Optional[float] = None,
        behaviour_score: Optional[float] = None,
        audio_score: Optional[float] = None,
        environment_score: Optional[float] = None
    ) -> Dict[str, Any]:
        
        base_weights = {
            "image": settings.WEIGHT_VISUAL,
            "video": settings.WEIGHT_BEHAVIOUR,  # video/behaviour modality
            "audio": settings.WEIGHT_AUDIO,
            "environment": settings.WEIGHT_ENVIRONMENT
        }

        available_scores = {}
        if visual_score is not None:
            available_scores["image"] = min(100.0, max(0.0, float(visual_score)))
        if behaviour_score is not None:
            available_scores["video"] = min(100.0, max(0.0, float(behaviour_score)))
        if audio_score is not None:
            available_scores["audio"] = min(100.0, max(0.0, float(audio_score)))
        if environment_score is not None:
            available_scores["environment"] = min(100.0, max(0.0, float(environment_score)))

        if not available_scores:
            # Fallback if no modalities provided at all
            return {
                "risk_score": 0,
                "risk_level": "NORMAL",
                "modalities_analyzed": []
            }

        # Calculate sum of weights for available modalities only
        total_weight = sum(base_weights[mod] for mod in available_scores.keys())
        
        if total_weight <= 0:
            total_weight = 1.0

        # Calculate weighted average with re-normalized weights
        composite_score = 0.0
        for mod, score in available_scores.items():
            normalized_weight = base_weights[mod] / total_weight
            composite_score += score * normalized_weight

        final_risk_score = int(round(composite_score))
        final_risk_score = min(100, max(0, final_risk_score))

        # Risk level categorization
        if final_risk_score >= 65:
            risk_level = "HIGH_RISK"
        elif final_risk_score >= 35:
            risk_level = "ATTENTION"
        else:
            risk_level = "NORMAL"

        return {
            "risk_score": final_risk_score,
            "risk_level": risk_level,
            "modalities_analyzed": list(available_scores.keys())
        }


risk_engine = RiskEngine()
