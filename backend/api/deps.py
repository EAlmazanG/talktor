"""
Dependencies for FastAPI endpoints
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from db.database import get_db_session
from services.persistence_service import persistence_service
from core.logging import get_logger

logger = get_logger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def get_persistence_service():
    """
    Dependency to get persistence service
    """
    return persistence_service


async def verify_session_exists(session_id: str, db: Session = Depends(get_db)) -> str:
    """
    Verify that a session exists in the database
    """
    session = persistence_service.session_crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return session_id


async def get_user_id_from_header(x_user_id: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from header (for now, simple header-based auth)
    In production, this would be replaced with proper JWT/OAuth authentication
    """
    if not x_user_id:
        # For development, use a default user
        return "default_user"
    return x_user_id


async def validate_user_access(
    session_id: str,
    user_id: str = Depends(get_user_id_from_header),
    db: Session = Depends(get_db)
) -> tuple[str, str]:
    """
    Validate that the user has access to the specified session
    """
    session = persistence_service.session_crud.get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Session belongs to different user"
        )
    
    return session_id, user_id


class CommonQueryParams:
    """
    Common query parameters for pagination and filtering
    """
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.page = max(1, page)
        self.page_size = min(100, max(1, page_size))  # Limit page size to 100
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.offset = (self.page - 1) * self.page_size
