"""
CRUD operations for Talktor database models
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .models import Session as SessionModel, Transcript, Feedback, HomeworkItem, VocabularyItem
from .models import AgentType, ConversationMode, Speaker, FeedbackPillar
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
    def create_feedback_item(
        db: Session,
        session_id: int,
        pillar: FeedbackPillar,
        score: float,
        feedback_text: str,
        examples: Optional[Dict] = None,
        suggestions: Optional[Dict] = None,
        errors: Optional[Dict] = None,
        generated_by: str = "standard_agent"
    ) -> Feedback:
        """Create a feedback item for a specific pillar"""
        try:
            feedback = Feedback(
                session_id=session_id,
                pillar=pillar,
                score=score,
                feedback_text=feedback_text,
                examples=examples,
                suggestions=suggestions,
                errors=errors,
                generated_by=generated_by
            )
            db.add(feedback)
            db.commit()
            db.refresh(feedback)
            logger.info(f"✅ Created feedback: {pillar} - Score: {score}")
            return feedback
        except Exception as e:
            logger.error(f"❌ Error creating feedback: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def create_session_feedback(
        db: Session,
        session_id: int,
        feedback_data: Dict[str, Any]
    ) -> List[Feedback]:
        """Create feedback for all pillars from StandardAgent output"""
        feedback_items = []
        
        try:
            # Assuming feedback_data has structure like:
            # {"pillars": {"pronunciation": {"score": 7, "feedback": "..."}, ...}}
            pillars_data = feedback_data.get("pillars", {})
            
            for pillar_name, pillar_data in pillars_data.items():
                try:
                    pillar_enum = FeedbackPillar(pillar_name.lower())
                    feedback_item = FeedbackCRUD.create_feedback_item(
                        db=db,
                        session_id=session_id,
                        pillar=pillar_enum,
                        score=pillar_data.get("score", 0),
                        feedback_text=pillar_data.get("feedback", ""),
                        examples=pillar_data.get("examples"),
                        suggestions=pillar_data.get("suggestions"),
                        errors=pillar_data.get("errors")
                    )
                    feedback_items.append(feedback_item)
                except ValueError:
                    logger.warning(f"⚠️ Unknown pillar: {pillar_name}")
                    continue
            
            logger.info(f"✅ Created {len(feedback_items)} feedback items for session {session_id}")
            return feedback_items
            
        except Exception as e:
            logger.error(f"❌ Error creating session feedback: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_session_feedback(
        db: Session,
        session_id: int
    ) -> List[Feedback]:
        """Get all feedback for a session"""
        return db.query(Feedback).filter(Feedback.session_id == session_id).all()
    
    @staticmethod
    def get_user_feedback_history(
        db: Session,
        user_id: str,
        pillar: Optional[FeedbackPillar] = None,
        limit: int = 100
    ) -> List[Feedback]:
        """Get feedback history for a user, optionally filtered by pillar"""
        query = (
            db.query(Feedback)
            .join(SessionModel)
            .filter(SessionModel.user_id == user_id)
        )
        
        if pillar:
            query = query.filter(Feedback.pillar == pillar)
        
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
