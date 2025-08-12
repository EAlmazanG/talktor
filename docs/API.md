# Talktor API Reference (v1)

Audience: developers and LLMs. This document standardizes endpoint paths, request/response schemas, and the realtime WebSocket protocol.

- Base URL (dev): `http://localhost:8000`
- API version prefix: `/api/v1`
- Auth: none by default (dev). Provide `user_id` with each request.
- Content-Type: `application/json` (unless WebSocket)

Key resources
- Conversations: create/start, realtime voice via WebSocket, end, details, transcript
- Feedback: fetch full object, summary, trigger generation (placeholder)
- Sessions: list user sessions

See also: `docs/CONTEXT_REPOSITORY.md`, `docs/ARCHITECTURE.md`.

## Conventions

- `user_id` is a string that identifies the user. In dev mode pass it in the JSON body for REST endpoints.
- Identifiers:
  - `session_id`: UUID
- Timestamps are ISO-8601 strings unless otherwise stated.
- Errors follow FastAPI's default error schema: `{ "detail": "..." }`.

## Conversations

### Start a conversation
- POST `/api/v1/conversations/start`

Request
```json
{
  "user_id": "user_123",           
  "topic": "English practice",     
  "mode": "FREE_TOPIC",           
  "agent_type": "REALTIME"        
}
```
Notes
- `mode` enum: `FREE_TOPIC`, `REVIEW_PREVIOUS`, `SITUATIONAL`, `DYNAMIC`, `CHALLENGE`
- `agent_type` enum: `REALTIME`, `STANDARD`

Response 200
```json
{
  "session_id": "e5f9c07c-9a4e-4b77-9a1e-6a1a9c9f9a2e",
  "user_id": "user_123",
  "agent_type": "REALTIME",
  "mode": "FREE_TOPIC",
  "created_at": "2025-08-12T12:00:01Z"
}
```

### Realtime conversation (WebSocket)
- WS `ws://localhost:8000/api/v1/conversations/{session_id}/realtime?user_id=user_123`

Behaviour
- Full duplex bridge to OpenAI Realtime API via the backend.
- Natural barge-in supported: when speech is detected, server cancels current AI response and clears TTS playback.
- Server may finalize the session on end-phrases.

Client → Server messages (JSON)
- Append audio chunk (base64-encoded 16kHz, 16-bit PCM, mono)
```json
{ "type": "input_audio_buffer.append", "audio": "<base64>" }
```
- Commit appended audio for processing
```json
{ "type": "input_audio_buffer.commit" }
```
- Send a text message instead of audio (optional)
```json
{ "type": "input_text", "text": "Hello!" }
```

Server → Client messages (JSON)
- Incremental transcript
```json
{ "type": "transcript.delta", "text": "...partial..." }
```
- Final transcript segment
```json
{ "type": "transcript.final", "text": "...complete segment..." }
```
- Clear any pending playback (barge-in)
```json
{ "type": "playback.clear", "reason": "speech_started" }
```
- Generic error
```json
{ "type": "error", "message": "..." }
```
- Session finalized (connection may close shortly after)
```json
{ "type": "session.finalized" }
```

Python example (simplified)
```python
import asyncio, json, websockets, base64

async def run(session_id, user_id, wav_bytes):
    url = f"ws://localhost:8000/api/v1/conversations/{session_id}/realtime?user_id={user_id}"
    async with websockets.connect(url) as ws:
        # send audio chunk
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(wav_bytes).decode()
        }))
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        # read events
        async for msg in ws:
            evt = json.loads(msg)
            if evt.get("type") == "transcript.delta":
                print(evt["text"], end="", flush=True)
```

### End a conversation
- POST `/api/v1/conversations/{session_id}/end`

Request
```json
{ "user_id": "user_123" }
```

Response 200 (summary)
```json
{
  "session_id": "...",
  "message_count": 23,
  "duration_seconds": 312.4,
  "has_feedback": true,
  "overall_score": 7.8,
  "closed_at": "2025-08-12T12:10:33Z"
}
```

### Get conversation details
- GET `/api/v1/conversations/{session_id}`

Response 200
```json
{
  "session_id": "...",
  "user_id": "user_123",
  "agent_type": "REALTIME",
  "mode": "FREE_TOPIC",
  "message_count": 23,
  "total_cost": 0.015,
  "total_tokens": 1842,
  "created_at": "...",
  "updated_at": "..."
}
```

### Get transcript
- GET `/api/v1/conversations/{session_id}/transcript`

Response 200
```json
{
  "session_id": "...",
  "messages": [
    { "speaker": "user", "text": "Hi!", "ts": 1723456.12 },
    { "speaker": "assistant", "text": "Hello!", "ts": 1723457.45 }
  ]
}
```

## Feedback

### Get feedback for a session
- GET `/api/v1/feedback/{session_id}`

Response 200 (abbreviated)
```json
{
  "session_id": "...",
  "overall_score": 7.8,
  "general_feedback": "Great job maintaining the conversation.",
  "general_errors": ["..."],
  "general_suggestions": ["..."],
  "pronunciation": {
    "score": 7.0,
    "summary": "Mostly clear.",
    "errors": ["..."],
    "suggestions": ["..."]
  },
  "fluency": { "score": 7.5, "summary": "", "errors": [], "suggestions": [] },
  "grammar": { "score": 7.2, "summary": "", "errors": [], "suggestions": [] },
  "expressions": { "score": 7.9, "summary": "", "errors": [], "suggestions": [] },
  "vocabulary": { "score": 7.6, "summary": "", "errors": [], "suggestions": [] },
  "comprehension": { "score": 8.2, "summary": "", "errors": [], "suggestions": [] },
  "generated_by": "standard_agent",
  "created_at": "..."
}
```

### Get feedback summary
- GET `/api/v1/feedback/{session_id}/summary`

Response 200
```json
{
  "session_id": "...",
  "overall_score": 7.8,
  "pillar_scores": {
    "pronunciation": 7.0,
    "fluency": 7.5,
    "grammar": 7.2,
    "expressions": 7.9,
    "vocabulary": 7.6,
    "comprehension": 8.2
  }
}
```

### Trigger feedback generation (placeholder)
- POST `/api/v1/feedback/{session_id}/generate`

Request
```json
{ "user_id": "user_123" }
```

Response 200 (current placeholder)
```json
{ "status": "pending", "message": "Generation not yet implemented" }
```

## Sessions

### List sessions for a user
- GET `/api/v1/users/{user_id}/sessions`

Response 200
```json
{
  "user_id": "user_123",
  "sessions": [
    {
      "session_id": "...",
      "created_at": "...",
      "message_count": 23,
      "has_feedback": true,
      "overall_score": 7.8
    }
  ]
}
```

## Status Codes
- 200 OK – Success
- 201 Created – Resource created
- 202 Accepted – Async operation started (future use)
- 400 Bad Request – Validation error
- 401 Unauthorized – If auth is later enabled
- 404 Not Found – Resource not found
- 500 Internal Server Error – Unexpected error

## Realtime Client & Utilities
- Example client: `scripts/interactive_audio_ws_client.py`
- Logs viewer: `scripts/dev/view_logs.py`

## Notes
- This API is designed to be straightforward to call from LLM tools. Prefer explicit request schemas, stable field names, and idempotent GET endpoints.
- The realtime protocol forwards and mirrors upstream events from OpenAI as needed. Unknown event types should be ignored gracefully by clients.
