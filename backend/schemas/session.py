"""
Session-related schemas for the Talktor API
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from db.models import AgentType, ConversationMode


class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    user_id: str = Field(description="User identifier")
    agent_type: AgentType = Field(default=AgentType.REALTIME, description="Type of AI agent to use")
    mode: ConversationMode = Field(default=ConversationMode.FREE_TOPIC, description="Conversation mode")
    topic: Optional[str] = Field(None, description="Optional conversation topic")


class SessionResponse(BaseModel):
    """Schema for session response"""
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User identifier")
    agent_type: AgentType = Field(description="Type of AI agent used")
    mode: ConversationMode = Field(description="Conversation mode")
    topic: Optional[str] = Field(None, description="Conversation topic")
    duration_seconds: Optional[int] = Field(None, description="Session duration in seconds")
    token_count: Optional[int] = Field(None, description="Total tokens used")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost in USD")
    started_at: datetime = Field(description="Session start time")
    ended_at: Optional[datetime] = Field(None, description="Session end time")
    status: str = Field(description="Session status")
    notes: Optional[str] = Field(None, description="Optional session notes")

    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    """Schema for session summary with additional data"""
    session: SessionResponse = Field(description="Session details")
    message_count: int = Field(description="Number of messages in conversation")
    has_feedback: bool = Field(description="Whether feedback is available")
    feedback_score: Optional[float] = Field(None, description="Overall feedback score")


class SessionListResponse(BaseModel):
    """Schema for listing user sessions"""
    sessions: List[SessionSummary] = Field(description="List of user sessions")
    total: int = Field(description="Total number of sessions")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
