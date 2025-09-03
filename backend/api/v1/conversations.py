"""
Conversation endpoints for the Talktor API
"""
import uuid
import json
import asyncio
import base64
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
import re
from sqlalchemy.orm import Session

from api.deps import get_db, get_persistence_service, get_user_id_from_header, validate_user_access
from schemas.conversation import (
    ConversationStart, ConversationStartResponse, ConversationEnd, 
    ConversationEndResponse, ConversationDetails, TranscriptResponse
)
from schemas.common import SuccessResponse, ErrorResponse
from services.persistence_service import PersistenceService
from services.openai_service import OpenAIService
from services.session_state import SessionState
from services.conversation_service import ConversationService
from core.logging import get_logger
from prompts import REQUEST_FEEDBACK_MESSAGE_TEXT

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
    WebSocket endpoint for real-time conversation bridging to OpenAI Realtime API.
    Protocol:
    - Text JSON messages:
      {"type":"input_text","text":"..."} -> send user text to OpenAI and trigger response
      {"type":"audio_commit"} -> commit current input_audio_buffer and trigger response
      {"type":"end"} -> finalize session, persist, and close
      Any other JSON payload -> forwarded to OpenAI as-is
    - Binary messages: treated as raw PCM16 audio chunks and forwarded upstream
    - Outbound: we forward key events to the client as JSON; AI audio is streamed as binary frames
    """
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected for session: {session_id}")

    persistence = get_persistence_service()
    session = persistence.session_crud.get_session_by_id(db, session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    user_id = session.user_id

    # Initialize state and services
    session_state = SessionState(session_id=session_id, user_id=user_id)
    openai_service = OpenAIService()
    conversation_service = ConversationService()

    # Lightweight agent adapter to satisfy ConversationService expectations
    class WSAgentAdapter:
        def __init__(self):
            self.conversation_feedback = None
            self._finalized = False
        async def stop_conversation(self):
            await finalize(reason="agent_stop")
        async def _schedule_auto_termination_after_feedback(self):
            await asyncio.sleep(3)
            await finalize(reason="auto_after_feedback")

    agent_adapter = WSAgentAdapter()
    session_state.agent = agent_adapter

    # Idempotent finalization
    finalized = False
    finalize_lock = asyncio.Lock()

    async def finalize(reason: str = "client_end"):
        nonlocal finalized
        if finalized:
            return
        async with finalize_lock:
            if finalized:
                return
            finalized = True
            try:
                session_state.stop_session()
                # Close upstream connection
                await openai_service.close_connection(session_state)
            except Exception as e:
                logger.error(f"Error closing upstream connection: {e}")

            # Build summary and persist
            try:
                summary = conversation_service.get_conversation_summary(session_state)
                duration_seconds = int(summary.get("duration_seconds", 0) or 0)
                feedback_data = getattr(agent_adapter, "conversation_feedback", None)

                # Persist complete conversation (JSON) and feedback
                try:
                    await persistence.save_complete_conversation(
                        session_id=session_id,
                        user_id=user_id,
                        conversation_json=summary.get("conversation_json", summary),
                        feedback_data=feedback_data,
                        duration_seconds=duration_seconds,
                        agent_type="realtime",
                        mode="free_topic"
                    )
                except Exception as persist_err:
                    logger.error(f"Error saving complete conversation: {persist_err}")

                # Send final message (best-effort)
                end_payload = {
                    "type": "ended",
                    "session_id": session_id,
                    "duration_seconds": duration_seconds,
                    "message_count": summary.get("message_count", 0),
                    "status": "ended",
                    "feedback_generated": bool(feedback_data)
                }
                try:
                    await websocket.send_text(json.dumps(end_payload))
                except Exception:
                    pass
            finally:
                try:
                    await websocket.close(code=1000)
                except Exception:
                    pass

    # Helper: request structured feedback explicitly and set a safety timeout
    feedback_requested = False

    async def request_feedback():
        nonlocal feedback_requested
        if feedback_requested:
            return
        feedback_requested = True
        try:
            # Send special user message to trigger feedback function call
            await openai_service.send_message(session_state, {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": REQUEST_FEEDBACK_MESSAGE_TEXT}]
                }
            })
            await openai_service.send_message(session_state, {"type": "response.create"})
            logger.info("📣 Explicit feedback request sent to OpenAI")
        except Exception as e:
            logger.error(f"Error sending feedback request: {e}")

        # Safety: if no feedback arrives within 6s, finalize anyway to avoid hanging
        async def safety_finalize():
            await asyncio.sleep(6)
            if not finalized and not getattr(agent_adapter, "conversation_feedback", None):
                logger.warning("⚠️ Feedback not received within 6s. Finalizing session without feedback.")
                await finalize(reason="safety_no_feedback")

        asyncio.create_task(safety_finalize())

    # Helper: detect explicit end-of-conversation commands (NOT farewells)
    END_PATTERNS = [
        r"\bend\b",
        r"\bfinish\b",
        r"\bstop\b",
        r"\bend\s+(conversation|session)\b",
        r"\b(stop|finish)\s+(conversation|session)\b",
        r"\bterminamos\b",
        r"\bterminar\b",
        r"\bfinalizar\b",
        r"\bfinaliza(r)?\b",
    ]

    def is_end_phrase(text: str) -> bool:
        s = (text or "").strip().lower()
        if not s:
            return False

        # Normalize punctuation spacing
        import re as _re
        s_norm = _re.sub(r"[^\w\s]", "", s)
        words = s_norm.split()

        # Exact single-word explicit commands
        if len(words) == 1 and words[0] in {"end", "stop", "finish", "quit", "exit"}:
            return True

        # Explicit multi-word phrases
        patterns = [
            r"^(please\s+)?(end|stop|finish)\s+(the\s+)?(conversation|session)\b",
            r"^(end|stop|finish)\s+now\b",
            r"^(end|stop|finish)\s+it\b",
            r"^(end|stop|finish)\s+this\s+(conversation|session)\b",
            # Spanish explicit phrases (avoid farewells like adios/chao)
            r"^(terminamos)$",
            r"^terminar(\s+la\s+)?(conversacion|sesion)$",
            r"^finalizar(\s+la\s+)?(conversacion|sesion)$",
            r"^finaliza(r)?$",
        ]
        for pat in patterns:
            if _re.search(pat, s_norm):
                return True
        return False

    # Upstream connection
    try:
        ws = await openai_service.connect_websocket(session_state)
        if not ws:
            raise RuntimeError("Failed to connect to OpenAI WebSocket")
        await openai_service.send_session_config(session_state)
    except Exception as e:
        logger.error(f"❌ Upstream connection error for session {session_id}: {e}")
        await websocket.close(code=1011, reason="Upstream connection failed")
        return

    # Handle messages from OpenAI and forward to client
    async def handle_openai_message(message: dict, state: SessionState):
        try:
            event_type = message.get("type", "")

            if event_type == "session.created":
                await websocket.send_text(json.dumps({"type": "session.created"}))
                return

            # User started speaking (detected by OpenAI VAD) -> barge-in
            if event_type == "input_audio_buffer.speech_started":
                # 1) Ask OpenAI to cancel any ongoing response to stop further TTS
                try:
                    await openai_service.send_message(state, {"type": "response.cancel"})
                except Exception:
                    # It's ok if there's no active response
                    pass
                # 2) Tell client to clear its local playback buffer for instant stop
                try:
                    await websocket.send_text(json.dumps({"type": "playback.clear", "reason": "speech_started"}))
                except Exception:
                    pass
                return

            if event_type == "response.audio.delta":
                delta_b64 = message.get("delta", "")
                if delta_b64:
                    try:
                        audio_bytes = base64.b64decode(delta_b64)
                        await websocket.send_bytes(audio_bytes)
                    except Exception:
                        # Fallback to JSON if binary send fails
                        await websocket.send_text(json.dumps({"type": "audio.delta.b64", "delta": delta_b64}))
                return

            if event_type == "conversation.item.input_audio_transcription.delta":
                delta = message.get("delta", "")
                if delta:
                    state.add_user_transcript(delta)
                    await websocket.send_text(json.dumps({"type": "user_transcript.delta", "delta": delta}))
                return

            if event_type == "conversation.item.input_audio_transcription.completed":
                transcript = message.get("transcript", "")
                if transcript:
                    conversation_service.update_conversation_context(state, "user", transcript)
                    await websocket.send_text(json.dumps({"type": "user_transcript.completed", "transcript": transcript}))
                    # If user said an end phrase, cancel playback and request feedback explicitly
                    if is_end_phrase(transcript):
                        try:
                            await openai_service.send_message(state, {"type": "response.cancel"})
                        except Exception:
                            pass
                        # Notify client to clear any remaining playback then end
                        try:
                            await websocket.send_text(json.dumps({"type": "playback.clear", "reason": "end_phrase"}))
                        except Exception:
                            pass
                        await request_feedback()
                return

            if event_type == "response.audio_transcript.delta":
                delta = message.get("delta", "")
                if delta:
                    state.add_ai_transcript(delta)
                    await websocket.send_text(json.dumps({"type": "ai_transcript.delta", "delta": delta}))
                return

            if event_type == "response.audio_transcript.done":
                transcript = message.get("transcript", "")
                if transcript:
                    conversation_service.update_conversation_context(state, "ai", transcript)
                    await websocket.send_text(json.dumps({"type": "ai_transcript.completed", "transcript": transcript}))
                return

            if event_type == "response.function_call_arguments.done":
                # Let ConversationService process the function call and send result back upstream
                result, call_id = await conversation_service.handle_function_call(message, state)
                await openai_service.send_function_call_result(state, result, call_id)
                await websocket.send_text(json.dumps({"type": "function_call.handled", "call_id": call_id}))
                return

            if event_type == "error":
                await websocket.send_text(json.dumps({"type": "error", "payload": message.get("error", {})}))
                return

            # Default: forward minimal event info to client
            await websocket.send_text(json.dumps({"type": "upstream", "event": event_type}))
        except Exception as e:
            logger.error(f"Error handling upstream message: {e}")

    upstream_task = asyncio.create_task(openai_service.receive_messages(session_state, handle_openai_message))

    # Client message loop
    try:
        while True:
            incoming = await websocket.receive()

            # Text messages
            if incoming.get("text") is not None:
                text_msg = incoming["text"]
                # Try JSON first
                payload = None
                try:
                    payload = json.loads(text_msg)
                except json.JSONDecodeError:
                    payload = None

                if payload and isinstance(payload, dict):
                    msg_type = payload.get("type")

                    if msg_type == "end":
                        # Cancel ongoing TTS and clear playback immediately
                        try:
                            await openai_service.send_message(session_state, {"type": "response.cancel"})
                        except Exception:
                            pass
                        try:
                            await websocket.send_text(json.dumps({"type": "playback.clear", "reason": "client_end"}))
                        except Exception:
                            pass
                        # If we already have feedback, finalize; otherwise request it
                        if getattr(agent_adapter, "conversation_feedback", None):
                            await finalize(reason="client_end_with_feedback")
                        else:
                            await request_feedback()
                        continue

                    if msg_type == "input_text":
                        user_text = payload.get("text", "")
                        if user_text:
                            # If text itself is an end phrase, request feedback instead of normal reply
                            if is_end_phrase(user_text):
                                try:
                                    await openai_service.send_message(session_state, {"type": "response.cancel"})
                                except Exception:
                                    pass
                                await request_feedback()
                                continue
                            await openai_service.send_message(session_state, {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [{"type": "input_text", "text": user_text}]
                                }
                            })
                            await openai_service.send_message(session_state, {"type": "response.create"})
                        continue

                    if msg_type == "audio_commit":
                        # With server-side VAD enabled, OpenAI will automatically
                        # create a response after commit. Avoid sending response.create
                        # here to prevent the model from replying twice or talking to itself.
                        try:
                            logger.info(f"🎙️ audio_commit received (session={session_id})")
                        except Exception:
                            pass
                        await openai_service.send_message(session_state, {"type": "input_audio_buffer.commit"})
                        continue

                    # Passthrough: forward unknown JSON as-is to OpenAI
                    await openai_service.send_message(session_state, payload)
                    continue

                # Plain text commands
                if text_msg.strip().lower() in {"end", "stop", "finish"}:
                    try:
                        await openai_service.send_message(session_state, {"type": "response.cancel"})
                    except Exception:
                        pass
                    try:
                        await websocket.send_text(json.dumps({"type": "playback.clear", "reason": "client_end"}))
                    except Exception:
                        pass
                    if getattr(agent_adapter, "conversation_feedback", None):
                        await finalize(reason="client_end_with_feedback")
                    else:
                        await request_feedback()
                    continue

                # Plain text treated as user message
                await openai_service.send_message(session_state, {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": text_msg}]
                    }
                })
                await openai_service.send_message(session_state, {"type": "response.create"})
                continue

            # Binary messages -> audio chunks
            if incoming.get("bytes") is not None:
                audio_bytes = incoming["bytes"]
                try:
                    logger.info(f"🎧 received audio chunk: {len(audio_bytes)} bytes (session={session_id})")
                except Exception:
                    pass
                encoded = base64.b64encode(audio_bytes).decode("utf-8")
                await openai_service.send_audio_chunk(session_state, encoded)
                continue

            # Handle disconnects
            if incoming.get("type") == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for session {session_id}: {str(e)}")
    finally:
        try:
            if not upstream_task.done():
                upstream_task.cancel()
                try:
                    await upstream_task
                except asyncio.CancelledError:
                    pass
        finally:
            await finalize(reason="disconnect")


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
        
        # Use persistence to validate and complete session
        persistence = get_persistence_service()

        # Verify session exists
        session_obj = persistence.session_crud.get_session_by_id(db, session_id)
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Compute duration if absent
        now = datetime.now(timezone.utc)
        created_at = session_obj.created_at
        if created_at is not None and created_at.tzinfo is None:
            from datetime import timezone as _tz
            created_at = created_at.replace(tzinfo=_tz.utc)
        duration_seconds = session_obj.duration_seconds or (
            int((now - created_at).total_seconds()) if created_at else 0
        )

        # Finalize session (no agent/service changes)
        try:
            await persistence.complete_session(
                session_id=session_id,
                duration_seconds=duration_seconds
            )
        except Exception as e:
            logger.error(f"❌ Error completing session {session_id}: {e}")

        # Get updated session summary for response
        updated_summary = persistence.get_session_summary(db, session_id) or {}
        session_data = updated_summary.get("session", {}) or {}
        
        logger.info(f"✅ Conversation ended for session: {session_id}")
        
        return ConversationEndResponse(
            session_id=session_id,
            duration_seconds=session_data.get("duration_seconds", 0) or 0,
            message_count=updated_summary.get("message_count", 0),
            status="ended",
            feedback_generated=updated_summary.get("has_feedback", False)
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
        
        # Map ORM objects to API schema, converting internal DB id to external string session_id
        transcript_responses = []
        for t in transcripts:
            transcript_responses.append(TranscriptResponse(
                session_id=session.session_id,
                speaker=t.speaker,
                content=t.content,
                sequence_number=t.sequence_number,
                timestamp=t.timestamp,
                confidence_score=t.confidence_score,
                audio_duration=t.audio_duration,
            ))
        
        return transcript_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting transcripts for {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transcripts: {str(e)}"
        )
