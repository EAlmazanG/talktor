"""
Middleware for FastAPI application
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger
from schemas.common import ErrorResponse

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(f"🌐 [{request_id}] {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"✅ [{request_id}] {response.status_code} - {process_time:.3f}s"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"❌ [{request_id}] Error: {str(e)} - {process_time:.3f}s")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    message="Internal server error",
                    error_code="INTERNAL_ERROR",
                    details={"request_id": request_id}
                ).dict(),
                headers={"X-Request-ID": request_id}
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle and format errors consistently
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            error_response = ErrorResponse(
                message=e.detail,
                error_code=f"HTTP_{e.status_code}",
                details={
                    "request_id": request_id,
                    "status_code": e.status_code
                }
            )
            
            return JSONResponse(
                status_code=e.status_code,
                content=error_response.dict()
            )
        except Exception as e:
            # Handle unexpected errors
            request_id = getattr(request.state, 'request_id', 'unknown')
            logger.error(f"❌ Unhandled error in request {request_id}: {str(e)}")
            
            error_response = ErrorResponse(
                message="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
                details={"request_id": request_id}
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response.dict()
            )


def setup_cors(app):
    """
    Setup CORS middleware
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_middleware(app):
    """
    Setup all middleware for the application
    """
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Setup CORS
    setup_cors(app)
