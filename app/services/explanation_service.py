from typing import List, Dict, Any


class ExplanationService:
    """
    Explainability Service.
    Generates transparent, evidence-based explanations and non-prescriptive recommendations based ONLY
    on observed indicators.
    
    STRICT NON-DIAGNOSTIC POLICY:
    - Never outputs disease diagnoses.
    - Never prescribes medications.
    - Uses non-diagnostic terms: 'potential health risk', 'indicator', 'signal', 'anomaly', 'risk condition'.
    """

    EXACT_RECOMMENDATION = (
        "Inspect the animal's movement, feeding behaviour, and physical condition. "
        "Review the farm's temperature, humidity, shade and ventilation conditions. "
        "If concerning signs persist, seek veterinary assessment."
    )

    def generate_explanation(
        self,
        animal_id: str,
        risk_level: str,
        indicators: List[Dict[str, Any]]
    ) -> str:
        # Filter for concerning or non-normal indicators
        concerning = [
            ind for ind in indicators 
            if not ind["name"].startswith("normal_") and ind["confidence"] >= 0.50
        ]

        if not concerning or risk_level == "NORMAL":
            return f"{animal_id} showed normal observable physical activity, acoustic patterns, and environmental risk levels."

        descriptions = []
        for ind in concerning:
            clean_name = ind["name"].replace("_", " ")
            descriptions.append(clean_name)

        why_str = ", ".join(descriptions)
        
        return (
            f"{animal_id} was flagged with risk level {risk_level} because potential health risk indicators "
            f"were observed: {why_str}."
        )

    def generate_recommendation(self, risk_level: str) -> str:
        return self.EXACT_RECOMMENDATION


explanation_service = ExplanationService()
