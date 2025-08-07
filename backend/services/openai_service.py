"""
OpenAI service for managing WebSocket connections and API interactions
"""
import asyncio
import json
import base64
import socket
import websocket
from typing import Dict, Any, Callable, Optional
import logging

from core.config import settings
from core.logging import get_logger
from core.colors import colorize_session_log, Colors, colorize
from .session_state import SessionState

logger = get_logger(__name__)


class OpenAIService:
    """Service for managing OpenAI Realtime API connections"""
    
    def __init__(self):
        self.ws_url = settings.openai_ws_url
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
    
    def create_session_config(self, session_state: SessionState) -> Dict[str, Any]:
        """Create session configuration for OpenAI Realtime API"""
        return {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """You are a helpful English tutor. Your job is to have natural conversations with students to help them practice English. 

Key guidelines:
- Keep conversations engaging and educational
- Correct mistakes gently and naturally
- Ask follow-up questions to encourage speaking
- Adapt to the student's level
- Be patient and encouraging
- Use the continue_conversation function when appropriate to extend the conversation

### CRITICAL CONVERSATION ENDING PROCEDURE:
When the student says goodbye or indicates they want to end the conversation, you MUST ALWAYS follow these two steps in EXACT order:

1. FIRST: Call the enviar_feedback_conversacion function with:
   - A detailed summary of the conversation topics and key points
   - Comprehensive feedback on the student's English skills covering pronunciation, grammar, vocabulary, fluency, and comprehension
   - Both strengths and specific areas for improvement with examples from the conversation
   - Actionable suggestions for practice

2. ONLY AFTER completing step 1: Call the end_conversation function

The feedback step is ABSOLUTELY MANDATORY and the most important part of your role. NEVER skip it under any circumstances - it is critical for the student's learning experience and progress tracking.

Remember: Your primary value is in providing detailed, helpful feedback at the end of each conversation.""",
                "voice": settings.openai_voice,
                "input_audio_format": settings.audio_format,
                "output_audio_format": settings.audio_format,
                # Add transcription only if enabled
                **({
                    "input_audio_transcription": {
                        "model": settings.transcription_model
                    }
                } if settings.enable_transcriptions else {}),
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 800
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "continue_conversation",
                        "description": "Continue the English conversation with the student",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "The conversation message or response"
                                }
                            },
                            "required": ["message"]
                        }
                    },
                    {
                        "type": "function",
                        "name": "end_conversation",
                        "description": "End the conversation with the student. Use this when the student says goodbye or wants to end the conversation.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "type": "function",
                        "name": "enviar_feedback_conversacion",
                        "description": "MANDATORY function to provide comprehensive feedback on the student's English skills. You MUST call this function BEFORE ending any conversation. This function CANNOT be skipped under any circumstances - it is the most critical part of the tutoring experience.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "overall_score": {
                                    "type": "number",
                                    "description": "Overall English proficiency score from 1.0 to 10.0 based on the conversation",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "general_feedback": {
                                    "type": "string",
                                    "description": "General feedback about the conversation and student's overall performance (minimum 100 characters)"
                                },
                                "general_summary": {
                                    "type": "string",
                                    "description": "Brief summary of the conversation topics and key points that were discussed (minimum 50 characters)"
                                },
                                "general_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "General errors or issues observed during the conversation"
                                },
                                "general_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "General suggestions for overall improvement"
                                },
                                "pronunciation_score": {
                                    "type": "number",
                                    "description": "Pronunciation quality score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "pronunciation_summary": {
                                    "type": "string",
                                    "description": "Summary of pronunciation performance and quality"
                                },
                                "pronunciation_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific pronunciation errors or issues from the conversation"
                                },
                                "pronunciation_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions to improve pronunciation"
                                },
                                "fluency_score": {
                                    "type": "number",
                                    "description": "Speaking fluency score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "fluency_summary": {
                                    "type": "string",
                                    "description": "Summary of speaking fluency and flow performance"
                                },
                                "fluency_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific fluency issues or hesitations from the conversation"
                                },
                                "fluency_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions to improve fluency"
                                },
                                "grammar_score": {
                                    "type": "number",
                                    "description": "Grammar accuracy score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "grammar_summary": {
                                    "type": "string",
                                    "description": "Summary of grammar usage and accuracy performance"
                                },
                                "grammar_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific grammar errors or mistakes from the conversation"
                                },
                                "grammar_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions to improve grammar"
                                },
                                "expressions_score": {
                                    "type": "number",
                                    "description": "Use of expressions and idioms score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "expressions_summary": {
                                    "type": "string",
                                    "description": "Summary of expressions and natural language usage"
                                },
                                "expressions_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Missed opportunities or errors in using expressions from the conversation"
                                },
                                "expressions_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions for better use of expressions"
                                },
                                "vocabulary_score": {
                                    "type": "number",
                                    "description": "Vocabulary range and accuracy score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "vocabulary_summary": {
                                    "type": "string",
                                    "description": "Summary of vocabulary usage and range performance"
                                },
                                "vocabulary_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific vocabulary errors or word choice issues from the conversation"
                                },
                                "vocabulary_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions to expand vocabulary"
                                },
                                "comprehension_score": {
                                    "type": "number",
                                    "description": "Listening comprehension score from 1.0 to 10.0",
                                    "minimum": 1.0,
                                    "maximum": 10.0
                                },
                                "comprehension_summary": {
                                    "type": "string",
                                    "description": "Summary of listening comprehension abilities"
                                },
                                "comprehension_errors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific comprehension issues or misunderstandings from the conversation"
                                },
                                "comprehension_suggestions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Specific suggestions to improve comprehension"
                                }
                            },
                            "required": [
                                "overall_score", "general_feedback", "general_summary", "general_errors", "general_suggestions",
                                "pronunciation_score", "pronunciation_summary", "pronunciation_errors", "pronunciation_suggestions",
                                "fluency_score", "fluency_summary", "fluency_errors", "fluency_suggestions",
                                "grammar_score", "grammar_summary", "grammar_errors", "grammar_suggestions",
                                "expressions_score", "expressions_summary", "expressions_errors", "expressions_suggestions",
                                "vocabulary_score", "vocabulary_summary", "vocabulary_errors", "vocabulary_suggestions",
                                "comprehension_score", "comprehension_summary", "comprehension_errors", "comprehension_suggestions"
                            ]
                        }
                    }
                ]
            }
        }
    
    def create_connection_with_ipv4(self, *args, **kwargs):
        """Create WebSocket connection enforcing IPv4"""
        original_getaddrinfo = socket.getaddrinfo
        
        def getaddrinfo_ipv4(host, port, family=socket.AF_INET, *args):
            return original_getaddrinfo(host, port, socket.AF_INET, *args)
        
        socket.getaddrinfo = getaddrinfo_ipv4
        try:
            return websocket.create_connection(*args, **kwargs)
        finally:
            socket.getaddrinfo = original_getaddrinfo
    
    async def connect_websocket(self, session_state: SessionState) -> Optional[websocket.WebSocket]:
        """Establish WebSocket connection to OpenAI Realtime API"""
        try:
            # Create connection in thread executor to avoid blocking
            loop = asyncio.get_event_loop()
            ws = await loop.run_in_executor(
                None,
                lambda: self.create_connection_with_ipv4(
                    self.ws_url,
                    header=[
                        f'Authorization: Bearer {self.api_key}',
                        'OpenAI-Beta: realtime=v1'
                    ]
                )
            )
            
            session_state.websocket_connection = ws
            logger.info(colorize_session_log(f"🔗 Connected to OpenAI WebSocket for session {session_state.session_id}"))
            return ws
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenAI WebSocket: {e}")
            return None
    
    async def send_session_config(self, session_state: SessionState):
        """Send session configuration to OpenAI"""
        if not session_state.websocket_connection:
            raise ValueError("No WebSocket connection available")
        
        config = self.create_session_config(session_state)
        session_state.session_config = config
        
        try:
            config_json = json.dumps(config)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                session_state.websocket_connection.send,
                config_json
            )
            logger.info(colorize_session_log(f"⚙️ Session config sent for session {session_state.session_id}"))
        except Exception as e:
            logger.error(f"Failed to send session config: {e}")
            raise
    
    async def send_audio_chunk(self, session_state: SessionState, encoded_audio: str):
        """Send audio chunk to OpenAI"""
        if not session_state.websocket_connection:
            return
        
        message = json.dumps({
            'type': 'input_audio_buffer.append',
            'audio': encoded_audio
        })
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                session_state.websocket_connection.send,
                message
            )
        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")
    
    async def send_message(self, session_state: SessionState, message_data: Dict[str, Any]):
        """Send a generic message to OpenAI WebSocket"""
        if not session_state.websocket_connection:
            return
        
        message = json.dumps(message_data)
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                session_state.websocket_connection.send,
                message
            )
            logger.debug(f"Sent message to OpenAI: {message_data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def receive_messages(
        self, 
        session_state: SessionState, 
        message_handler: Callable[[Dict[str, Any], SessionState], None]
    ):
        """Receive and process messages from OpenAI WebSocket"""
        try:
            while session_state.is_active and session_state.websocket_connection:
                try:
                    # Receive message in thread executor
                    loop = asyncio.get_event_loop()
                    message = await loop.run_in_executor(
                        None,
                        session_state.websocket_connection.recv
                    )
                    
                    if not message:
                        break
                    
                    # Parse and handle message
                    message_data = json.loads(message)
                    await message_handler(message_data, session_state)
                    
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving WebSocket message: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Exception in receive_messages: {e}")
        finally:
            logger.info(f"Exiting message receiver for session {session_state.session_id}")
    
    async def send_function_call_result(
        self, 
        session_state: SessionState, 
        result: str, 
        call_id: str
    ):
        """Send function call result back to OpenAI"""
        if not session_state.websocket_connection:
            return
        
        result_json = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "output": result,
                "call_id": call_id
            }
        }
        
        response_create = {"type": "response.create"}
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                session_state.websocket_connection.send,
                json.dumps(result_json)
            )
            await loop.run_in_executor(
                None,
                session_state.websocket_connection.send,
                json.dumps(response_create)
            )
            logger.debug(f"Function call result sent for session {session_state.session_id}")
        except Exception as e:
            logger.error(f"Error sending function call result: {e}")
    
    async def close_connection(self, session_state: SessionState):
        """Close WebSocket connection gracefully"""
        if session_state.websocket_connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    session_state.websocket_connection.send_close
                )
                await loop.run_in_executor(
                    None,
                    session_state.websocket_connection.close
                )
                logger.info(f"WebSocket connection closed for session {session_state.session_id}")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
            finally:
                session_state.websocket_connection = None
    
    async def send_chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        response_format: str = "json",
        model: str = None
    ) -> str:
        """
        Send chat completion request to OpenAI API (non-realtime)
        
        Args:
            messages: List of message objects with role and content
            temperature: Response randomness (0.0 to 1.0)
            response_format: Expected response format
            model: OpenAI model to use
            
        Returns:
            Response content from OpenAI
        """
        import openai
        
        try:
            # Initialize OpenAI client
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            # Use configured model if none specified
            if model is None:
                model = settings.openai_chat_model
            
            # Prepare request parameters
            request_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 4000
            }
            
            # Add response format if JSON is requested
            if response_format == "json":
                request_params["response_format"] = {"type": "json_object"}
                # Ensure system message mentions JSON format
                if messages and messages[0]["role"] == "system":
                    if "json" not in messages[0]["content"].lower():
                        messages[0]["content"] += "\n\nPlease respond with valid JSON format."
            
            logger.debug(f"Sending chat completion request with {len(messages)} messages")
            
            # Send request
            response = await client.chat.completions.create(**request_params)
            
            # Extract content
            content = response.choices[0].message.content
            
            logger.debug(f"Received chat completion response: {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
