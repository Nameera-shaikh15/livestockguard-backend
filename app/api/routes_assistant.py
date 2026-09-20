from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.assistant_service import assistant_service

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class AssistantRequest(BaseModel):
    animal_id: str
    user_question: str


@router.post("")
async def query_assistant(request: AssistantRequest, db: Session = Depends(get_db)):
    """
    Query AI Assistant regarding animal health context, risk factors, or alerts.
    
    STRICT NON-DIAGNOSTIC GUARANTEE:
    Answers rely exclusively on stored analysis observations. Does NOT diagnose disease
    or prescribe treatment.
    """
    if not request.animal_id or not request.user_question:
        raise HTTPException(status_code=400, detail="animal_id and user_question are required.")

    return await assistant_service.answer_question(
        db=db,
        animal_id=request.animal_id,
        user_question=request.user_question
    )
