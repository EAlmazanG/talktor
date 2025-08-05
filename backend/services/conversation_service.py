"""
Conversation service for handling conversation logic and function calls
"""
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from .session_state import SessionState
from core.colors import colorize, Colors
from core.logging import get_logger

logger = get_logger(__name__)


class ConversationService:
    """Service for managing conversation logic and processing"""
    
    def __init__(self):
        pass
    
    def process_english_conversation(self, message: str, session_state: SessionState) -> str:
        """
        Process English conversation message
        
        For now, this is a simple echo to maintain POC functionality.
        In the future, this will be expanded to include:
        - Conversation analysis
        - Error detection
        - Learning progress tracking
        - Personalized responses
        """
        logger.info(f"Processing conversation message for session {session_state.session_id}: {message[:50]}...")
        
        # Simple response for now - this maintains POC behavior
        response = {
            "status": "conversation_continuing",
            "message": f"Received: {message}",
            "session_id": session_state.session_id,
            "timestamp": session_state.started_at.isoformat()
        }
        
        return json.dumps(response)
    
    async def handle_function_call(
        self, 
        event_data: Dict[str, Any], 
        session_state: SessionState
    ) -> tuple[str, str]:
        """
        Handle function call from OpenAI
        
        Returns:
            tuple: (result, call_id)
        """
        try:
            name = event_data.get("name", "")
            call_id = event_data.get("call_id", "")
            arguments = event_data.get("arguments", "{}")
            
            logger.debug(f"Handling function call '{name}' for session {session_state.session_id}")
            
            # Parse function arguments
            function_call_args = json.loads(arguments)
            
            if name == "continue_conversation":
                message = function_call_args.get("message", "")
                result = self.process_english_conversation(message, session_state)
                return result, call_id
            elif name == "end_conversation":
                logger.info("🔄 Agent requested to end the conversation")
                # Trigger conversation termination in the RealtimeAgent
                result = json.dumps({
                    "status": "success",
                    "message": "Ending conversation..."
                })
                
                # Schedule the conversation termination to happen after we return
                if hasattr(session_state, "agent") and session_state.agent:
                    asyncio.create_task(session_state.agent._handle_conversation_termination())
                
                return result, call_id
            elif name == "enviar_feedback_conversacion":
                logger.info(colorize("📝 Agent requested to send conversation feedback", Colors.BRIGHT_GREEN))
                # Get the feedback data from the function call
                resumen = function_call_args.get("resumen_conversacion", "")
                feedback = function_call_args.get("feedback_tutor", "")
                
                # Log the complete function call arguments for debugging
                logger.info(f"📥 Received function call arguments: {json.dumps(function_call_args, indent=2)[:500]}...")
                
                # Log the received feedback data for debugging
                logger.info(f"📋 Received feedback summary ({len(resumen)} chars): {resumen[:100]}...")
                logger.info(f"💬 Received feedback content ({len(feedback)} chars): {feedback[:100]}...")
                
                # Validate feedback data
                if not resumen or len(resumen) < 10:
                    logger.warning(colorize("⚠️ Received empty or very short conversation summary", Colors.BRIGHT_YELLOW))
                if not feedback or len(feedback) < 10:
                    logger.warning(colorize("⚠️ Received empty or very short feedback content", Colors.BRIGHT_YELLOW))
                
                # Store the feedback in the session state for later use
                if hasattr(session_state, "agent") and session_state.agent:
                    # Store the feedback in the agent for later retrieval
                    try:
                        session_state.agent.conversation_feedback = {
                            "resumen": resumen,
                            "feedback": feedback,
                            "timestamp": datetime.now().isoformat()
                        }
                        logger.info(colorize("✅ Successfully stored conversation feedback in agent", Colors.BRIGHT_GREEN))
                        logger.info(f"📊 Feedback summary length: {len(resumen)} chars")
                        logger.info(f"📊 Feedback content length: {len(feedback)} chars")
                    except Exception as store_error:
                        logger.error(colorize(f"❌ Error storing feedback in agent: {str(store_error)}", Colors.BRIGHT_RED))
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    logger.error(colorize("❌ Could not store feedback - agent not available in session state", Colors.BRIGHT_RED))
                
                result = json.dumps({
                    "status": "success",
                    "message": "Feedback received and stored"
                })
                
                return result, call_id
            else:
                logger.warning(f"Unknown function call: {name}")
                error_result = json.dumps({
                    "status": "error",
                    "message": f"Unknown function: {name}"
                })
                return error_result, call_id
                
        except Exception as e:
            logger.error(f"Error parsing function call arguments: {e}")
            error_result = json.dumps({
                "status": "error",
                "message": f"Error processing function call: {str(e)}"
            })
            return error_result, event_data.get("call_id", "")
    
    def update_conversation_context(self, session_state: SessionState, speaker: str, text: str):
        """
        Update conversation context for the session using structured messages
        
        Args:
            session_state: Current session state
            speaker: "user" or "ai" 
            text: Transcript text to add
        """
        from datetime import datetime
        
        # Convert speaker format to role format
        role = "user" if speaker == "user" else "assistant"
        
        # Add as structured message with timestamp
        session_state.add_message(role, text, datetime.now())
        
        logger.debug(f"Added {speaker} message to session {session_state.session_id}: '{text[:50]}...'")
    
    def get_conversation_summary(self, session_state: SessionState) -> Dict[str, Any]:
        """
        Get a summary of the current conversation with full transcript data
        
        Returns data in the format expected by ConversationFlow:
        - messages: List of conversation messages
        - conversation_text: Full conversation text
        - duration_seconds: Session duration
        - Other metadata
        """
        from datetime import datetime, timezone
        
        # Get structured messages from session state
        messages = session_state.get_messages()
        
        # Convert messages to the format expected by ConversationFlow
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "order": msg["order"],
                "confidence_score": 0.9,  # Default confidence
                "audio_duration": None
            })
        
        # Create conversation text from structured messages
        conversation_text = ""
        for msg in messages:
            speaker = "USER" if msg["role"] == "user" else "AI"
            conversation_text += f"{speaker}: {msg['content']}\n"
        
        return {
            "session_id": session_state.session_id,
            "messages": formatted_messages,
            "conversation_text": conversation_text.strip(),
            "duration_seconds": session_state.get_session_duration(),
            "message_count": len(messages),
            "user_transcript_length": len(session_state.user_transcript),
            "ai_transcript_length": len(session_state.ai_transcript),
            "is_active": session_state.is_active,
            "mode": session_state.mode,
            "topic": session_state.topic,
            "status": "completed" if not session_state.is_active else "active",
            "conversation_json": session_state.get_conversation_json()
        }
