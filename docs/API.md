# Talktor API Reference (v1)

Audience: developers and LLMs. This document standardizes endpoint paths, request/response schemas, and the realtime WebSocket protocol.

- Base URL (dev): `http://localhost:8000`
- API version prefix: `/api/v1`
- Auth: none by default (dev). Provide the user via the `X-User-Id` header on REST requests. If missing in dev, it defaults to `default_user`.
- Content-Type: `application/json` (unless WebSocket)

Key resources
- Conversations: create/start, realtime voice via WebSocket, end, details, transcript
- Feedback: fetch full object, summary, trigger generation (placeholder)
- Sessions: list user sessions

See also: `docs/CONTEXT_REPOSITORY.md`, `docs/ARCHITECTURE.md`.

## Conventions

- `user_id` is a string that identifies the user. In dev mode pass it in the `X-User-Id` header for REST endpoints. The WebSocket endpoint does not require it (user is derived from the session).
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
  "session_id": "optional-predefined-session-id"
}
```
Notes
- Defaults (current behavior): `agent_type=REALTIME`, `mode=FREE_TOPIC`.
- Additional fields are not currently accepted by this endpoint.

Response 200
```json
{
  "session_id": "e5f9c07c-9a4e-4b77-9a1e-6a1a9c9f9a2e",
  "status": "started",
  "websocket_url": "/api/v1/conversations/e5f9c07c-9a4e-4b77-9a1e-6a1a9c9f9a2e/realtime"
}
```

### Realtime conversation (WebSocket)
- WS `ws://localhost:8000/api/v1/conversations/{session_id}/realtime`

Behaviour
- Full duplex bridge to OpenAI Realtime API via the backend.
- Natural barge-in supported: when speech is detected, server cancels current AI response and clears TTS playback.
- Server may finalize the session on end-phrases.

Client → Server
- JSON control/messages and optional raw binary audio frames
- Append audio chunk (base64-encoded 24kHz, 16-bit PCM, mono)
```json
{ "type": "input_audio_buffer.append", "audio": "<base64>" }
```
- Alternatively, send raw binary audio frames (PCM16 24kHz mono)
  - Send bytes directly over the WebSocket; the server base64-encodes and forwards upstream equivalently to `input_audio_buffer.append`.
- Commit appended audio for processing
```json
{ "type": "audio_commit" }
```
  - The server forwards this upstream as `input_audio_buffer.commit`.
- End the session explicitly
```json
{ "type": "end" }
```
- Send a text message instead of audio (optional)
```json
{ "type": "input_text", "text": "Hello!" }
```
- Plain text (non-JSON) is also supported
  - Sending `"end"`, `"stop"`, or `"finish"` as a plain string ends the session.
  - Any other plain string is treated as user text and forwarded upstream.

Server → Client messages (JSON)
- Session created upstream
```json
{ "type": "session.created" }
```
- Incremental user transcript (from user speech)
```json
{ "type": "user_transcript.delta", "delta": "...partial..." }
```
- Final user transcript segment
```json
{ "type": "user_transcript.completed", "transcript": "...complete segment..." }
```
- Incremental AI transcript (from AI speech)
```json
{ "type": "ai_transcript.delta", "delta": "...partial..." }
```
- Final AI transcript segment
```json
{ "type": "ai_transcript.completed", "transcript": "...complete segment..." }
```
- Clear any pending playback (barge-in)
```json
{ "type": "playback.clear", "reason": "speech_started" }
```
  - Possible reasons: `speech_started`, `end_phrase`, `client_end`.
- AI audio stream (binary)
  - The server streams AI audio as raw binary frames (PCM16 24kHz, mono).
  - In rare cases where binary send fails, a fallback is emitted:
```json
{ "type": "audio.delta.b64", "delta": "<base64-bytes>" }
```
- Generic upstream event (for unrecognized passthroughs)
```json
{ "type": "upstream", "event": "<upstream_event_type>" }
```
- Generic error
```json
{ "type": "error", "payload": { "message": "..." } }
```
- Session ended (emitted before close)
```json
{
  "type": "ended",
  "session_id": "...",
  "duration_seconds": 312,
  "message_count": 23,
  "status": "ended",
  "feedback_generated": true
}
```

Python example (simplified)
```python
import asyncio, json, websockets, base64

async def run(session_id, wav_bytes):
    url = f"ws://localhost:8000/api/v1/conversations/{session_id}/realtime"
    async with websockets.connect(url) as ws:
        # Option A: send JSON base64 audio
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(wav_bytes).decode()
        }))
        await ws.send(json.dumps({"type": "audio_commit"}))

        # Option B: send raw binary frames instead (PCM16 24kHz mono)
        # await ws.send(wav_bytes)
        # await ws.send(json.dumps({"type": "audio_commit"}))

        while True:
            msg = await ws.recv()
            if isinstance(msg, bytes):
                # AI audio bytes; play or buffer as needed
                handle_ai_audio(msg)
                continue
            evt = json.loads(msg)
            if evt.get("type") == "user_transcript.delta":
                print(evt["delta"], end="", flush=True)
            elif evt.get("type") == "ai_transcript.delta":
                print(evt["delta"], end="", flush=True)
            elif evt.get("type") == "ended":
                break
```

### End a conversation
- POST `/api/v1/conversations/{session_id}/end`

Request
Headers
```
X-User-Id: user_123
```
```json
{ "force_feedback": false }
```

Response 200 (summary)
```json
{
  "session_id": "...",
  "duration_seconds": 312,
  "message_count": 23,
  "status": "ended",
  "feedback_generated": true
}
```

### Get conversation details
- GET `/api/v1/conversations/{session_id}`

Response 200
```json
{
  "session_id": "...",
  "user_id": "user_123",
  "duration_seconds": 312,
  "message_count": 23,
  "messages": [
    {
      "role": "user",
      "content": "Hi!",
      "timestamp": "2025-08-12T12:00:03Z",
      "order": 1
    },
    {
      "role": "assistant",
      "content": "Hello!",
      "timestamp": "2025-08-12T12:00:04Z",
      "order": 2
    }
  ],
  "status": "ended",
  "started_at": "2025-08-12T12:00:01Z",
  "ended_at": "2025-08-12T12:10:33Z"
}
```

### Get transcripts
- GET `/api/v1/conversations/{session_id}/transcripts`

Response 200
```json
[
  {
    "session_id": "...",
    "speaker": "user",
    "content": "Hi!",
    "sequence_number": 1,
    "timestamp": "2025-08-12T12:00:03Z",
    "confidence_score": 0.98,
    "audio_duration": 1.23
  },
  {
    "session_id": "...",
    "speaker": "assistant",
    "content": "Hello!",
    "sequence_number": 2,
    "timestamp": "2025-08-12T12:00:04Z",
    "confidence_score": 1.0,
    "audio_duration": 0.95
  }
]
```

## Feedback

### Get feedback for a session
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
  "general_summary": "...",
  "generated_by": "standard_agent",
  "created_at": "..."
}
```

### Get feedback summary
```json
{
  "session_id": "...",
  "overall_score": 7.8,
  "general_summary": "...",
  "pillar_scores": {
    "pronunciation": 7.0,
    "fluency": 7.5,
    "grammar": 7.2,
    "expressions": 7.9,
    "vocabulary": 7.6,
    "comprehension": 8.2
  },
  "created_at": "..."
}
```

### Trigger feedback generation (placeholder)
- POST `/api/v1/feedback/{session_id}/generate`

Request
```json
{ "session_id": "...", "force_generation": false }
```

Response 200 (current placeholder)
```json
{
  "message": "Feedback generation triggered successfully",
  "data": { "session_id": "...", "status": "processing" }
}
```

## Sessions

### List sessions for a user
- GET `/api/v1/users/{user_id}/sessions`

Response 200
```json
{
  "sessions": [
    {
      "session": {
        "session_id": "...",
        "user_id": "user_123",
        "agent_type": "REALTIME",
        "mode": "FREE_TOPIC",
        "duration_seconds": 312,
        "token_count": null,
        "estimated_cost": null,
        "started_at": "...",
        "ended_at": "...",
        "status": "ended",
        "notes": null
      },
      "message_count": 23,
      "has_feedback": true,
      "feedback_score": 7.8
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### Get user progress
- GET `/api/v1/users/{user_id}/progress`

Response 200
```json
{
  "user_id": "user_123",
  "total_sessions": 10,
  "average_score": 7.6,
  "latest_session_date": "...",
  "pillar_averages": {
    "pronunciation": 7.2,
    "fluency": 7.4,
    "grammar": 7.0,
    "expressions": 7.8,
    "vocabulary": 7.5,
    "comprehension": 8.0
  },
  "improvement_areas": ["grammar"],
  "strengths": ["comprehension", "expressions"]
}
```

### Get user stats
- GET `/api/v1/users/{user_id}/stats`

Response 200
```json
{
  "user_id": "user_123",
  "total_sessions": 10,
  "average_score": 7.6,
  "latest_session_date": "...",
  "recent_sessions_count": 5,
  "pillar_averages": { "pronunciation": 7.2, "fluency": 7.4 },
  "has_recent_activity": true,
  "learning_streak": 0
}
```

## Status Codes
- 200 OK – Success
- 201 Created – Resource created
- 202 Accepted – Async operation started (future use)
- 400 Bad Request – Validation error
- 401 Unauthorized – If auth is later enabled
- 403 Forbidden – Access denied (e.g., viewing other users' data)
- 404 Not Found – Resource not found
- 409 Conflict – Resource state conflict (e.g., feedback already exists)
- 500 Internal Server Error – Unexpected error

## Realtime Client & Utilities
- Example client: `scripts/interactive_audio_ws_client.py`
- Logs viewer: `scripts/dev/view_logs.py`

## Notes
- This API is designed to be straightforward to call from LLM tools. Prefer explicit request schemas, stable field names, and idempotent GET endpoints.
- The realtime protocol forwards and mirrors upstream events from OpenAI as needed. Unknown event types should be ignored gracefully by clients.
