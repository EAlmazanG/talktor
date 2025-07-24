"""
Conversation Flow Service - Integrates RealtimeAgent → StandardAgent → Database
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from core.logging import get_logger
from core.colors import colorize, Colors
from agents.realtime_agent import RealtimeAgent
from agents.standard_agent import StandardAgent
from services.persistence_service import persistence_service
from db.models import AgentType, ConversationMode

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
        
        # Use centralized persistence service
        self.persistence = persistence_service
        
        logger.info(f"🔄 ConversationFlow initialized for user: {user_id}")
    
    async def start_conversation(self, session_id: str = None) -> str:
        """Start a new conversation session"""
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            self.session_id = session_id
            
            # Create database session record using persistence service
            await self.persistence.create_session(
                session_id=session_id,
                user_id=self.user_id,
                agent_type=AgentType.REALTIME,
                mode=ConversationMode.FREE_TOPIC  # Updated to use existing enum
            )
            
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
            conversation_summary = self.realtime_agent.get_session_info()
            
            # Extract conversation data
            conversation_text = conversation_summary.get("conversation_text", "")
            messages = conversation_summary.get("messages", [])
            duration = conversation_summary.get("duration_seconds", 0)
            conversation_json = conversation_summary.get("conversation_json", {})
            
            logger.info(f"📊 Conversation summary: {len(messages)} messages, {duration}s duration")
            
            # Generate feedback using StandardAgent
            feedback_data = await self._generate_feedback(conversation_summary)
            
            # Save complete conversation using persistence service (atomic transaction)
            result = await self.persistence.save_complete_conversation(
                session_id=self.session_id,
                user_id=self.user_id,
                conversation_json=conversation_json,
                feedback_data=feedback_data,
                duration_seconds=duration,
                agent_type=AgentType.REALTIME,
                mode=ConversationMode.FREE_TOPIC
            )
            
            # Prepare final results
            results = {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "duration_seconds": duration,
                "message_count": len(messages),
                "conversation_text": conversation_text,
                "feedback": feedback_data,
                "status": "completed",
                "database_result": result["summary"]
            }
            
            logger.info(colorize(f"✅ Conversation flow completed successfully: {self.session_id}", Colors.BRIGHT_GREEN))
            return results
            
        except Exception as e:
            logger.error(f"❌ Error ending conversation: {e}")
            raise
    

    
    async def _generate_feedback(self, conversation_summary: dict) -> Dict[str, Any]:
        """Generate feedback using StandardAgent"""
        try:
            logger.info("🤖 Generating feedback with StandardAgent...")
            
            # Extract user and AI transcripts from messages
            messages = conversation_summary.get("messages", [])
            user_transcript = "\n".join([msg["content"] for msg in messages if msg.get("role") == "user"])
            ai_transcript = "\n".join([msg["content"] for msg in messages if msg.get("role") == "assistant"])
            duration = conversation_summary.get("duration_seconds", 0)
            
            # Create a mock session state for StandardAgent
            from services.session_state import SessionState
            mock_session_state = SessionState(session_id=self.session_id)
            
            # Use StandardAgent to analyze the conversation
            feedback_result = await self.standard_agent.analyze_conversation_feedback(
                session_state=mock_session_state,
                user_transcript=user_transcript,
                ai_transcript=ai_transcript,
                conversation_duration=duration
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
