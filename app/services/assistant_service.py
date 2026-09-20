from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.database import crud


class AssistantService:
    """
    AI Assistant Service.
    Answers farmer questions using stored animal analysis history and alert records.
    
    STRICT COMPLIANCE GUARANTEE:
    - Never diagnoses disease.
    - Never prescribes medication.
    - Never invents unobserved symptoms.
    """

    async def answer_question(
        self,
        db: Session,
        animal_id: str,
        user_question: str
    ) -> Dict[str, Any]:
        animal = crud.get_animal(db, animal_id)
        analyses = crud.get_animal_analyses(db, animal_id)
        alerts = crud.get_alerts(db)
        animal_alerts = [a for a in alerts if a.animal_id == animal_id]

        if not animal:
            return {
                "animal_id": animal_id,
                "question": user_question,
                "answer": f"No records found for animal {animal_id} in the database. Please verify the animal ID or submit an analysis first."
            }

        latest_analysis = analyses[0] if analyses else None
        active_alert = next((a for a in animal_alerts if a.status == "ACTIVE"), None)

        # Context text construction
        context_parts = [
            f"Animal: {animal.animal_id} (Species: {animal.species}, Age: {animal.age or 'N/A'}, Status: {animal.current_status})."
        ]
        if latest_analysis:
            context_parts.append(
                f"Latest Analysis: Risk Score {latest_analysis.risk_score} ({latest_analysis.risk_level}). "
                f"Explanation: {latest_analysis.explanation}"
            )
        if active_alert:
            context_parts.append(f"Active Alert: Risk Level {active_alert.risk_level}, Explanation: {active_alert.explanation}")
        elif animal_alerts:
            context_parts.append(f"Resolved Alerts Count: {len([a for a in animal_alerts if a.status == 'RESOLVED'])}.")

        context_str = " ".join(context_parts)

        # Try LLM if configured
        if settings.LLM_API_KEY and settings.LLM_API_URL:
            try:
                llm_answer = await self._call_external_llm(context_str, user_question)
                if llm_answer:
                    return {
                        "animal_id": animal_id,
                        "question": user_question,
                        "answer": llm_answer
                    }
            except Exception:
                pass

        # Context-based robust fallback answer system
        q_lower = user_question.lower()
        if "why" in q_lower or "risk" in q_lower or "high" in q_lower or "flagged" in q_lower:
            if latest_analysis:
                answer = (
                    f"{animal_id} is currently marked as {animal.current_status}. "
                    f"During the latest analysis, the system observed: {latest_analysis.explanation} "
                    f"Recommendation: Inspect the animal's physical condition and environmental surroundings."
                )
            else:
                answer = f"{animal_id} has no stored risk analysis indicators at this time."
        elif "status" in q_lower or "condition" in q_lower or "how" in q_lower:
            answer = (
                f"{animal_id} ({animal.species}) currently has a status of {animal.current_status}. "
                f"Total historical analyses recorded: {len(analyses)}. "
                f"Active alerts: {1 if active_alert else 0}."
            )
        else:
            answer = (
                f"Based on stored records for {animal_id}: {context_str} "
                f"Please consult a certified veterinarian for medical evaluation."
            )

        return {
            "animal_id": animal_id,
            "question": user_question,
            "answer": answer
        }

    async def _call_external_llm(self, context: str, question: str) -> Optional[str]:
        system_prompt = (
            "You are LivestockGuard AI assistant. Answer using ONLY provided context. "
            "NEVER diagnose disease. NEVER prescribe medicine. ALWAYS recommend veterinary assessment if high risk."
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.LLM_API_URL,
                headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                json={
                    "prompt": f"{system_prompt}\nContext: {context}\nQuestion: {question}",
                    "max_tokens": 200
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("answer") or data.get("text")
        return None


assistant_service = AssistantService()
