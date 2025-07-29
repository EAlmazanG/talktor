"""
Persistence Service - Centralized database operations for Talktor

This service provides a high-level API for all database operations,
handling transactions, error management, and complex queries.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
import logging
from contextlib import contextmanager

from core.logging import get_logger
from core.colors import colorize, Colors
from db.database import get_db_session, init_database
from db.crud import SessionCRUD, TranscriptCRUD, FeedbackCRUD, HomeworkCRUD
from db.models import (
    AgentType, ConversationMode, Speaker, FeedbackPillar,
    Session as SessionModel, Transcript, Feedback, HomeworkItem
)

logger = get_logger(__name__)


class PersistenceService:
    """
    Centralized service for all database operations in Talktor.
    
    Provides high-level methods for complex operations, handles transactions,
    and abstracts database details from business logic components.
    """
    
    def __init__(self):
        """Initialize the persistence service"""
        # Initialize database
        init_database()
        
        # CRUD instances
        self.session_crud = SessionCRUD()
        self.transcript_crud = TranscriptCRUD()
        self.feedback_crud = FeedbackCRUD()
        self.homework_crud = HomeworkCRUD()
        
        logger.info("🗄️ PersistenceService initialized")
    
    @contextmanager
    def get_db_transaction(self):
        """
        Context manager for database transactions.
        Automatically commits on success, rolls back on error.
        """
        db = get_db_session()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Database transaction failed: {e}")
            raise
        finally:
            db.close()
    
    # ========================================
    # SESSION OPERATIONS
    # ========================================
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        agent_type: Union[AgentType, str] = AgentType.REALTIME,
        mode: Union[ConversationMode, str] = ConversationMode.FREE_TOPIC,
        topic: Optional[str] = None
    ) -> SessionModel:
        """Create a new conversation session"""
        try:
            # Convert string enums if needed
            if isinstance(agent_type, str):
                agent_type = AgentType(agent_type.lower())
            if isinstance(mode, str):
                mode = ConversationMode(mode.lower())
            
            with self.get_db_transaction() as db:
                session = self.session_crud.create_session(
                    db=db,
                    session_id=session_id,
                    user_id=user_id,
                    agent_type=agent_type,
                    mode=mode,
                    topic=topic
                )
                
                logger.info(f"✅ Created session: {session_id}")
                return session
                
        except Exception as e:
            logger.error(f"❌ Error creating session {session_id}: {e}")
            raise
    
    async def complete_session(
        self,
        session_id: str,
        duration_seconds: int,
        token_count: int = 0,
        estimated_cost: float = 0.0,
        notes: Optional[str] = None
    ) -> Optional[SessionModel]:
        """Mark a session as completed with final metadata"""
        try:
            with self.get_db_transaction() as db:
                session = self.session_crud.update_session_completion(
                    db=db,
                    session_id=session_id,
                    duration_seconds=duration_seconds,
                    token_count=token_count,
                    estimated_cost=estimated_cost,
                    status="completed"
                )
                
                # Add notes if provided
                if notes and session:
                    session.notes = notes
                    db.commit()
                
                logger.info(f"✅ Completed session: {session_id}")
                return session
                
        except Exception as e:
            logger.error(f"❌ Error completing session {session_id}: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get a session by ID"""
        try:
            with self.get_db_transaction() as db:
                session = self.session_crud.get_session_by_id(db, session_id)
                return session
        except Exception as e:
            logger.error(f"❌ Error getting session {session_id}: {e}")
            raise
    
    # ========================================
    # TRANSCRIPT OPERATIONS
    # ========================================
    
    async def save_conversation_transcripts(
        self,
        session_id: str,
        messages: List[Dict[str, Any]]
    ) -> List[Transcript]:
        """
        Save all transcript messages for a conversation in a single transaction
        
        Args:
            session_id: Session identifier
            messages: List of message dicts with 'role', 'content', 'timestamp', etc.
        """
        try:
            with self.get_db_transaction() as db:
                # Get session database ID
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    raise ValueError(f"Session not found: {session_id}")
                
                transcripts = []
                logger.info(f"💬 Saving {len(messages)} transcript messages for session {session_id}")
                
                for i, message in enumerate(messages):
                    # Determine speaker
                    role = message.get("role", "").lower()
                    speaker = Speaker.USER if role == "user" else Speaker.AI
                    
                    # Get content and timestamp
                    content = message.get("content", "").strip()
                    timestamp = message.get("timestamp")
                    
                    # Only save non-empty messages
                    if content:
                        transcript = self.transcript_crud.add_transcript_message(
                            db=db,
                            session_id=session.id,
                            speaker=speaker,
                            content=content,
                            sequence_number=i + 1,
                            confidence_score=message.get("confidence_score"),
                            audio_duration=message.get("audio_duration")
                        )
                        transcripts.append(transcript)
                
                logger.info(f"✅ Saved {len(transcripts)} transcript messages")
                return transcripts
                
        except Exception as e:
            logger.error(f"❌ Error saving transcripts for session {session_id}: {e}")
            raise
    
    async def get_session_transcripts(self, session_id: str) -> List[Transcript]:
        """Get all transcripts for a session"""
        try:
            with self.get_db_transaction() as db:
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    raise ValueError(f"Session not found: {session_id}")
                
                transcripts = self.transcript_crud.get_session_transcripts(db, session.id)
                return transcripts
        except Exception as e:
            logger.error(f"❌ Error getting transcripts for session {session_id}: {e}")
            raise
    
    # ========================================
    # FEEDBACK OPERATIONS
    # ========================================
    
    async def save_conversation_feedback(
        self,
        session_id: str,
        feedback_data: Dict[str, Any]
    ) -> List[Feedback]:
        """
        Save structured feedback for a conversation
        
        Args:
            session_id: Session identifier
            feedback_data: Feedback dict with 'pillars' containing scores and analysis
        """
        try:
            with self.get_db_transaction() as db:
                # Get session database ID
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    raise ValueError(f"Session not found: {session_id}")
                
                feedback_items = []
                pillars = feedback_data.get("pillars", {})
                
                logger.info(f"📊 Saving feedback for session {session_id}")
                
                # Map pillar names to database enum values
                pillar_mapping = {
                    "pronunciation": FeedbackPillar.PRONUNCIATION,
                    "fluency": FeedbackPillar.FLUENCY,
                    "grammar": FeedbackPillar.GRAMMAR,
                    "expressions": FeedbackPillar.EXPRESSIONS,
                    "vocabulary": FeedbackPillar.VOCABULARY,
                    "comprehension": FeedbackPillar.COMPREHENSION
                }
                
                for pillar_name, pillar_data in pillars.items():
                    if pillar_name in pillar_mapping and isinstance(pillar_data, dict):
                        # Extract feedback details
                        score = pillar_data.get("score", 7.0)
                        feedback_text = pillar_data.get("feedback", "")
                        examples = pillar_data.get("examples", [])
                        suggestions = pillar_data.get("suggestions", [])
                        errors = pillar_data.get("errors", [])
                        
                        # Create feedback item
                        feedback = self.feedback_crud.create_feedback_item(
                            db=db,
                            session_id=session.id,
                            pillar=pillar_mapping[pillar_name],
                            score=score,
                            feedback_text=feedback_text,
                            examples=json.dumps(examples) if examples else None,
                            suggestions=json.dumps(suggestions) if suggestions else None,
                            errors=json.dumps(errors) if errors else None,
                            generated_by="standard_agent"
                        )
                        feedback_items.append(feedback)
                
                logger.info(f"✅ Saved {len(feedback_items)} feedback items")
                return feedback_items
                
        except Exception as e:
            logger.error(f"❌ Error saving feedback for session {session_id}: {e}")
            raise
    
    async def get_session_feedback(self, session_id: str) -> List[Feedback]:
        """Get all feedback for a session"""
        try:
            with self.get_db_transaction() as db:
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    raise ValueError(f"Session not found: {session_id}")
                
                feedback = self.feedback_crud.get_session_feedback(db, session.id)
                return feedback
        except Exception as e:
            logger.error(f"❌ Error getting feedback for session {session_id}: {e}")
            raise
    
    # ========================================
    # COMPLEX OPERATIONS
    # ========================================
    
    async def save_complete_conversation(
        self,
        session_id: str,
        user_id: str,
        conversation_json: Dict[str, Any],
        feedback_data: Optional[Dict[str, Any]],
        duration_seconds: int,
        agent_type: Union[AgentType, str] = AgentType.REALTIME,
        mode: Union[ConversationMode, str] = ConversationMode.FREE_TOPIC,
        token_count: int = 0,
        estimated_cost: float = 0.0,
        topic: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a complete conversation in a single atomic transaction.
        This is the main method for persisting conversation data.
        
        Returns:
            Dict with created objects and summary
        """
        try:
            logger.info(colorize(f"💾 STARTING: Save complete conversation {session_id}", Colors.BRIGHT_BLUE))
            logger.info(f"   👤 User: {user_id}")
            logger.info(f"   💬 Messages: {conversation_json.get('message_count', 0)}")
            logger.info(f"   ⏱️ Duration: {duration_seconds}s")
            
            # Convert string enums if needed
            if isinstance(agent_type, str):
                agent_type = AgentType(agent_type.lower())
            if isinstance(mode, str):
                mode = ConversationMode(mode.lower())
            
            with self.get_db_transaction() as db:
                # 1. Create or get session
                logger.info(f"   📝 Step 1: Creating/getting session...")
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    session = self.session_crud.create_session(
                        db=db,
                        session_id=session_id,
                        user_id=user_id,
                        agent_type=agent_type,
                        mode=mode,
                        topic=topic
                    )
                    logger.info(f"   ✅ Session created: {session_id}")
                else:
                    logger.info(f"   🔄 Session found: {session_id}")
                
                # 2. Save complete conversation as single JSON transcript
                logger.info(f"   💬 Step 2: Saving complete conversation JSON...")
                
                # Save the entire conversation as a single JSON transcript
                transcript = self.transcript_crud.add_transcript_message(
                    db=db,
                    session_id=session.id,
                    speaker=Speaker.AI,  # Use AI as default speaker for JSON transcripts
                    content=json.dumps(conversation_json, default=str),  # Convert to JSON string
                    sequence_number=1,  # Single transcript entry
                    confidence_score=0.95,  # High confidence for structured data
                    audio_duration=conversation_json.get('duration_seconds')
                )
                
                logger.info(f"   ✅ Saved complete conversation JSON with {conversation_json.get('message_count', 0)} messages")
                
                # 3. Save feedback
                logger.info(f"   📊 Step 3: Saving feedback data...")
                feedback_items = []
                
                if feedback_data is None:
                    logger.info("   ⚠️ No feedback data provided - skipping feedback save")
                    pillars = {}
                else:
                    pillars = feedback_data.get("pillars", {})
                pillar_mapping = {
                    "pronunciation": FeedbackPillar.PRONUNCIATION,
                    "fluency": FeedbackPillar.FLUENCY,
                    "grammar": FeedbackPillar.GRAMMAR,
                    "expressions": FeedbackPillar.EXPRESSIONS,
                    "vocabulary": FeedbackPillar.VOCABULARY,
                    "comprehension": FeedbackPillar.COMPREHENSION
                }
                
                for pillar_name, pillar_data in pillars.items():
                    if pillar_name in pillar_mapping and isinstance(pillar_data, dict):
                        feedback = self.feedback_crud.create_feedback_item(
                            db=db,
                            session_id=session.id,
                            pillar=pillar_mapping[pillar_name],
                            score=pillar_data.get("score", 7.0),
                            feedback_text=pillar_data.get("feedback", ""),
                            examples=json.dumps(pillar_data.get("examples", [])),
                            suggestions=json.dumps(pillar_data.get("suggestions", [])),
                            errors=json.dumps(pillar_data.get("errors", [])),
                            generated_by="standard_agent"
                        )
                        feedback_items.append(feedback)
                
                logger.info(f"   ✅ Saved {len(feedback_items)} feedback items")
                
                # 4. Complete session
                logger.info(f"   🏁 Step 4: Completing session...")
                session = self.session_crud.update_session_completion(
                    db=db,
                    session_id=session_id,
                    duration_seconds=duration_seconds,
                    token_count=token_count,
                    estimated_cost=estimated_cost,
                    status="completed"
                )
                
                # Add notes if provided
                if notes and session:
                    session.notes = notes
                
                # Prepare result
                result = {
                    "session": session,
                    "transcript": transcript,  # Single JSON transcript
                    "feedback": feedback_items,
                    "conversation_json": conversation_json,
                    "summary": {
                        "session_id": session_id,
                        "user_id": user_id,
                        "duration_seconds": duration_seconds,
                        "message_count": conversation_json.get('message_count', 0),
                        "feedback_count": len(feedback_items),
                        "status": "completed"
                    }
                }
                
                logger.info(colorize(
                    f"✅ Saved complete conversation: {session_id} "
                    f"({conversation_json.get('message_count', 0)} messages, {len(feedback_items)} feedback items)",
                    Colors.BRIGHT_GREEN
                ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Error saving complete conversation {session_id}: {e}")
            raise
    
    # ========================================
    # ANALYTICS & REPORTING
    # ========================================
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user progress analytics"""
        try:
            with self.get_db_transaction() as db:
                # Get user sessions
                sessions = self.session_crud.get_user_sessions(db, user_id)
                
                if not sessions:
                    return {
                        "user_id": user_id,
                        "total_sessions": 0,
                        "total_duration": 0,
                        "average_scores": {},
                        "recent_activity": []
                    }
                
                # Calculate statistics
                total_sessions = len(sessions)
                total_duration = sum(s.duration_seconds or 0 for s in sessions)
                completed_sessions = [s for s in sessions if s.status == "completed"]
                
                # Get all feedback for user sessions
                all_feedback = []
                for session in sessions:
                    feedback = self.feedback_crud.get_session_feedback(db, session.id)
                    all_feedback.extend(feedback)
                
                # Calculate average scores by pillar
                pillar_scores = {}
                for feedback in all_feedback:
                    pillar = feedback.pillar.value
                    if pillar not in pillar_scores:
                        pillar_scores[pillar] = []
                    pillar_scores[pillar].append(feedback.score)
                
                average_scores = {
                    pillar: sum(scores) / len(scores)
                    for pillar, scores in pillar_scores.items()
                }
                
                # Recent activity (last 5 sessions)
                recent_sessions = sorted(sessions, key=lambda s: s.created_at, reverse=True)[:5]
                recent_activity = [
                    {
                        "session_id": s.session_id,
                        "date": s.created_at,
                        "duration": s.duration_seconds,
                        "status": s.status
                    }
                    for s in recent_sessions
                ]
                
                return {
                    "user_id": user_id,
                    "total_sessions": total_sessions,
                    "completed_sessions": len(completed_sessions),
                    "total_duration": total_duration,
                    "average_duration": total_duration / total_sessions if total_sessions > 0 else 0,
                    "average_scores": average_scores,
                    "recent_activity": recent_activity,
                    "last_session": recent_sessions[0].created_at if recent_sessions else None
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting user progress for {user_id}: {e}")
            raise
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session summary with all related data"""
        try:
            with self.get_db_transaction() as db:
                # Get session
                session = self.session_crud.get_session_by_id(db, session_id)
                if not session:
                    return None
                
                # Get transcripts
                transcripts = self.transcript_crud.get_session_transcripts(db, session.id)
                
                # Get feedback
                feedback = self.feedback_crud.get_session_feedback(db, session.id)
                
                # Build conversation text
                conversation_text = "\n".join([
                    f"{t.speaker.value.upper()}: {t.content}"
                    for t in transcripts
                ])
                
                # Organize feedback by pillar
                feedback_by_pillar = {
                    f.pillar.value: {
                        "score": f.score,
                        "feedback": f.feedback_text,
                        "examples": json.loads(f.examples) if f.examples else [],
                        "suggestions": json.loads(f.suggestions) if f.suggestions else [],
                        "errors": json.loads(f.errors) if f.errors else []
                    }
                    for f in feedback
                }
                
                return {
                    "session": {
                        "id": session.session_id,
                        "user_id": session.user_id,
                        "agent_type": session.agent_type.value,
                        "mode": session.mode.value,
                        "topic": session.topic,
                        "status": session.status,
                        "duration_seconds": session.duration_seconds,
                        "token_count": session.token_count,
                        "estimated_cost": session.estimated_cost,
                        "created_at": session.created_at,
                        "ended_at": session.ended_at,
                        "notes": session.notes
                    },
                    "conversation": {
                        "message_count": len(transcripts),
                        "conversation_text": conversation_text,
                        "messages": [
                            {
                                "speaker": t.speaker.value,
                                "content": t.content,
                                "sequence": t.sequence_number,
                                "timestamp": t.timestamp,
                                "confidence": t.confidence_score,
                                "duration": t.audio_duration
                            }
                            for t in transcripts
                        ]
                    },
                    "feedback": {
                        "pillar_count": len(feedback),
                        "average_score": sum(f.score for f in feedback) / len(feedback) if feedback else 0,
                        "pillars": feedback_by_pillar
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting session summary for {session_id}: {e}")
            raise
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and basic stats"""
        try:
            with self.get_db_transaction() as db:
                # Count records in main tables
                session_count = db.query(SessionModel).count()
                transcript_count = db.query(Transcript).count()
                feedback_count = db.query(Feedback).count()
                
                return {
                    "status": "healthy",
                    "database": "connected",
                    "tables": {
                        "sessions": session_count,
                        "transcripts": transcript_count,
                        "feedback": feedback_count
                    },
                    "timestamp": datetime.now(timezone.utc)
                }
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            }


# Singleton instance for global use
persistence_service = PersistenceService()
