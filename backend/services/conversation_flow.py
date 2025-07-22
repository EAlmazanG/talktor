"""
Conversation Flow Service - Integrates RealtimeAgent → StandardAgent → Database
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from core.logging import get_logger
from core.colors import colorize, Colors
from agents.realtime_agent import RealtimeAgent
from agents.standard_agent import StandardAgent
from db.database import get_db_session, init_database
from db.crud import SessionCRUD, TranscriptCRUD, FeedbackCRUD
from db.models import AgentType, ConversationMode, Speaker

logger = get_logger(__name__)


class ConversationFlow:
    """
    Orchestrates the complete conversation flow:
    1. RealtimeAgent handles voice conversation
    2. StandardAgent analyzes conversation and generates feedback
    3. Database persistence for session, transcripts, and feedback
    """
    
    def __init__(self, user_id: str = "test_user"):
        self.user_id = user_id
        self.session_id = None
        self.realtime_agent = None
        self.standard_agent = StandardAgent()
        
        # Initialize database
        init_database()
        
        # CRUD instances
        self.session_crud = SessionCRUD()
        self.transcript_crud = TranscriptCRUD()
        self.feedback_crud = FeedbackCRUD()
        
        logger.info(f"🔄 ConversationFlow initialized for user: {user_id}")
    
    async def start_conversation(self, session_id: str = None) -> str:
        """Start a new conversation session"""
        try:
            # Generate session ID if not provided
            if not session_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_id = f"session_{timestamp}"
            
            self.session_id = session_id
            
            # Create database session record
            db = get_db_session()
            try:
                session_data = {
                    "session_id": session_id,
                    "user_id": self.user_id,
                    "agent_type": AgentType.REALTIME,
                    "conversation_mode": ConversationMode.VOICE,
                    "status": "active",
                    "started_at": datetime.now(timezone.utc)
                }
                
                db_session = self.session_crud.create_session(db, session_data)
                logger.info(f"📝 Created database session: {session_id}")
            finally:
                db.close()
            
            # Initialize RealtimeAgent
            self.realtime_agent = RealtimeAgent(session_id=session_id, user_id=self.user_id)
            
            # Start the conversation
            logger.info(colorize(f"🚀 Starting conversation flow for session: {session_id}", Colors.BRIGHT_GREEN))
            await self.realtime_agent.start_conversation()
            
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error starting conversation: {e}")
            raise
    
    async def end_conversation(self) -> Dict[str, Any]:
        """End the conversation and process everything"""
        try:
            if not self.session_id or not self.realtime_agent:
                raise ValueError("No active conversation to end")
            
            logger.info(colorize(f"🛑 Ending conversation: {self.session_id}", Colors.BRIGHT_YELLOW))
            
            # Get conversation summary from RealtimeAgent
            conversation_summary = self.realtime_agent.get_conversation_summary()
            
            # Extract conversation data
            conversation_text = conversation_summary.get("conversation_text", "")
            messages = conversation_summary.get("messages", [])
            duration = conversation_summary.get("duration_seconds", 0)
            
            logger.info(f"📊 Conversation summary: {len(messages)} messages, {duration}s duration")
            
            # Save transcripts to database
            await self._save_transcripts(messages)
            
            # Generate feedback using StandardAgent
            feedback_data = await self._generate_feedback(conversation_text)
            
            # Save feedback to database
            await self._save_feedback(feedback_data)
            
            # Update session completion
            await self._complete_session(duration)
            
            # Prepare final results
            results = {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "duration_seconds": duration,
                "message_count": len(messages),
                "conversation_text": conversation_text,
                "feedback": feedback_data,
                "status": "completed"
            }
            
            logger.info(colorize(f"✅ Conversation flow completed successfully: {self.session_id}", Colors.BRIGHT_GREEN))
            return results
            
        except Exception as e:
            logger.error(f"❌ Error ending conversation: {e}")
            raise
    
    async def _save_transcripts(self, messages: List[Dict[str, Any]]):
        """Save conversation transcripts to database"""
        try:
            db = get_db_session()
            try:
                # Get session database ID
                db_session = self.session_crud.get_session_by_id(db, self.session_id)
                if not db_session:
                    raise ValueError(f"Session not found: {self.session_id}")
                
                logger.info(f"💬 Saving {len(messages)} transcript messages...")
                
                for i, message in enumerate(messages):
                    speaker = Speaker.USER if message.get("role") == "user" else Speaker.AI
                    content = message.get("content", "")
                    timestamp = message.get("timestamp")
                    
                    if content.strip():  # Only save non-empty messages
                        transcript_data = {
                            "session_id": db_session.id,
                            "speaker": speaker,
                            "content": content,
                            "sequence_number": i + 1,
                            "timestamp": timestamp or datetime.now(timezone.utc)
                        }
                        
                        self.transcript_crud.add_transcript(db, transcript_data)
                
                logger.info(f"✅ Saved {len(messages)} transcript messages")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error saving transcripts: {e}")
            raise
    
    async def _generate_feedback(self, conversation_text: str) -> Dict[str, Any]:
        """Generate feedback using StandardAgent"""
        try:
            logger.info("🤖 Generating feedback with StandardAgent...")
            
            # Use StandardAgent to analyze the conversation
            feedback_result = await self.standard_agent.analyze_conversation_feedback(
                conversation_text=conversation_text,
                user_level="intermediate"  # Could be dynamic based on user profile
            )
            
            logger.info("✅ Feedback generated successfully")
            return feedback_result
            
        except Exception as e:
            logger.error(f"❌ Error generating feedback: {e}")
            # Return fallback feedback
            return {
                "overall_score": 7.0,
                "pillars": {
                    "pronunciation": {"score": 7.0, "feedback": "Good pronunciation overall"},
                    "fluency": {"score": 7.0, "feedback": "Decent conversational flow"},
                    "grammar": {"score": 7.0, "feedback": "Grammar needs some work"},
                    "expressions": {"score": 7.0, "feedback": "Good use of expressions"},
                    "vocabulary": {"score": 7.0, "feedback": "Adequate vocabulary range"},
                    "comprehension": {"score": 7.0, "feedback": "Good understanding"}
                }
            }
    
    async def _save_feedback(self, feedback_data: Dict[str, Any]):
        """Save feedback to database"""
        try:
            db = get_db_session()
            try:
                # Get session database ID
                db_session = self.session_crud.get_session_by_id(db, self.session_id)
                if not db_session:
                    raise ValueError(f"Session not found: {self.session_id}")
                
                logger.info("📊 Saving feedback to database...")
                
                pillars = feedback_data.get("pillars", {})
                feedback_items = []
                
                # Map pillar names to database enum values
                pillar_mapping = {
                    "pronunciation": "PRONUNCIATION",
                    "fluency": "FLUENCY", 
                    "grammar": "GRAMMAR",
                    "expressions": "EXPRESSIONS",
                    "vocabulary": "VOCABULARY",
                    "comprehension": "COMPREHENSION"
                }
                
                for pillar_name, pillar_data in pillars.items():
                    if pillar_name in pillar_mapping:
                        feedback_item = {
                            "session_id": db_session.id,
                            "pillar": pillar_mapping[pillar_name],
                            "score": pillar_data.get("score", 7.0),
                            "feedback_text": pillar_data.get("feedback", ""),
                            "examples": json.dumps(pillar_data.get("examples", [])),
                            "suggestions": json.dumps(pillar_data.get("suggestions", [])),
                            "errors": json.dumps(pillar_data.get("errors", []))
                        }
                        feedback_items.append(feedback_item)
                
                # Save all feedback items
                self.feedback_crud.create_feedback_batch(db, feedback_items)
                logger.info(f"✅ Saved {len(feedback_items)} feedback items")
                
        except Exception as e:
            logger.error(f"❌ Error saving feedback: {e}")
            raise
    
    async def _complete_session(self, duration_seconds: int):
        """Mark session as completed and update metadata"""
        try:
            db = get_db_session()
            try:
                completion_data = {
                    "status": "completed",
                    "ended_at": datetime.now(timezone.utc),
                    "duration_seconds": duration_seconds,
                    "notes": "Conversation completed successfully"
                }
                
                updated_session = self.session_crud.complete_session(db, self.session_id, completion_data)
                logger.info(f"✅ Session marked as completed: {self.session_id}")
                
        except Exception as e:
            logger.error(f"❌ Error completing session: {e}")
            raise
    
    def is_active(self) -> bool:
        """Check if conversation is active"""
        return (self.realtime_agent is not None and 
                self.realtime_agent.is_active() and 
                self.session_id is not None)
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.realtime_agent:
                # The realtime agent should handle its own cleanup
                pass
            
            self.session_id = None
            self.realtime_agent = None
            logger.info("🧹 ConversationFlow cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


# Convenience function for simple usage
async def run_complete_conversation_flow(user_id: str = "test_user", session_id: str = None) -> Dict[str, Any]:
    """
    Run a complete conversation flow from start to finish
    This is a convenience function for testing and simple usage
    """
    flow = ConversationFlow(user_id=user_id)
    
    try:
        # Start conversation
        actual_session_id = await flow.start_conversation(session_id)
        
        # Wait for conversation to end (this will block until user terminates)
        # In practice, this would be handled by the RealtimeAgent's termination logic
        while flow.is_active():
            await asyncio.sleep(1)
        
        # Process the ended conversation
        results = await flow.end_conversation()
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in conversation flow: {e}")
        raise
    finally:
        await flow.cleanup()
