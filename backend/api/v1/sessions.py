"""
Session endpoints for the Talktor API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.deps import get_db, get_persistence_service, get_user_id_from_header, CommonQueryParams
from schemas.session import SessionCreate, SessionResponse, SessionSummary, SessionListResponse
from schemas.common import SuccessResponse, HealthCheckResponse
from services.persistence_service import PersistenceService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    user_id: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation session
    """
    try:
        logger.info(f"🆕 Creating session for user: {request.user_id}")
        
        # Verify user can create session for this user_id
        if request.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create session for different user"
            )
        
        persistence = get_persistence_service()
        
        # Create session
        session = persistence.create_session(
            db=db,
            user_id=request.user_id,
            agent_type=request.agent_type,
            mode=request.mode,
            topic=request.topic
        )
        
        logger.info(f"✅ Session created: {session.session_id}")
        
        return SessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Get session details by ID
    """
    try:
        logger.info(f"📋 Getting session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify user access
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Session belongs to different user"
            )
        
        # Get session summary
        session_summary = persistence.get_session_summary(db, session_id)
        
        return SessionSummary(
            session=SessionResponse.from_orm(session),
            message_count=session_summary.get('message_count', 0) if session_summary else 0,
            has_feedback=session_summary.get('has_feedback', False) if session_summary else False,
            feedback_score=session_summary.get('feedback_score') if session_summary else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=SessionListResponse)
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
                message_count=session_summary.message_count if session_summary else 0,
                has_feedback=session_summary.has_feedback if session_summary else False,
                feedback_score=session_summary.feedback_score if session_summary else None
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


@router.delete("/{session_id}", response_model=SuccessResponse)
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
):
    """
    Delete a session (soft delete - marks as deleted)
    """
    try:
        logger.info(f"🗑️ Deleting session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session to verify ownership
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Verify user access
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Session belongs to different user"
            )
        
        # Soft delete session
        success = persistence.session_crud.delete_session(db, session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete session"
            )
        
        logger.info(f"✅ Session deleted: {session_id}")
        
        return SuccessResponse(
            message="Session deleted successfully",
            data={"session_id": session_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: Session = Depends(get_db)
):
    """
    Health check endpoint for sessions service
    """
    try:
        persistence = get_persistence_service()
        health_info = persistence.health_check(db)
        
        return HealthCheckResponse(
            status="healthy",
            database="connected",
            services={
                "sessions": "healthy",
                "database": "connected",
                "total_sessions": str(health_info.get("total_sessions", 0))
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            database="disconnected",
            services={
                "sessions": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
