"""
Conversation service for handling conversation logic and function calls
"""
import json
import logging
from typing import Dict, Any

from .session_state import SessionState

logger = logging.getLogger(__name__)


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
        Update conversation context for the session
        
        This method will be expanded in the future to:
        - Track conversation flow
        - Maintain context for better responses
        - Analyze conversation patterns
        """
        if speaker == "user":
            session_state.add_user_transcript(text)
        elif speaker == "ai":
            session_state.add_ai_transcript(text)
        
        logger.debug(f"Updated {speaker} transcript for session {session_state.session_id}")
    
    def get_conversation_summary(self, session_state: SessionState) -> Dict[str, Any]:
        """
        Get a summary of the current conversation
        
        Future expansion will include:
        - Conversation analysis
        - Key topics discussed
        - Learning objectives met
        - Areas for improvement
        """
        return {
            "session_id": session_state.session_id,
            "duration_seconds": session_state.get_session_duration(),
            "user_transcript_length": len(session_state.user_transcript),
            "ai_transcript_length": len(session_state.ai_transcript),
            "is_active": session_state.is_active,
            "mode": session_state.mode,
            "topic": session_state.topic
        }
