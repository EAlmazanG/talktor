"""
Conversation endpoints for the Talktor API
"""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from api.deps import get_db, get_persistence_service, get_user_id_from_header, validate_user_access
from schemas.conversation import (
    ConversationStart, ConversationStartResponse, ConversationEnd, 
    ConversationEndResponse, ConversationDetails, TranscriptResponse
)
from schemas.common import SuccessResponse, ErrorResponse
from services.conversation_flow import ConversationFlow
from services.persistence_service import PersistenceService
from core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(
    request: ConversationStart,
    db: Session = Depends(get_db),
    persistence: PersistenceService = Depends(get_persistence_service)
):
    """
    Start a new conversation session
    """
    try:
        logger.info(f"🚀 Starting conversation for user: {request.user_id}")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Check if session already exists
        existing_session = persistence.session_crud.get_session_by_id(db, session_id)
        if existing_session:
            logger.info(f"✅ Using existing session: {session_id}")
            session = existing_session
        else:
            # Create new session using persistence service
            from db.models import AgentType, ConversationMode
            session = persistence.create_session(
                db=db,
                session_id=session_id,
                user_id=request.user_id,
                agent_type=AgentType.REALTIME,
                mode=ConversationMode.FREE_TOPIC
            )
        
        logger.info(f"✅ Conversation started with session ID: {session_id}")
        
        return ConversationStartResponse(
            session_id=session_id,
            status="started",
            websocket_url=f"/api/v1/conversations/{session_id}/realtime"
        )
        
    except Exception as e:
        logger.error(f"❌ Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.websocket("/{session_id}/realtime")
async def conversation_websocket(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time conversation
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for session: {session_id}")
    
    try:
        # Verify session exists
        persistence = get_persistence_service()
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            await websocket.close(code=4004, reason="Session not found")
            return
        
        # Initialize conversation flow
        conversation_flow = ConversationFlow()
        
        # Handle WebSocket communication
        # Note: This is a simplified version. In production, you'd integrate
        # with the RealtimeAgent's WebSocket handling
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                logger.info(f"📨 Received message for session {session_id}: {data[:100]}...")
                
                # Echo back for now (replace with actual conversation logic)
                await websocket.send_text(f"Echo: {data}")
                
            except WebSocketDisconnect:
                logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
                break
                
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {str(e)}")
        await websocket.close(code=4000, reason="Internal error")


@router.post("/{session_id}/end", response_model=ConversationEndResponse)
async def end_conversation(
    session_id: str,
    request: ConversationEnd,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    End a conversation session
    """
    try:
        logger.info(f"🛑 Ending conversation for session: {session_id}")
        
        # Initialize conversation flow
        conversation_flow = ConversationFlow()
        
        # Get session details before ending
        persistence = get_persistence_service()
        session_summary = persistence.get_session_summary(db, session_id)
        
        if not session_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # End conversation
        await conversation_flow.end_conversation(
            session_id=session_id,
            force_feedback=request.force_feedback
        )
        
        # Get updated session details
        updated_summary = persistence.get_session_summary(db, session_id)
        
        logger.info(f"✅ Conversation ended for session: {session_id}")
        
        return ConversationEndResponse(
            session_id=session_id,
            duration_seconds=updated_summary.session.duration_seconds or 0,
            message_count=updated_summary.message_count,
            status="ended",
            feedback_generated=updated_summary.has_feedback
        )
        
    except Exception as e:
        logger.error(f"❌ Error ending conversation {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end conversation: {str(e)}"
        )


@router.get("/{session_id}", response_model=ConversationDetails)
async def get_conversation_details(
    session_id: str,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    Get detailed conversation information including messages
    """
    try:
        logger.info(f"📋 Getting conversation details for session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session and its database ID
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get session summary
        session_summary = persistence.get_session_summary(db, session_id)
        if not session_summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get conversation transcripts using database ID
        transcripts = persistence.transcript_crud.get_session_transcripts(db, session.id)
        
        # Convert transcripts to messages format
        messages = []
        for transcript in transcripts:
            messages.append({
                "role": "user" if transcript.speaker.value == "user" else "assistant",
                "content": transcript.content,
                "timestamp": transcript.timestamp,
                "order": transcript.sequence_number
            })
        
        return ConversationDetails(
            session_id=session_id,
            user_id=session.user_id,
            duration_seconds=session.duration_seconds,
            message_count=session_summary.get('message_count', 0),
            messages=messages,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting conversation details for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation details: {str(e)}"
        )


@router.get("/{session_id}/transcripts", response_model=List[TranscriptResponse])
async def get_conversation_transcripts(
    session_id: str,
    session_user: tuple = Depends(validate_user_access),
    db: Session = Depends(get_db)
):
    """
    Get conversation transcripts
    """
    try:
        logger.info(f"📝 Getting transcripts for session: {session_id}")
        
        persistence = get_persistence_service()
        
        # Get session and its database ID
        session = persistence.session_crud.get_session_by_id(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get transcripts using database ID
        transcripts = persistence.transcript_crud.get_session_transcripts(db, session.id)
        
        return [TranscriptResponse.from_orm(transcript) for transcript in transcripts]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting transcripts for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transcripts: {str(e)}"
        )
