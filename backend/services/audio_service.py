"""
Audio service for handling microphone input and speaker output
"""
import asyncio
import base64
import pyaudio
from typing import Callable, Optional
import logging
from core.config import settings
from core.logging import get_logger
from core.colors import colorize_audio_log, Colors, colorize
from .session_state import SessionState

logger = get_logger(__name__)


class AudioService:
    """Service for managing audio input/output operations"""
    
    def __init__(self):
        self.pyaudio_instance = None
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = settings.audio_sample_rate
        self.chunk_size = settings.audio_chunk_size
        
    def initialize_audio(self):
        """Initialize PyAudio instance"""
        if self.pyaudio_instance is None:
            self.pyaudio_instance = pyaudio.PyAudio()
    
    def cleanup_audio(self):
        """Cleanup PyAudio resources"""
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            self.pyaudio_instance = None
    
    def create_mic_callback(self, session_state: SessionState):
        """Create microphone callback for a specific session"""
        def mic_callback(in_data, frame_count, time_info, status):
            if not session_state.is_mic_active:
                logger.debug(f"Mic activated for session {session_state.session_id}")
                session_state.is_mic_active = True
            
            # Put audio data in session's queue (non-blocking)
            try:
                session_state.mic_queue.put_nowait(in_data)
            except asyncio.QueueFull:
                logger.warning(f"Mic queue full for session {session_state.session_id}")
            
            return (None, pyaudio.paContinue)
        
        return mic_callback
    
    def create_speaker_callback(self, session_state: SessionState):
        """Create speaker callback for a specific session"""
        def speaker_callback(in_data, frame_count, time_info, status):
            bytes_to_read = frame_count * self.channels * 2  # 2 bytes per sample for paInt16
            
            if len(session_state.audio_buffer) >= bytes_to_read:
                # Extract audio data from buffer
                audio_data = bytes(session_state.audio_buffer[:bytes_to_read])
                # Remove consumed data from buffer
                del session_state.audio_buffer[:bytes_to_read]
                return (audio_data, pyaudio.paContinue)
            else:
                # Not enough data, return silence
                silence = b'\x00' * bytes_to_read
                return (silence, pyaudio.paContinue)
        
        return speaker_callback
    
    def start_audio_streams(self, session_state: SessionState):
        """Start audio input and output streams for a session"""
        self.initialize_audio()
        
        # Create callbacks for this session
        mic_callback = self.create_mic_callback(session_state)
        speaker_callback = self.create_speaker_callback(session_state)
        
        # Create microphone stream
        mic_stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            stream_callback=mic_callback,
            frames_per_buffer=self.chunk_size
        )
        
        # Create speaker stream
        speaker_stream = self.pyaudio_instance.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            output=True,
            stream_callback=speaker_callback,
            frames_per_buffer=self.chunk_size
        )
        
        # Start streams
        mic_stream.start_stream()
        speaker_stream.start_stream()
        
        logger.info(colorize_audio_log(f"🎧 Audio streams started for session {session_state.session_id}"))
        
        return mic_stream, speaker_stream
    
    def stop_audio_streams(self, mic_stream, speaker_stream):
        """Stop and cleanup audio streams"""
        try:
            if mic_stream and mic_stream.is_active():
                mic_stream.stop_stream()
                mic_stream.close()
            
            if speaker_stream and speaker_stream.is_active():
                speaker_stream.stop_stream()
                speaker_stream.close()
            
            logger.info("Audio streams stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping audio streams: {e}")
    
    async def process_mic_queue(self, session_state: SessionState, audio_sender_callback: Callable):
        """Process microphone audio queue and send to callback"""
        try:
            while session_state.is_active:
                try:
                    # Get audio chunk from queue with timeout
                    mic_chunk = await asyncio.wait_for(
                        session_state.mic_queue.get(), 
                        timeout=0.1
                    )
                    
                    # Encode and send audio chunk
                    encoded_chunk = base64.b64encode(mic_chunk).decode('utf-8')
                    await audio_sender_callback(encoded_chunk)
                    
                except asyncio.TimeoutError:
                    # No audio data available, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing mic queue: {e}")
                    break
        except Exception as e:
            logger.error(f"Exception in process_mic_queue: {e}")
        finally:
            logger.info(f"Exiting mic queue processing for session {session_state.session_id}")
    
    def add_audio_to_playback_buffer(self, session_state: SessionState, audio_data: bytes):
        """Add audio data to the session's playback buffer"""
        session_state.audio_buffer.extend(audio_data)
