"""
Feedback endpoints for the Talktor API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_persistence_service, validate_user_access, get_user_id_from_header
from schemas.feedback import FeedbackResponse, FeedbackSummary, UserProgress, FeedbackRequest, PillarFeedback
from schemas.common import SuccessResponse
from services.persistence_service import PersistenceService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/feedback", tags=["feedback"])


def _convert_feedback_to_response(feedback, session_id: str) -> FeedbackResponse:
    """
    Convert database feedback model to API response schema
    """
    if not feedback:
        return None
    
    # Helper function to create pillar feedback
    def create_pillar_feedback(score, summary, errors, suggestions):
        return PillarFeedback(
            score=score,
            summary=summary,
            errors=errors if errors else [],
            suggestions=suggestions if suggestions else []
        )
    
    return FeedbackResponse(
        session_id=session_id,
        overall_score=feedback.overall_score,
        general_feedback=feedback.general_feedback,
        general_summary=feedback.general_summary,
        general_errors=feedback.general_errors if feedback.general_errors else [],
        general_suggestions=feedback.general_suggestions if feedback.general_suggestions else [],
        pronunciation=create_pillar_feedback(
            feedback.pronunciation_score,
            feedback.pronunciation_summary,
            feedback.pronunciation_errors,
            feedback.pronunciation_suggestions
        ),
        fluency=create_pillar_feedback(
            feedback.fluency_score,
            feedback.fluency_summary,
            feedback.fluency_errors,
            feedback.fluency_suggestions
        ),
        grammar=create_pillar_feedback(
            feedback.grammar_score,
            feedback.grammar_summary,
            feedback.grammar_errors,
            feedback.grammar_suggestions
        ),
        expressions=create_pillar_feedback(
            feedback.expressions_score,
            feedback.expressions_summary,
            feedback.expressions_errors,
            feedback.expressions_suggestions
        ),
        vocabulary=create_pillar_feedback(
            feedback.vocabulary_score,
            feedback.vocabulary_summary,
            feedback.vocabulary_errors,
            feedback.vocabulary_suggestions
        ),
        comprehension=create_pillar_feedback(
            feedback.comprehension_score,
            feedback.comprehension_summary,
            feedback.comprehension_errors,
            feedback.comprehension_suggestions
        ),
        created_at=feedback.created_at,
        generated_by=feedback.generated_by or "unknown"
    )


@router.get("/{session_id}", response_model=Optional[FeedbackResponse])
async def get_session_feedback(
    session_id: str,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    Get feedback for a specific session
    """
    try:
        logger.info(f"📊 Getting feedback for session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session and its database ID
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get feedback using database ID
        feedback = persistence.feedback_crud.get_session_feedback(db, session.id)
        
        if not feedback:
            logger.info(f"📊 No feedback found for session: {session_id}")
            return None
        
        response = _convert_feedback_to_response(feedback, session_id)
        logger.info(f"✅ Retrieved feedback for session: {session_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting feedback for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


@router.get("/{session_id}/summary", response_model=Optional[FeedbackSummary])
async def get_feedback_summary(
    session_id: str,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    Get a summary of feedback for a session (lighter version)
    """
    try:
        logger.info(f"📈 Getting feedback summary for session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session and its database ID
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get feedback using database ID
        feedback = persistence.feedback_crud.get_session_feedback(db, session.id)
        
        if not feedback:
            logger.info(f"📈 No feedback found for session: {session_id}")
            return None
        
        pillar_scores = {
            "pronunciation": feedback.pronunciation_score,
            "fluency": feedback.fluency_score,
            "grammar": feedback.grammar_score,
            "expressions": feedback.expressions_score,
            "vocabulary": feedback.vocabulary_score,
            "comprehension": feedback.comprehension_score
        }
        
        return FeedbackSummary(
            session_id=session_id,
            overall_score=feedback.overall_score,
            general_summary=feedback.general_summary,
            pillar_scores=pillar_scores,
            created_at=feedback.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting feedback summary for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback summary: {str(e)}"
        )


@router.post("/{session_id}/generate", response_model=SuccessResponse)
async def generate_feedback(
    session_id: str,
    request: FeedbackRequest,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    Manually trigger feedback generation for a session
    """
    try:
        logger.info(f"🔄 Generating feedback for session: {session_id}")
        
        # Get session and its database ID
        persistence = get_persistence_service()
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if feedback already exists using database ID
        existing_feedback = persistence.feedback_crud.get_session_feedback(db, session.id)
        
        if existing_feedback and not request.force_generation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feedback already exists for this session. Use force_generation=true to regenerate."
            )
        
        # Get session to verify it exists and has transcripts
        session_summary = persistence.get_session_summary(db, session_id)
        if not session_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session_summary.get('message_count', 0) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot generate feedback for session with no messages"
            )
        
        # TODO: Implement manual feedback generation
        # This would involve calling the ConversationService to generate feedback
        # For now, return a placeholder response
        
        logger.info(f"✅ Feedback generation triggered for session: {session_id}")
        
        return SuccessResponse(
            message="Feedback generation triggered successfully",
            data={"session_id": session_id, "status": "processing"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating feedback for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feedback: {str(e)}"
        )


@router.get("/users/{user_id}/progress", response_model=UserProgress)
async def get_user_progress(
    user_id: str,
    current_user: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Get user progress across all sessions
    """
    try:
        # Verify user can access this data (users can only see their own progress)
        if user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own progress"
            )
        
        logger.info(f"📊 Getting progress for user: {user_id}")
        
        persistence = get_persistence_service()
        progress = persistence.get_user_progress(db, user_id)
        
        if not progress:
            # Return empty progress for users with no sessions
            return UserProgress(
                user_id=user_id,
                total_sessions=0,
                average_score=None,
                latest_session_date=None,
                pillar_averages={},
                improvement_areas=[],
                strengths=[]
            )
        
        # Determine improvement areas and strengths based on scores
        pillar_averages = progress.get("pillar_averages", {})
        improvement_areas = []
        strengths = []
        
        for pillar, score in pillar_averages.items():
            if score is not None:
                if score < 6.0:
                    improvement_areas.append(pillar)
                elif score >= 8.0:
                    strengths.append(pillar)
        
        return UserProgress(
            user_id=user_id,
            total_sessions=progress.get("total_sessions", 0),
            average_score=progress.get("average_score"),
            latest_session_date=progress.get("latest_session_date"),
            pillar_averages=pillar_averages,
            improvement_areas=improvement_areas,
            strengths=strengths
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user progress for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user progress: {str(e)}"
        )
