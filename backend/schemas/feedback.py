"""
Feedback-related schemas for the Talktor API
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class PillarFeedback(BaseModel):
    """Schema for individual pillar feedback"""
    score: Optional[float] = Field(None, description="Score from 1.0 to 10.0", ge=1.0, le=10.0)
    summary: Optional[str] = Field(None, description="Summary of performance in this pillar")
    errors: List[str] = Field(default_factory=list, description="Specific errors or issues")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")


class FeedbackResponse(BaseModel):
    """Schema for complete feedback response"""
    session_id: str = Field(description="Session identifier")
    overall_score: Optional[float] = Field(None, description="Overall score from 1.0 to 10.0", ge=1.0, le=10.0)
    general_feedback: Optional[str] = Field(None, description="General feedback about performance")
    general_summary: Optional[str] = Field(None, description="Summary of conversation topics")
    general_errors: List[str] = Field(default_factory=list, description="General errors observed")
    general_suggestions: List[str] = Field(default_factory=list, description="General suggestions")
    
    # Pillar-specific feedback
    pronunciation: PillarFeedback = Field(default_factory=PillarFeedback, description="Pronunciation feedback")
    fluency: PillarFeedback = Field(default_factory=PillarFeedback, description="Fluency feedback")
    grammar: PillarFeedback = Field(default_factory=PillarFeedback, description="Grammar feedback")
    expressions: PillarFeedback = Field(default_factory=PillarFeedback, description="Expressions feedback")
    vocabulary: PillarFeedback = Field(default_factory=PillarFeedback, description="Vocabulary feedback")
    comprehension: PillarFeedback = Field(default_factory=PillarFeedback, description="Comprehension feedback")
    
    # Metadata
    created_at: datetime = Field(description="When feedback was generated")
    generated_by: str = Field(description="Which agent generated the feedback")

    class Config:
        from_attributes = True


class FeedbackSummary(BaseModel):
    """Schema for feedback summary (lighter version)"""
    session_id: str = Field(description="Session identifier")
    overall_score: Optional[float] = Field(None, description="Overall score")
    general_summary: Optional[str] = Field(None, description="Summary of conversation topics")
    pillar_scores: Dict[str, Optional[float]] = Field(description="Scores for each pillar")
    created_at: datetime = Field(description="When feedback was generated")


class UserProgress(BaseModel):
    """Schema for user progress across sessions"""
    user_id: str = Field(description="User identifier")
    total_sessions: int = Field(description="Total number of sessions")
    average_score: Optional[float] = Field(None, description="Average overall score")
    latest_session_date: Optional[datetime] = Field(None, description="Date of latest session")
    pillar_averages: Dict[str, Optional[float]] = Field(description="Average scores per pillar")
    improvement_areas: List[str] = Field(description="Areas that need improvement")
    strengths: List[str] = Field(description="User's strongest areas")


class FeedbackRequest(BaseModel):
    """Schema for requesting feedback generation"""
    session_id: str = Field(description="Session identifier")
    force_generation: bool = Field(default=False, description="Force feedback generation even for short conversations")
