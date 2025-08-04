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
# Import RealtimeAgent lazily to avoid circular imports
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
            
            # Initialize RealtimeAgent (lazy import to avoid circular imports)
            from agents.realtime_agent import RealtimeAgent
            self.realtime_agent = RealtimeAgent(session_id=session_id, user_id=self.user_id)
            
            # Start the conversation
            logger.info(colorize(f"🚀 Starting conversation flow for session: {session_id}", Colors.BRIGHT_GREEN))
            await self.realtime_agent.start()
            
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
        """Extract feedback from the conversation JSON (generated by RealtimeAgent)"""
        try:
            logger.info("🤖 Extracting feedback from conversation...")
            
            # Get the conversation JSON which contains the AI-generated feedback
            conversation_json = conversation_summary.get("conversation_json", {})
            messages = conversation_json.get("messages", [])
            
            # Look for feedback message (should be the last assistant message with feedback_type)
            feedback_data = None
            for message in reversed(messages):
                if message.get("role") == "assistant":
                    content = message.get("content", "")
                    # Try to parse as JSON to see if it's feedback
                    try:
                        import json
                        parsed_content = json.loads(content)
                        if parsed_content.get("feedback_type") == "conversation_analysis":
                            feedback_data = parsed_content
                            logger.info("✅ Found AI-generated feedback in conversation")
                            break
                    except (json.JSONDecodeError, AttributeError):
                        continue
            
            if feedback_data:
                # Return the feedback in the new format
                logger.info("✅ Found real AI-generated feedback from RealtimeAgent")
                return {
                    "overall_score": feedback_data.get("overall_score"),
                    "general": feedback_data.get("general", {}),
                    "pillars": feedback_data.get("pillars", {}),
                    "source": "realtime_agent",
                    "generated_at": datetime.now().isoformat()
                }
            else:
                logger.warning("⚠️ No AI feedback found in conversation - feedback will be empty")
                return None  # Return None instead of fallback
            
        except Exception as e:
            logger.error(f"❌ Error extracting feedback: {e}")
            return None  # Return None instead of fallback on error
    

    
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
