"""
Session state management for individual conversation sessions
"""
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionState:
    """State container for a single conversation session"""
    
    session_id: str
    user_id: Optional[str] = None
    
    # Audio buffers and queues
    audio_buffer: bytearray = field(default_factory=bytearray)
    mic_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    
    # Session control
    is_active: bool = True
    is_mic_active: bool = False
    
    # Transcription tracking - now using structured messages
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Legacy fields for backward compatibility (will be deprecated)
    user_transcript: str = ""
    ai_transcript: str = ""
    
    # Session metadata
    started_at: datetime = field(default_factory=datetime.now)
    topic: Optional[str] = None
    mode: str = "free_topic"
    
    # WebSocket connection
    websocket_connection: Optional[Any] = None
    
    # Session configuration
    session_config: Optional[Dict[str, Any]] = None
    
    # Reference to the agent handling this session
    agent: Optional[Any] = None
    
    def reset_transcripts(self):
        """Reset transcript buffers"""
        self.user_transcript = ""
        self.ai_transcript = ""
    
    def add_user_transcript(self, text: str):
        """Add text to user transcript"""
        self.user_transcript += text
    
    def add_ai_transcript(self, text: str):
        """Add text to AI transcript"""
        self.ai_transcript += text
    
    def get_session_duration(self) -> float:
        """Get session duration in seconds"""
        return (datetime.now() - self.started_at).total_seconds()
    
    def stop_session(self):
        """Mark session as inactive"""
        self.is_active = False
    
    def add_message(self, role: str, content: str, timestamp: Optional[datetime] = None):
        """Add a structured message to the conversation"""
        if timestamp is None:
            timestamp = datetime.now()
        
        message = {
            "role": role,  # "user" or "assistant"
            "content": content.strip(),
            "timestamp": timestamp,
            "order": len(self.messages) + 1
        }
        
        self.messages.append(message)
        
        # Update legacy fields for backward compatibility
        if role == "user":
            self.user_transcript += content
        elif role == "assistant":
            self.ai_transcript += content
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in chronological order"""
        return sorted(self.messages, key=lambda x: x["timestamp"])
    
    def get_conversation_json(self) -> Dict[str, Any]:
        """Get complete conversation as structured JSON"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat(),
            "duration_seconds": self.get_session_duration(),
            "mode": self.mode,
            "topic": self.topic,
            "message_count": len(self.messages),
            "messages": self.get_messages()
        }
    
    def reset_messages(self):
        """Reset all messages and transcripts"""
        self.messages.clear()
        self.reset_transcripts()


class SessionManager:
    """Manages multiple active sessions"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
    
    def create_session(self, session_id: str, user_id: Optional[str] = None) -> SessionState:
        """Create a new session"""
        if session_id in self._sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        session = SessionState(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get an existing session"""
        return self._sessions.get(session_id)
    
    def remove_session(self, session_id: str) -> bool:
        """Remove a session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.stop_session()
            del self._sessions[session_id]
            return True
        return False
    
    def get_active_sessions(self) -> Dict[str, SessionState]:
        """Get all active sessions"""
        return {sid: session for sid, session in self._sessions.items() if session.is_active}
    
    def cleanup_inactive_sessions(self):
        """Remove inactive sessions"""
        inactive_sessions = [sid for sid, session in self._sessions.items() if not session.is_active]
        for session_id in inactive_sessions:
            del self._sessions[session_id]


# Global session manager instance
session_manager = SessionManager()
