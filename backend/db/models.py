"""
Database models for Talktor application
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class AgentType(enum.Enum):
    """Types of AI agents"""
    REALTIME = "realtime"
    STANDARD = "standard"


class ConversationMode(enum.Enum):
    """Conversation modes from PRD"""
    FREE_TOPIC = "free_topic"
    REVIEW_PREVIOUS = "review_previous"
    SITUATIONAL = "situational"
    DYNAMIC = "dynamic"
    CHALLENGE = "challenge"


class Speaker(enum.Enum):
    """Who is speaking in the conversation"""
    USER = "user"
    AI = "ai"


class FeedbackPillar(enum.Enum):
    """The 6 feedback pillars from PRD"""
    PRONUNCIATION = "pronunciation"
    FLUENCY = "fluency"
    GRAMMAR = "grammar"
    EXPRESSIONS = "expressions"
    VOCABULARY = "vocabulary"
    COMPREHENSION = "comprehension"


class Session(Base):
    """
    Session model - Metadatos de conversación
    Stores metadata about each conversation session
    """
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Session identification
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    
    # Session configuration
    agent_type = Column(Enum(AgentType), nullable=False)
    mode = Column(Enum(ConversationMode), nullable=False)
    topic = Column(String(200), nullable=True)
    
    # Session metrics
    duration_seconds = Column(Integer, nullable=True)  # Total duration
    token_count = Column(Integer, nullable=True)       # Total tokens used
    estimated_cost = Column(Float, nullable=True)      # Estimated cost in USD
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Session status and metadata
    status = Column(String(50), default="active")  # active, completed, interrupted, error
    notes = Column(Text, nullable=True)            # User notes about the session
    
    # Relationships
    transcripts = relationship("Transcript", back_populates="session", cascade="all, delete-orphan")
    feedback_items = relationship("Feedback", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, session_id='{self.session_id}', user_id='{self.user_id}')>"


class Transcript(Base):
    """
    Transcript model - Texto de la conversación con timestamps
    Stores individual messages/utterances in the conversation
    """
    __tablename__ = "transcripts"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to session
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Message details
    speaker = Column(Enum(Speaker), nullable=False)
    content = Column(Text, nullable=False)
    sequence_number = Column(Integer, nullable=False)  # Order in conversation
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional metadata
    confidence_score = Column(Float, nullable=True)    # Transcription confidence (0-1)
    audio_duration = Column(Float, nullable=True)      # Duration of audio segment
    
    # Relationships
    session = relationship("Session", back_populates="transcripts")
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, session_id={self.session_id}, speaker='{self.speaker}')>"


class Feedback(Base):
    """
    Feedback model - Feedback estructurado por pilares
    Stores structured feedback analysis for each session
    """
    __tablename__ = "feedback"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to session
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Feedback details
    pillar = Column(Enum(FeedbackPillar), nullable=False)
    score = Column(Float, nullable=False)              # Score 1-10
    feedback_text = Column(Text, nullable=False)       # Detailed feedback
    
    # Structured data
    examples = Column(JSON, nullable=True)             # Examples from conversation
    suggestions = Column(JSON, nullable=True)          # Improvement suggestions
    errors = Column(JSON, nullable=True)               # Specific errors found
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_by = Column(String(50), default="standard_agent")  # Which agent generated this
    
    # Relationships
    session = relationship("Session", back_populates="feedback_items")
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, session_id={self.session_id}, pillar='{self.pillar}', score={self.score})>"


# Additional models for future implementation (homework, flashcards, etc.)
class HomeworkItem(Base):
    """
    Homework items generated from feedback
    """
    __tablename__ = "homework_items"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    category = Column(String(50), nullable=False)      # vocabulary, grammar, pronunciation, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False)    # beginner, intermediate, advanced
    priority = Column(String(20), nullable=False)      # high, medium, low
    estimated_time_minutes = Column(Integer, nullable=True)
    
    status = Column(String(20), default="pending")     # pending, in_progress, completed
    completed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<HomeworkItem(id={self.id}, title='{self.title}', status='{self.status}')>"


class VocabularyItem(Base):
    """
    Vocabulary items to learn/review
    """
    __tablename__ = "vocabulary_items"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)  # Can be session-specific or general
    
    word_or_phrase = Column(String(200), nullable=False)
    definition = Column(Text, nullable=False)
    example_sentence = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False)
    
    times_reviewed = Column(Integer, default=0)
    times_correct = Column(Integer, default=0)
    last_reviewed = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<VocabularyItem(id={self.id}, word='{self.word_or_phrase}')>"
