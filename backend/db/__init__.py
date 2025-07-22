# Database package

from .database import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    create_tables,
    drop_tables,
    test_connection,
    init_database
)

from .models import (
    Base,
    Session,
    Transcript,
    Feedback,
    HomeworkItem,
    VocabularyItem,
    AgentType,
    ConversationMode,
    Speaker,
    FeedbackPillar
)

from .crud import (
    SessionCRUD,
    TranscriptCRUD,
    FeedbackCRUD,
    HomeworkCRUD,
    get_session_summary
)

__all__ = [
    # Database connection
    'engine',
    'SessionLocal', 
    'get_db',
    'get_db_session',
    'create_tables',
    'drop_tables',
    'test_connection',
    'init_database',
    
    # Models
    'Base',
    'Session',
    'Transcript', 
    'Feedback',
    'HomeworkItem',
    'VocabularyItem',
    'AgentType',
    'ConversationMode',
    'Speaker',
    'FeedbackPillar',
    
    # CRUD operations
    'SessionCRUD',
    'TranscriptCRUD',
    'FeedbackCRUD', 
    'HomeworkCRUD',
    'get_session_summary'
]
