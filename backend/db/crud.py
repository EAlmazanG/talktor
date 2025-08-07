"""
CRUD operations for Talktor database models
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .models import Session as SessionModel, Transcript, Feedback, HomeworkItem, VocabularyItem
from .models import AgentType, ConversationMode, Speaker
from core.logging import get_logger

logger = get_logger(__name__)


class SessionCRUD:
    """CRUD operations for Session model"""
    
    @staticmethod
    def create_session(
        db: Session,
        session_id: str,
        user_id: str,
        agent_type: AgentType,
        mode: ConversationMode,
        topic: Optional[str] = None
    ) -> SessionModel:
        """Create a new session"""
        try:
            db_session = SessionModel(
                session_id=session_id,
                user_id=user_id,
                agent_type=agent_type,
                mode=mode,
                topic=topic,
                status="active"
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            logger.info(f"✅ Created session: {session_id}")
            return db_session
        except Exception as e:
            logger.error(f"❌ Error creating session {session_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_session_by_id(db: Session, session_id: str) -> Optional[SessionModel]:
        """Get session by session_id"""
        return db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    
    @staticmethod
    def update_session_completion(
        db: Session,
        session_id: str,
        duration_seconds: int,
        token_count: int,
        estimated_cost: float,
        status: str = "completed"
    ) -> Optional[SessionModel]:
        """Update session when completed"""
        try:
            db_session = SessionCRUD.get_session_by_id(db, session_id)
            if db_session:
                db_session.duration_seconds = duration_seconds
                db_session.token_count = token_count
                db_session.estimated_cost = estimated_cost
                db_session.status = status
                db_session.ended_at = datetime.utcnow()
                db.commit()
                db.refresh(db_session)
                logger.info(f"✅ Updated session completion: {session_id}")
                return db_session
            else:
                logger.warning(f"⚠️ Session not found: {session_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error updating session {session_id}: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[SessionModel]:
        """Get sessions for a specific user"""
        return (
            db.query(SessionModel)
            .filter(SessionModel.user_id == user_id)
            .order_by(desc(SessionModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )


class TranscriptCRUD:
    """CRUD operations for Transcript model"""
    
    @staticmethod
    def add_transcript_message(
        db: Session,
        session_id: int,  # Database ID, not session_id string
        speaker: Speaker,
        content: str,
        sequence_number: int,
        confidence_score: Optional[float] = None,
        audio_duration: Optional[float] = None
    ) -> Transcript:
        """Add a transcript message to the conversation"""
        try:
            transcript = Transcript(
                session_id=session_id,
                speaker=speaker,
                content=content,
                sequence_number=sequence_number,
                confidence_score=confidence_score,
                audio_duration=audio_duration
            )
            db.add(transcript)
            db.commit()
            db.refresh(transcript)
            logger.debug(f"✅ Added transcript message: {speaker} - {len(content)} chars")
            return transcript
        except Exception as e:
            logger.error(f"❌ Error adding transcript: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_session_transcripts(
        db: Session,
        session_id: int,
        order_by_sequence: bool = True
    ) -> List[Transcript]:
        """Get all transcripts for a session"""
        query = db.query(Transcript).filter(Transcript.session_id == session_id)
        if order_by_sequence:
            query = query.order_by(Transcript.sequence_number)
        return query.all()
    
    @staticmethod
    def get_full_conversation_text(
        db: Session,
        session_id: int,
        speaker: Optional[Speaker] = None
    ) -> str:
        """Get full conversation as concatenated text"""
        query = db.query(Transcript).filter(Transcript.session_id == session_id)
        if speaker:
            query = query.filter(Transcript.speaker == speaker)
        
        transcripts = query.order_by(Transcript.sequence_number).all()
        return "\n".join([f"{t.speaker.value}: {t.content}" for t in transcripts])


class FeedbackCRUD:
    """CRUD operations for Feedback model"""
    
    @staticmethod
    def get_session_feedback(
        db: Session,
        session_id: int
    ) -> Optional[Feedback]:
        """Get feedback for a session (single row)"""
        return db.query(Feedback).filter(Feedback.session_id == session_id).first()
    
    @staticmethod
    def create_comprehensive_feedback(
        db: Session,
        session_id: int,
        # General feedback
        general_feedback: str = None,
        general_summary: str = None,
        general_errors: str = None,
        general_suggestions: str = None,
        overall_score: float = None,
        # Pronunciation
        pronunciation_score: float = None,
        pronunciation_summary: str = None,
        pronunciation_errors: str = None,
        pronunciation_suggestions: str = None,
        # Fluency
        fluency_score: float = None,
        fluency_summary: str = None,
        fluency_errors: str = None,
        fluency_suggestions: str = None,
        # Grammar
        grammar_score: float = None,
        grammar_summary: str = None,
        grammar_errors: str = None,
        grammar_suggestions: str = None,
        # Expressions
        expressions_score: float = None,
        expressions_summary: str = None,
        expressions_errors: str = None,
        expressions_suggestions: str = None,
        # Vocabulary
        vocabulary_score: float = None,
        vocabulary_summary: str = None,
        vocabulary_errors: str = None,
        vocabulary_suggestions: str = None,
        # Comprehension
        comprehension_score: float = None,
        comprehension_summary: str = None,
        comprehension_errors: str = None,
        comprehension_suggestions: str = None,
        # Metadata
        generated_by: str = "realtime_agent"
    ) -> Feedback:
        """Create a comprehensive feedback record for a session"""
        feedback = Feedback(
            session_id=session_id,
            # General feedback
            general_feedback=general_feedback,
            general_summary=general_summary,
            general_errors=general_errors,
            general_suggestions=general_suggestions,
            overall_score=overall_score,
            # Pronunciation
            pronunciation_score=pronunciation_score,
            pronunciation_summary=pronunciation_summary,
            pronunciation_errors=pronunciation_errors,
            pronunciation_suggestions=pronunciation_suggestions,
            # Fluency
            fluency_score=fluency_score,
            fluency_summary=fluency_summary,
            fluency_errors=fluency_errors,
            fluency_suggestions=fluency_suggestions,
            # Grammar
            grammar_score=grammar_score,
            grammar_summary=grammar_summary,
            grammar_errors=grammar_errors,
            grammar_suggestions=grammar_suggestions,
            # Expressions
            expressions_score=expressions_score,
            expressions_summary=expressions_summary,
            expressions_errors=expressions_errors,
            expressions_suggestions=expressions_suggestions,
            # Vocabulary
            vocabulary_score=vocabulary_score,
            vocabulary_summary=vocabulary_summary,
            vocabulary_errors=vocabulary_errors,
            vocabulary_suggestions=vocabulary_suggestions,
            # Comprehension
            comprehension_score=comprehension_score,
            comprehension_summary=comprehension_summary,
            comprehension_errors=comprehension_errors,
            comprehension_suggestions=comprehension_suggestions,
            # Metadata
            generated_by=generated_by
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        logger.info(f"✅ Created comprehensive feedback for session {session_id}")
        return feedback
    
    @staticmethod
    def get_user_feedback_history(
        db: Session,
        user_id: str,
        limit: int = 100
    ) -> List[Feedback]:
        """Get feedback history for a user"""
        query = (
            db.query(Feedback)
            .join(SessionModel)
            .filter(SessionModel.user_id == user_id)
        )
        
        return (
            query.order_by(desc(Feedback.created_at))
            .limit(limit)
            .all()
        )


class HomeworkCRUD:
    """CRUD operations for HomeworkItem model"""
    
    @staticmethod
    def create_homework_items(
        db: Session,
        session_id: int,
        homework_data: Dict[str, List[Dict]]
    ) -> List[HomeworkItem]:
        """Create homework items from StandardAgent output"""
        homework_items = []
        
        try:
            for category, items in homework_data.items():
                for item_data in items:
                    homework_item = HomeworkItem(
                        session_id=session_id,
                        category=category,
                        title=item_data.get("title", ""),
                        description=item_data.get("description", ""),
                        difficulty=item_data.get("difficulty", "intermediate"),
                        priority=item_data.get("priority", "medium"),
                        estimated_time_minutes=item_data.get("estimated_time_minutes")
                    )
                    db.add(homework_item)
                    homework_items.append(homework_item)
            
            db.commit()
            logger.info(f"✅ Created {len(homework_items)} homework items")
            return homework_items
            
        except Exception as e:
            logger.error(f"❌ Error creating homework items: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_pending_homework(
        db: Session,
        user_id: str,
        category: Optional[str] = None
    ) -> List[HomeworkItem]:
        """Get pending homework for a user"""
        query = (
            db.query(HomeworkItem)
            .join(SessionModel)
            .filter(
                and_(
                    SessionModel.user_id == user_id,
                    HomeworkItem.status == "pending"
                )
            )
        )
        
        if category:
            query = query.filter(HomeworkItem.category == category)
        
        return query.order_by(desc(HomeworkItem.created_at)).all()


# Utility functions
def get_session_summary(db: Session, session_id: str) -> Optional[Dict[str, Any]]:
    """Get complete session summary with transcripts and feedback"""
    session = SessionCRUD.get_session_by_id(db, session_id)
    if not session:
        return None
    
    transcripts = TranscriptCRUD.get_session_transcripts(db, session.id)
    feedback_items = FeedbackCRUD.get_session_feedback(db, session.id)
    
    return {
        "session": session,
        "transcripts": transcripts,
        "feedback": feedback_items,
        "transcript_count": len(transcripts),
        "feedback_count": len(feedback_items)
    }
