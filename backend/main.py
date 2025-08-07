from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routes
from api.v1 import conversations, feedback, sessions, users
from api.middleware import setup_middleware
from schemas.common import HealthCheckResponse
from core.logging import get_logger
from db.database import get_db_session
from services.persistence_service import persistence_service

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Talktor API",
    description="REST API for the Talktor English conversation learning platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup middleware
setup_middleware(app)

# Include API v1 routes
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def read_root():
    """Root endpoint returning API information"""
    return {
        "message": "Welcome to Talktor API",
        "version": "1.0.0",
        "description": "REST API for English conversation learning",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db = get_db_session()
        health_info = persistence_service.health_check(db)
        db.close()
        
        return HealthCheckResponse(
            status="healthy",
            database="connected",
            services={
                "api": "healthy",
                "database": "connected",
                "persistence": "healthy",
                "total_sessions": str(health_info.get("total_sessions", 0))
            }
        )
    except Exception as e:
        logger.error(f" Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            database="disconnected",
            services={
                "api": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


@app.get("/api/v1", tags=["api"])
async def api_info():
    """API v1 information endpoint"""
    return {
        "version": "v1",
        "endpoints": {
            "conversations": "/api/v1/conversations",
            "feedback": "/api/v1/feedback",
            "sessions": "/api/v1/sessions",
            "users": "/api/v1/users"
        },
        "websocket": {
            "realtime_conversation": "/api/v1/conversations/{session_id}/realtime"
        }
    }


if __name__ == "__main__":
    import uvicorn
    logger.info(" Starting Talktor API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
