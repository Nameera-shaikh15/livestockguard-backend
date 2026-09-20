from typing import Dict, Any, List
from app.config import settings


class EnvironmentService:
    """
    Farm Condition / Environmental Analysis Service.
    Calculates Temperature Humidity Index (THI) and evaluates environmental risk conditions.
    
    IMPORTANT: Environmental thresholds (THI limits) are configurable prototype parameters
    and are NOT clinically or medically validated.
    """

    def analyze_environment(
        self,
        temperature: float,
        humidity: float
    ) -> Dict[str, Any]:
        indicators = []
        structured_indicators = []
        risk_score = 15  # Baseline minimal environment risk

        # Calculate THI (Temperature Humidity Index for Livestock Heat Stress)
        # Standard formula: THI = (1.8 * T + 32) - (0.55 - 0.0055 * RH) * (1.8 * T - 26)
        thi = (1.8 * temperature + 32) - (0.55 - 0.0055 * humidity) * (1.8 * temperature - 26)

        # Cold stress check
        if temperature < 5.0:
            risk_score += 45
            indicators.append("cold_stress_risk_environment")
            structured_indicators.append({
                "modality": "environment",
                "name": "cold_stress_risk_environment",
                "confidence": 0.85,
                "description": f"Low ambient temperature ({temperature:.1f}°C) poses potential cold stress risk for animals."
            })

        # High heat & humidity check
        if thi >= settings.THI_SEVERE_STRESS or temperature >= settings.TEMP_HIGH_TH:
            risk_score = max(risk_score, 82)
            indicators.append("extreme_heat_risk_environment")
            structured_indicators.append({
                "modality": "environment",
                "name": "extreme_heat_risk_environment",
                "confidence": 0.92,
                "description": f"Critical environmental heat index (THI: {thi:.1f}, Temp: {temperature:.1f}°C, Humidity: {humidity:.1f}%) indicates severe heat risk."
            })
        elif thi >= settings.THI_MODERATE_STRESS or temperature >= settings.TEMP_WARNING_TH or humidity >= settings.HUMIDITY_HIGH_TH:
            risk_score = max(risk_score, 68)
            indicators.append("potential_heat_stress_environment")
            structured_indicators.append({
                "modality": "environment",
                "name": "potential_heat_stress_environment",
                "confidence": 0.88,
                "description": f"Elevated environmental temperature ({temperature:.1f}°C) and humidity ({humidity:.1f}%, THI: {thi:.1f}) indicate potential heat stress risk."
            })

        if humidity >= settings.HUMIDITY_HIGH_TH and "extreme_heat_risk_environment" not in indicators and "potential_heat_stress_environment" not in indicators:
            risk_score += 25
            indicators.append("high_humidity_risk_environment")
            structured_indicators.append({
                "modality": "environment",
                "name": "high_humidity_risk_environment",
                "confidence": 0.75,
                "description": f"High relative humidity ({humidity:.1f}%) increases environmental microbial and moisture stress."
            })

        if not indicators:
            indicators.append("normal_environmental_conditions")
            structured_indicators.append({
                "modality": "environment",
                "name": "normal_environmental_conditions",
                "confidence": 0.90,
                "description": f"Ambient temperature ({temperature:.1f}°C) and humidity ({humidity:.1f}%) are within standard comfort range."
            })

        risk_score = min(100, max(0, risk_score))

        explanation = (
            f"Environmental analysis evaluated temperature of {temperature:.1f}°C and humidity of {humidity:.1f}% "
            f"(Calculated THI: {thi:.1f}). Identified risk indicators: {', '.join(indicators)}."
        )

        return {
            "temperature": temperature,
            "humidity": humidity,
            "thi": round(thi, 1),
            "risk_score": risk_score,
            "indicators": indicators,
            "structured_indicators": structured_indicators,
            "explanation": explanation
        }


environment_service = EnvironmentService()
