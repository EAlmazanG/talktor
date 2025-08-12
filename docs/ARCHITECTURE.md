# Talktor Backend Architecture

## Overview

This document explains the new modular architecture for the Talktor backend, which transforms the original POC script into a scalable, maintainable system.

## Architecture Components

### 1. Configuration (`config.py`)
- Centralized configuration management using Pydantic Settings
- Environment variable loading from `.env` file
- Audio, OpenAI, and session settings

### 2. Services Layer (`services/`)

#### `session_state.py`
- **SessionState**: Container for individual session data (audio buffers, transcripts, metadata)
- **SessionManager**: Manages multiple concurrent sessions
- Replaces global variables from the POC with session-scoped state

#### `audio_service.py`
- **AudioService**: Handles PyAudio operations (microphone input, speaker output)
- Creates session-specific audio callbacks
- Manages audio streams lifecycle
- Processes audio queues asynchronously

#### `openai_service.py`
- **OpenAIService**: Manages WebSocket connections to OpenAI Realtime API
- Handles session configuration and message sending/receiving
- Manages function call responses
- IPv4 connection enforcement (from POC)

#### `conversation_service.py`
- **ConversationService**: Processes conversation logic and function calls
- Handles the `continue_conversation` function (expandable for future features)
- Manages conversation context and summaries
- Placeholder for future feedback and analysis features

### 3. Agents Layer (`agents/`)

#### `realtime_agent.py`
- **RealtimeAgent**: Orchestrates all services for a complete conversation
- Manages the full conversation lifecycle
- Handles concurrent tasks (audio processing, WebSocket communication)
- Provides clean start/stop interface
- Maintains session state and cleanup

## Key Architectural Improvements

### From POC to Production

| POC Approach | New Architecture |
|-------------|------------------|
| Global variables | Session-scoped state |
| Threading | Async/await |
| Monolithic script | Modular services |
| Single session | Multi-session support |
| Direct PyAudio calls | Audio service abstraction |
| Hardcoded config | Environment-based config |

### Scalability Features

1. **Multi-Session Support**: Each conversation runs in its own session with isolated state
2. **Async Operations**: Non-blocking I/O for better resource utilization
3. **Service Separation**: Each service has a single responsibility
4. **Resource Management**: Proper cleanup and resource lifecycle management
5. **Error Isolation**: Errors in one session don't affect others

## Usage

### Testing the New Architecture

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OpenAI API key

# Run the test script
python test_realtime_agent.py
```

### Creating a Conversation Session

```python
from agents.realtime_agent import RealtimeAgent

# Create agent
agent = RealtimeAgent("session_123", "user_456")

# Start conversation
await agent.start_conversation(
    topic="English practice",
    mode="free_topic"
)

# Stop when done
await agent.stop_conversation()
```

## Future Extensions

The architecture is designed to easily accommodate future features:

### Database Integration
- Add persistence services to save sessions, transcripts, and feedback
- Implement user management and progress tracking

### Feedback Engine
- Extend `ConversationService` to analyze conversations
- Add scoring for the 6 language pillars
- Generate personalized homework and recommendations

### API Layer
- Add FastAPI endpoints for session management
- Implement WebSocket endpoints for real-time communication
- Create REST APIs for user management and analytics

### Additional Agents
- **StandardAgent**: For text-based exercises and homework
- **FeedbackAgent**: For conversation analysis and scoring
- **HomeworkAgent**: For generating and managing assignments

## Error Handling

The architecture includes comprehensive error handling:

- **Service Level**: Each service handles its own errors gracefully
- **Agent Level**: Agent coordinates error recovery across services
- **Session Level**: Session state is preserved during recoverable errors
- **Logging**: Structured logging for debugging and monitoring

## Development Guidelines

1. **Service Independence**: Services should not directly depend on each other
2. **Session Isolation**: All session data should be contained in SessionState
3. **Async First**: Use async/await for all I/O operations
4. **Error Propagation**: Let errors bubble up to the agent level for handling
5. **Resource Cleanup**: Always implement proper cleanup in finally blocks

## Testing

The `test_realtime_agent.py` script demonstrates:
- Session creation and management
- Audio stream handling
- WebSocket communication
- Graceful shutdown
- Error handling

This replicates the exact functionality of the original POC but with the new modular architecture.
