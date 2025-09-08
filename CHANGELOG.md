# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.1.0] - 2025-09-08

### Added
- Realtime conversation pipeline (WebSocket) bridging to OpenAI Realtime:
  - Binary PCM16 24kHz mono audio, `audio_commit`, and natural barge-in.
  - AI audio streamed back as binary frames, with `audio.delta.b64` fallback.
  - Explicit feedback request on end phrases or `end` command; 6s safety finalize.
  - Streaming transcripts for user and AI with delta/completed events.
- REST API v1 endpoints (FastAPI):
  - Conversations: start, realtime (WS), end, details, transcripts.
  - Feedback: get full object, get summary, manual generate (placeholder in v0.1).
  - Users: sessions, progress, stats. Root and /health endpoints.
- Structured feedback system (single row per session):
  - Overall score and 6 pillars (pronunciation, fluency, grammar, expressions, vocabulary, comprehension) with scores, summaries, errors, suggestions.
  - Columns migrated to English; table redesigned to a comprehensive single record per session.
  - Feedback generation via StandardAgent (GPT‑4o) and explicit request in realtime flow.
- Persistence layer & database:
  - SQLAlchemy models, CRUD, and `PersistenceService` with transactional operations.
  - Migration utilities for feedback columns/table redesign.
- Logging system:
  - Dual output (console + timestamped files under `logs/`), CLI tools to list/search/tail/follow.
- Dev & Ops:
  - `docker-compose.yml` (prod on localhost) and `docker-compose.dev.yml` (DB + pgAdmin + optional frontend).
  - Backend/Frontend Dockerfiles, `.env.example`, and scripts (`dev_start.sh`, `dev_stop.sh`, `prod_start.sh`, `prod_stop.sh`).
- Frontend (Next.js):
  - Minimal UI with Practice (realtime), Learn (sessions/feedback), Progress (charts), Config (user ID).
  - Components: `FeedbackDetails`, `MiniLineChart`, `AiRadialVisualizer`.
  - REST and WebSocket helpers (`api.ts`, `ws.ts`).
- Utilities & examples:
  - `scripts/interactive_audio_ws_client.py` microphone streaming client.

### Changed
- Simplified and centralized prompt logic for feedback/end flow; moved logic to code paths.
- Refactor: prompts consolidated; standard agent imports cleaned up.

### Documentation
- Comprehensive docs under `docs/`: PRD, ARCHITECTURE, API, FRONTEND, CONTEXT_REPOSITORY.
- README revamped with banner, quickstart TL;DR, and screenshots.

