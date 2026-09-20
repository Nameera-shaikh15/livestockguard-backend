from typing import List, Dict, Any


class BehaviourService:
    """
    Behaviour Analysis Service.
    Evaluates temporal movement metrics, stillness duration, and activity levels.
    Inputs come from video frame differencing or user behavioral observations.
    
    IMPORTANT: Outputs represent behavioural and activity signals, NOT medical diagnoses.
    """

    def evaluate_activity_metrics(
        self,
        mean_frame_diff: float,
        stillness_ratio: float,
        frames_analyzed: int
    ) -> List[Dict[str, Any]]:
        indicators = []

        # High stillness ratio -> prolonged inactivity
        if stillness_ratio >= 0.70:
            indicators.append({
                "modality": "behaviour",
                "name": "prolonged_inactivity",
                "confidence": round(min(0.95, 0.5 + stillness_ratio / 2.0), 2),
                "description": f"Prolonged inactivity observed across {int(stillness_ratio * 100)}% of the {frames_analyzed} sampled video frames."
            })
        elif stillness_ratio >= 0.45:
            indicators.append({
                "modality": "behaviour",
                "name": "reduced_activity",
                "confidence": round(min(0.88, 0.4 + stillness_ratio / 2.0), 2),
                "description": f"Reduced overall activity detected across {frames_analyzed} sampled frames."
            })

        # High frame difference variance or erratic movement
        if mean_frame_diff > 35.0:
            indicators.append({
                "modality": "behaviour",
                "name": "unusual_erratic_movement",
                "confidence": 0.81,
                "description": "Erratic or rapid movement variations detected in video temporal sequence."
            })

        if not indicators:
            indicators.append({
                "modality": "behaviour",
                "name": "normal_activity_level",
                "confidence": 0.90,
                "description": f"Animal displayed regular movement patterns across all {frames_analyzed} sampled video frames."
            })

        return indicators


behaviour_service = BehaviourService()
