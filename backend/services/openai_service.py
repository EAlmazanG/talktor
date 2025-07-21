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

Remember: You're helping someone learn English through conversation practice.""",
                "voice": "alloy",
                "input_audio_format": settings.audio_format,
                "output_audio_format": settings.audio_format,
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
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
