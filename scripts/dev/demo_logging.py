#!/usr/bin/env python3
"""
Demo script to show the enhanced logging system
"""
import sys
import os
import logging
import asyncio
from pathlib import Path

def _find_repo_root(start: Path) -> Path:
    """Walk up from start until a directory containing 'backend' is found."""
    p = start.resolve()
    while p != p.parent:
        if (p / "backend").exists():
            return p
        p = p.parent
    return start.resolve()

# Add backend to path robustly regardless of script location
repo_root = _find_repo_root(Path(__file__).parent)
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

# Change to backend directory for relative paths
os.chdir(backend_path)

from core.logging import setup_logging

# Setup logging with file output
setup_logging(
    level="DEBUG",
    enable_file_logging=True,
    log_directory="logs",
    service_name="demo_logging"
)

# Get logger for this module
logger = logging.getLogger(__name__)


def demo_basic_logging():
    """Demo basic logging levels"""
    logger.info("🚀 Starting logging demo")
    logger.debug("This is a debug message - detailed information")
    logger.info("This is an info message - general information")
    logger.warning("This is a warning message - something might be wrong")
    logger.error("This is an error message - something went wrong")
    
    try:
        # Simulate an error
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error(f"Division by zero error: {e}", exc_info=True)


async def demo_async_logging():
    """Demo logging in async context"""
    logger.info("🔄 Starting async operation")
    
    for i in range(3):
        logger.debug(f"Processing item {i+1}")
        await asyncio.sleep(0.5)
        logger.info(f"✅ Completed item {i+1}")
    
    logger.info("🏁 Async operation completed")


def demo_structured_logging():
    """Demo structured logging with extra context"""
    user_id = "demo_user_123"
    session_id = "session_456"
    
    # Create a logger with extra context
    context_logger = logging.getLogger(f"{__name__}.user_session")
    
    context_logger.info(f"User {user_id} started session {session_id}")
    context_logger.debug(f"Session configuration loaded for {user_id}")
    context_logger.info(f"Processing conversation for session {session_id}")
    context_logger.warning(f"High latency detected for user {user_id}")
    context_logger.info(f"Session {session_id} completed successfully")


def main():
    print("🎯 Talktor Enhanced Logging Demo")
    print("=" * 50)
    print("This demo will generate various log messages.")
    print("Check both console output and the log file!")
    print()
    
    # Demo basic logging
    print("📝 1. Basic logging levels...")
    demo_basic_logging()
    
    print("\n🔄 2. Async logging...")
    asyncio.run(demo_async_logging())
    
    print("\n🏷️  3. Structured logging with context...")
    demo_structured_logging()
    
    print("\n✅ Demo completed!")
    print("📁 Check the logs/ directory for the generated log file.")
    print("💡 Use 'python scripts/dev/view_logs.py' to view logs easily.")


if __name__ == "__main__":
    main()
