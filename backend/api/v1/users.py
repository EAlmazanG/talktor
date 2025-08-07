"""
User endpoints for the Talktor API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_persistence_service, get_user_id_from_header, CommonQueryParams
from schemas.session import SessionListResponse, SessionSummary, SessionResponse
from schemas.feedback import UserProgress
from schemas.common import SuccessResponse
from services.persistence_service import PersistenceService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/sessions", response_model=SessionListResponse)
async def get_user_sessions(
    user_id: str,
    current_user: str = Depends(get_user_id_from_header),
    query_params: CommonQueryParams = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get all sessions for a user with pagination
    """
    try:
        # Verify user can access this data
        if user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own sessions"
            )
        
        logger.info(f"📋 Getting sessions for user: {user_id} (page {query_params.page})")
        
        persistence = get_persistence_service()
        
        # Get sessions with pagination
        sessions = persistence.session_crud.get_user_sessions(
            db=db,
            user_id=user_id,
            offset=query_params.offset,
            limit=query_params.page_size
        )
        
        # Get total count
        total_sessions = persistence.session_crud.count_user_sessions(db, user_id)
        
        # Convert to session summaries
        session_summaries = []
        for session in sessions:
            # Get additional session data
            session_summary = persistence.get_session_summary(db, session.session_id)
            
            session_summaries.append(SessionSummary(
                session=SessionResponse.from_orm(session),
                message_count=session_summary.get('message_count', 0) if session_summary else 0,
                has_feedback=session_summary.get('has_feedback', False) if session_summary else False,
                feedback_score=session_summary.get('feedback_score') if session_summary else None
            ))
        
        return SessionListResponse(
            sessions=session_summaries,
            total=total_sessions,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting sessions for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user sessions: {str(e)}"
        )


@router.get("/{user_id}/progress", response_model=UserProgress)
async def get_user_progress(
    user_id: str,
    current_user: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Get user progress across all sessions
    """
    try:
        # Verify user can access this data
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


@router.get("/{user_id}/stats", response_model=dict)
async def get_user_stats(
    user_id: str,
    current_user: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Get user statistics summary
    """
    try:
        # Verify user can access this data
        if user_id != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own statistics"
            )
        
        logger.info(f"📈 Getting statistics for user: {user_id}")
        
        persistence = get_persistence_service()
        
        # Get user progress
        progress = persistence.get_user_progress(db, user_id)
        
        # Get recent sessions
        recent_sessions = persistence.session_crud.get_user_sessions(
            db=db,
            user_id=user_id,
            offset=0,
            limit=5
        )
        
        # Calculate additional stats
        stats = {
            "user_id": user_id,
            "total_sessions": progress.get("total_sessions", 0) if progress else 0,
            "average_score": progress.get("average_score") if progress else None,
            "latest_session_date": progress.get("latest_session_date") if progress else None,
            "recent_sessions_count": len(recent_sessions),
            "pillar_averages": progress.get("pillar_averages", {}) if progress else {},
            "has_recent_activity": len(recent_sessions) > 0,
            "learning_streak": 0  # TODO: Calculate learning streak
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user stats for {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user statistics: {str(e)}"
        )
