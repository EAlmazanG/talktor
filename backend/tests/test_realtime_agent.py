"""
Test script for the new Realtime Agent architecture
This script replicates the functionality of the original POC using the new modular architecture
"""
import asyncio
import signal
import sys
from datetime import datetime

import sys
import os

# Add parent directory to path to import from backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.realtime_agent import RealtimeAgent
from services.session_state import session_manager
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging("INFO")
logger = get_logger(__name__)

# Global variables for graceful shutdown
current_agent = None
shutdown_event = asyncio.Event()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping conversation...")
    shutdown_event.set()


async def main():
    """Main function to test the realtime agent"""
    global current_agent
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Generate a unique session ID
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_id = "test_user"
    
    logger.info(f"Starting Talktor Realtime Agent Test")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Press Ctrl+C to stop the conversation")
    
    try:
        # Create and start the realtime agent
        current_agent = RealtimeAgent(session_id, user_id)
        
        # Start the conversation
        conversation_task = asyncio.create_task(
            current_agent.start_conversation(
                topic="English conversation practice",
                mode="free_topic"
            )
        )
        
        # Wait for shutdown signal or conversation to end
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        
        # Wait for either the conversation to end or shutdown signal
        done, pending = await asyncio.wait(
            [conversation_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Check if conversation ended due to error
        if conversation_task in done:
            try:
                await conversation_task
            except Exception as e:
                logger.error(f"Conversation ended with error: {e}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
    
    finally:
        # Cleanup
        if current_agent:
            await current_agent.stop_conversation()
        
        # Show session summary
        active_sessions = session_manager.get_active_sessions()
        logger.info(f"Active sessions at shutdown: {len(active_sessions)}")
        
        # Cleanup session manager
        session_manager.cleanup_inactive_sessions()
        
        logger.info("Test completed. Goodbye!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
