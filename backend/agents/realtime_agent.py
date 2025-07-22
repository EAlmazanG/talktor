"""
Realtime Agent for managing voice conversations with OpenAI Realtime API
"""
import asyncio
import base64
import json
from typing import Dict, Any, Optional
import logging
from core.logging import get_logger
from core.colors import colorize_audio_log, colorize_session_log, Colors, colorize
from services.session_state import SessionState, session_manager
from services.openai_service import OpenAIService
from services.audio_service import AudioService
from services.conversation_service import ConversationService

logger = get_logger(__name__)


class RealtimeAgent:
    """
    Agent for managing real-time voice conversations
    
    This agent orchestrates all the services needed for a voice conversation:
    - Audio capture and playback
    - WebSocket communication with OpenAI
    - Conversation processing and function calls
    - Session state management
    """
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        
        # Initialize services
        self.openai_service = OpenAIService()
        self.audio_service = AudioService()
        self.conversation_service = ConversationService()
        
        # Session state
        self.session_state: Optional[SessionState] = None
        
        # Audio streams (will be set when starting)
        self.mic_stream = None
        self.speaker_stream = None
        
        # Tasks for concurrent operations
        self.tasks = []
    
    async def start_conversation(self, topic: Optional[str] = None, mode: str = "free_topic"):
        """Start a new conversation session"""
        try:
            # Create session state
            self.session_state = session_manager.create_session(self.session_id, self.user_id)
            self.session_state.topic = topic
            self.session_state.mode = mode
            
            logger.info(colorize_session_log(f"🚀 Starting conversation for session {self.session_id}"))
            
            # Connect to OpenAI WebSocket
            ws = await self.openai_service.connect_websocket(self.session_state)
            if not ws:
                raise Exception("Failed to connect to OpenAI WebSocket")
            
            # Start audio streams
            self.mic_stream, self.speaker_stream = self.audio_service.start_audio_streams(self.session_state)
            
            # Start concurrent tasks
            await self._start_conversation_tasks()
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            await self.stop_conversation()
            raise
    
    async def _start_conversation_tasks(self):
        """Start all concurrent tasks for the conversation"""
        # Task 1: Process microphone audio and send to OpenAI
        mic_task = asyncio.create_task(
            self.audio_service.process_mic_queue(
                self.session_state,
                self._send_audio_to_openai
            )
        )
        
        # Task 2: Receive messages from OpenAI WebSocket
        receive_task = asyncio.create_task(
            self.openai_service.receive_messages(
                self.session_state,
                self._handle_openai_message
            )
        )
        
        self.tasks = [mic_task, receive_task]
        
        # Wait for all tasks to complete or session to end
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in conversation tasks: {e}")
        finally:
            await self._cleanup_tasks()
    
    async def _send_audio_to_openai(self, encoded_audio: str):
        """Send audio chunk to OpenAI (callback for audio service)"""
        await self.openai_service.send_audio_chunk(self.session_state, encoded_audio)
    
    async def _handle_openai_message(self, message: Dict[str, Any], session_state: SessionState):
        """Handle incoming messages from OpenAI WebSocket"""
        event_type = message.get('type', '')
        
        try:
            if event_type == 'session.created':
                await self._handle_session_created()
            
            elif event_type == 'response.audio.delta':
                await self._handle_audio_delta(message)
            
            elif event_type == 'input_audio_buffer.speech_started':
                await self._handle_speech_started(message)
            
            elif event_type == 'conversation.item.input_audio_transcription.delta':
                await self._handle_user_transcription_delta(message)
            
            elif event_type == 'conversation.item.input_audio_transcription.completed':
                await self._handle_user_transcription_completed(message)
            
            elif event_type == 'response.audio_transcript.delta':
                await self._handle_ai_transcription_delta(message)
            
            elif event_type == 'response.audio_transcript.done':
                await self._handle_ai_transcription_completed(message)
            
            elif event_type == 'response.function_call_arguments.done':
                await self._handle_function_call(message)
            
            elif event_type == 'error':
                await self._handle_error(message)
            
            else:
                logger.debug(f"Unhandled event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling OpenAI message: {e}")
    
    async def _handle_session_created(self):
        """Handle session created event"""
        logger.info(colorize_session_log(f"✅ OpenAI session created for {self.session_id}"))
        await self.openai_service.send_session_config(self.session_state)
    
    async def _handle_audio_delta(self, message: Dict[str, Any]):
        """Handle incoming audio data from OpenAI"""
        audio_content = base64.b64decode(message['delta'])
        self.audio_service.add_audio_to_playback_buffer(self.session_state, audio_content)
    
    async def _handle_speech_started(self, message: Dict[str, Any]):
        """Handle speech started event - user interruption detected by OpenAI"""
        logger.info(colorize_audio_log(f"🚨 USER SPEECH STARTED - clearing audio buffer for session {self.session_id}"))
        
        # Clear audio buffer immediately to stop current playback
        self.session_state.audio_buffer.clear()
        
        # Optionally cancel current AI response
        try:
            cancel_message = {"type": "response.cancel"}
            if hasattr(self.openai_service, 'send_message'):
                await self.openai_service.send_message(self.session_state, cancel_message)
                logger.debug(f"Sent response cancellation for session {self.session_id}")
        except Exception as e:
            logger.debug(f"Could not cancel response (this is normal): {e}")
    
    async def _handle_user_transcription_delta(self, message: Dict[str, Any]):
        """Handle user transcription delta"""
        delta = message.get('delta', '')
        
        # Log full delta message for debugging
        logger.debug(f"Full delta message: {message}")
        
        if delta and delta.strip():
            self.session_state.add_user_transcript(delta)
            logger.debug(f"User transcript delta: '{delta}'")
        else:
            logger.debug("Received empty delta")
    
    async def _handle_user_transcription_completed(self, message: Dict[str, Any]):
        """Handle completed user transcription"""
        # Log the full message to debug transcription quality
        logger.debug(f"Full transcription message: {message}")
        
        transcript = message.get('transcript', '')
        
        # Also check if there's additional transcription data
        item = message.get('item', {})
        if item:
            logger.debug(f"Transcription item data: {item}")
        
        logger.info(colorize(f"🗣️ User said: {transcript}", Colors.BRIGHT_CYAN))
        
        # Check for termination commands before processing
        if transcript and transcript.strip():
            # Check if user wants to end the conversation
            if self._is_termination_command(transcript):
                logger.info(colorize(f"🛑 Termination command detected: {transcript}", Colors.BRIGHT_YELLOW))
                await self._handle_conversation_termination()
                return
            
            # Normal transcript processing
            self.conversation_service.update_conversation_context(self.session_state, "user", transcript)
        else:
            logger.warning("Received empty or invalid transcript")
    
    async def _handle_ai_transcription_delta(self, message: Dict[str, Any]):
        """Handle AI transcription delta"""
        delta = message.get('delta', '')
        self.session_state.add_ai_transcript(delta)
        logger.debug(f"AI transcript delta: {delta}")
    
    async def _handle_ai_transcription_completed(self, message: Dict[str, Any]):
        """Handle completed AI transcription"""
        transcript = message.get('transcript', '')
        logger.info(colorize(f"🤖 AI said: {transcript}", Colors.BRIGHT_GREEN))
        self.conversation_service.update_conversation_context(self.session_state, "ai", transcript)
    
    async def _handle_function_call(self, message: Dict[str, Any]):
        """Handle function call from OpenAI"""
        result, call_id = await self.conversation_service.handle_function_call(message, self.session_state)
        await self.openai_service.send_function_call_result(self.session_state, result, call_id)
    
    async def _handle_error(self, message: Dict[str, Any]):
        """Handle error messages from OpenAI"""
        error = message.get('error', {})
        error_code = error.get('code', '')
        
        # Some errors are expected and normal during interruptions
        if error_code == 'response_cancel_not_active':
            logger.debug(f"Expected OpenAI response: {error.get('message', 'No active response to cancel')}")
        else:
            logger.error(f"OpenAI error: {error}")
    
    async def stop_conversation(self):
        """Stop the conversation and cleanup resources"""
        logger.info(colorize_session_log(f"🛑 Stopping conversation for session {self.session_id}"))
        
        if self.session_state:
            self.session_state.stop_session()
        
        # Cancel all tasks
        await self._cleanup_tasks()
        
        # Close WebSocket connection
        if self.session_state:
            await self.openai_service.close_connection(self.session_state)
        
        # Stop audio streams
        if self.mic_stream or self.speaker_stream:
            self.audio_service.stop_audio_streams(self.mic_stream, self.speaker_stream)
        
        # Cleanup audio resources
        self.audio_service.cleanup_audio()
        
        # Remove session from manager
        session_manager.remove_session(self.session_id)
        
        logger.info(f"Conversation stopped for session {self.session_id}")
    
    async def _cleanup_tasks(self):
        """Cancel and cleanup all running tasks"""
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self.tasks.clear()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        if not self.session_state:
            return {"error": "No active session"}
        
        return self.conversation_service.get_conversation_summary(self.session_state)
    
    def is_active(self) -> bool:
        """Check if the conversation is active"""
        return self.session_state is not None and self.session_state.is_active
    
    def _is_termination_command(self, transcript: str) -> bool:
        """Check if the transcript contains a termination command"""
        # Normalize the transcript for comparison - remove punctuation
        import re
        normalized = re.sub(r'[^\w\s]', '', transcript.lower().strip())
        
        if not normalized:
            return False
        
        # Common termination phrases in English and Spanish
        termination_phrases = [
            # English
            "stop", "end", "finish", "quit", "exit", "bye", "goodbye",
            "stop conversation", "end conversation", "finish conversation",
            "stop talking", "end session", "finish session",
            "that's all", "thats all", "that's enough", "thats enough", "i'm done", "im done", "we're done", "were done",
            "terminate", "close", "stop please", "end please",
            "i want to stop", "i want to end", "i want to finish",
            
            # Spanish
            "para", "termina", "finaliza", "sal", "salir", "adiós", "adios", "chao",
            "para conversación", "termina conversación", "finaliza conversación",
            "para conversacion", "termina conversacion", "finaliza conversacion",
            "para de hablar", "termina sesión", "finaliza sesión",
            "para de sesion", "termina sesion", "finaliza sesion",
            "es todo", "es suficiente", "ya terminé", "ya terminamos", "ya termine",
            "terminar", "cerrar", "para por favor", "termina por favor",
            "quiero parar", "quiero terminar", "quiero finalizar"
        ]
        
        # Check for exact matches first
        for phrase in termination_phrases:
            if normalized == phrase:
                return True
        
        # Check if transcript starts with termination phrases
        for phrase in termination_phrases:
            if normalized.startswith(phrase + " "):
                return True
        
        # Check for termination intent patterns
        termination_patterns = [
            r'^(stop|end|finish|quit|para|termina|finaliza)$',  # Single word
            r'^(stop|end|finish|quit|para|termina|finaliza)\s+(now|please|ya|por favor)$',  # Word + modifier
            r'^(i want to|i need to|quiero|necesito)\s+(stop|end|finish|quit|para|terminar|finalizar)$',  # Intent + action
            r'^(please|por favor)\s+(stop|end|finish|quit|para|termina|finaliza)$',  # Polite request
        ]
        
        for pattern in termination_patterns:
            if re.match(pattern, normalized):
                return True
        
        # Avoid false positives - check for context that suggests NOT termination
        false_positive_patterns = [
            r'\b(stop sign|stop light|stop motion|bus stop|stop watch|stop button)\b',  # "stop" in different context
            r'\b(the end of|end of the|ending|end result|end game)\b',  # "end" in narrative context
            r'\b(stopped|ending|finished|finishing)\b',  # Past tense forms
            r'\b(stop by|stop over|stop in|stop at)\b',  # Phrasal verbs
        ]
        
        for pattern in false_positive_patterns:
            if re.search(pattern, normalized):
                return False
        
        # Additional check: if "stop" is followed by a noun, it's likely not a termination command
        if re.search(r'\bstop\s+(sign|light|button|watch|motion|car|bus|train|music|video|game|app)\b', normalized):
            return False
        
        # For very short phrases (1-2 words), be more permissive with core termination words
        words = normalized.split()
        if len(words) <= 2:
            core_termination_words = ["stop", "end", "finish", "quit", "bye", "para", "termina", "finaliza"]
            for word in words:
                if word in core_termination_words:
                    return True
        
        return False
    
    async def _handle_conversation_termination(self):
        """Handle conversation termination gracefully"""
        try:
            logger.info(colorize("🛑 Starting conversation termination process...", Colors.BRIGHT_YELLOW))
            
            # Send a farewell message to the user
            farewell_message = {
                "type": "response.create",
                "response": {
                    "modalities": ["text", "audio"],
                    "instructions": "Say a brief, friendly goodbye to the user. Thank them for the conversation and wish them well with their English learning."
                }
            }
            
            await self.openai_service.send_message(self.session_state, farewell_message)
            
            # Wait a moment for the farewell to be processed
            await asyncio.sleep(2)
            
            # Mark session as ending
            if self.session_state:
                self.session_state.is_active = False
                logger.info("✅ Session marked as inactive")
            
            # Close the WebSocket connection gracefully
            if self.openai_service and hasattr(self.openai_service, 'websocket'):
                await self.openai_service.close_connection(self.session_state)
                logger.info("✅ WebSocket connection closed")
            
            logger.info(colorize("🎯 Conversation termination completed successfully", Colors.BRIGHT_GREEN))
            
        except Exception as e:
            logger.error(f"Error during conversation termination: {e}")
            # Force close the session even if there's an error
            if self.session_state:
                self.session_state.is_active = False
