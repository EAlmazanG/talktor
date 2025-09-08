"""
Common schemas for API responses and shared data structures
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model for all API responses"""
    success: bool = Field(description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = Field(default=False)
    error_code: Optional[str] = Field(None, description="Error code for client handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = Field(default=True)
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    success: bool = Field(default=True)
    data: List[Dict[str, Any]] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now)
    database: str = Field(description="Database connection status")
    services: Dict[str, str] = Field(description="Status of various services")
