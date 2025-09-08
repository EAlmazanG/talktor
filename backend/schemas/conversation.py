"""
Conversation-related schemas for the Talktor API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from db.models import Speaker


class MessageResponse(BaseModel):
    """Schema for individual conversation messages"""
    role: str = Field(description="Message role (user/assistant)")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(description="Message timestamp")
    order: int = Field(description="Message order in conversation")


class ConversationStart(BaseModel):
    """Schema for starting a conversation"""
    user_id: str = Field(description="User identifier")
    session_id: Optional[str] = Field(None, description="Optional session ID (auto-generated if not provided)")


class ConversationStartResponse(BaseModel):
    """Schema for conversation start response"""
    session_id: str = Field(description="Session identifier")
    status: str = Field(description="Conversation status")
    websocket_url: Optional[str] = Field(None, description="WebSocket URL for real-time communication")


class ConversationEnd(BaseModel):
    """Schema for ending a conversation"""
    force_feedback: bool = Field(default=False, description="Force feedback generation even for short conversations")


class ConversationEndResponse(BaseModel):
    """Schema for conversation end response"""
    session_id: str = Field(description="Session identifier")
    duration_seconds: float = Field(description="Total conversation duration")
    message_count: int = Field(description="Number of messages exchanged")
    status: str = Field(description="Final conversation status")
    feedback_generated: bool = Field(description="Whether feedback was generated")


class ConversationDetails(BaseModel):
    """Schema for detailed conversation information"""
    session_id: str = Field(description="Session identifier")
    user_id: str = Field(description="User identifier")
    duration_seconds: Optional[float] = Field(None, description="Conversation duration")
    message_count: int = Field(description="Number of messages")
    messages: List[MessageResponse] = Field(description="Conversation messages")
    status: str = Field(description="Conversation status")
    started_at: datetime = Field(description="Conversation start time")
    ended_at: Optional[datetime] = Field(None, description="Conversation end time")


class TranscriptResponse(BaseModel):
    """Schema for conversation transcript"""
    session_id: str = Field(description="Session identifier")
    speaker: Speaker = Field(description="Who spoke (user/ai)")
    content: str = Field(description="Transcript content")
    sequence_number: int = Field(description="Order in conversation")
    timestamp: datetime = Field(description="When the message was spoken")
    confidence_score: Optional[float] = Field(None, description="Transcription confidence")
    audio_duration: Optional[float] = Field(None, description="Audio segment duration")

    class Config:
        from_attributes = True
