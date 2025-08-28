# Talktor – Repository Context (Canonical)

Purpose: This document provides a concise, standardized overview of the repository structure, architecture, runtime conventions, and data model. It is written to be easily consumed by both developers and LLMs.

- Tech stack: FastAPI, PostgreSQL, SQLAlchemy, OpenAI (Realtime + GPT-4o), Async Python
- Core capabilities: Real-time voice conversations, transcript storage, structured feedback across 6 pillars, homework/vocabulary generation, centralized logging
- Key docs: `docs/CONTEXT_REPOSITORY.md` (this file), `docs/ARCHITECTURE.md`, `docs/API.md`

## Repository Layout

Root
```
├── .env                         # Environment variables (not in git)
├── .gitignore                   # Git ignores
├── LICENSE                      # License
├── README.md                    # Project intro
├── docker-compose.yml           # Production Docker stack
├── docker-compose.dev.yml       # Development DB/pgAdmin stack
├── docs/                        # Documentation
│   ├── CONTEXT_REPOSITORY.md    # Repository context (EN, canonical)
│   ├── CONTEXT_REPOSITORY.es.md # Repository context (ES, legacy)
│   ├── ARCHITECTURE.md          # Backend architecture
│   └── API.md                   # API reference (v1)
├── backend/                     # Backend code
├── frontend/                    # Frontend (placeholder)
├── scripts/                     # Scripts
│   ├── dev/                     # Developer utilities
│   │   ├── view_logs.py
│   │   └── demo_logging.py
│   └── ops/                     # Operational helpers
│       ├── dev_start.sh         # Uses .venv exclusively
│       ├── dev_stop.sh
│       ├── prod_start.sh
│       └── prod_stop.sh
├── tests/                       # Root-level tests (currently minimal)
├── logs/                        # Centralized logs (created at runtime)
├── .venv/                       # Preferred Python virtualenv (ignored)
└── talktor-env/                 # Legacy virtualenv (unused)
```

Backend
```
backend/
├── core/                        # Cross-cutting concerns
│   ├── config.py                # Pydantic Settings (env-based)
│   ├── logging.py               # Structured logging (console + files)
│   ├── log_utils.py             # Log management/search helpers
│   └── colors.py                # Terminal color helpers
├── services/                    # Business logic & orchestration
│   ├── session_state.py         # SessionState + SessionManager
│   ├── audio_service.py         # Mic/speaker handling (PyAudio)
│   ├── openai_service.py        # Realtime API bridge (WebSocket)
│   ├── conversation_service.py  # Conversation logic & function calls
│   ├── conversation_flow.py     # End-to-end flow (analysis/feedback)
│   └── persistence_service.py   # Transactional DB operations
├── agents/
│   ├── realtime_agent.py        # Voice conversation orchestrator
│   └── standard_agent.py        # GPT-4o for analysis/feedback
├── db/
│   ├── models.py                # SQLAlchemy models (sessions, transcripts, feedback, homework, vocabulary)
│   ├── database.py              # DB engine/session config
│   ├── crud.py                  # CRUD utilities
│   └── migrations/              # DB migration utilities/scripts
├── api/
│   └── v1/                      # Implemented endpoints (conversations, feedback, sessions, users)
├── schemas/                     # Pydantic DTOs (as applicable)
├── tests/                       # Backend tests
│   ├── test_realtime_agent.py
│   ├── test_standard_agent.py
│   ├── test_database.py
│   ├── test_persistence_service.py
│   ├── test_config_validation.py
│   ├── test_complete_flow.py
│   ├── test_real_voice_conversation.py
│   ├── test_simple_flow.py
│   ├── test_termination_commands.py
│   ├── test_feedback_generation.py
│   └── test_feedback_english_columns.py
├── main.py                      # FastAPI app & router registration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Backend image
└── start.sh                     # Container entrypoint
```

## Development Conventions

- Virtualenv: `.venv/` required. Scripts in `scripts/ops/` use `.venv` exclusively; no fallback.
- Logs: All services write to the repository-root `logs/` directory via `backend/core/logging.py`.
- Migrations: Keep migration utilities in `backend/db/migrations/`.
- Scripts: Developer tools in `scripts/dev/`; operational helpers in `scripts/ops/`.

Quickstart
```
# 1) Create & activate venv (recommended)
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 2) Start dev services (DB + backend; uvicorn runs in background)
./scripts/ops/dev_start.sh

# 3) (Optional) Run the backend manually instead of step 2
# From repo root with .venv active:
uvicorn backend.main:app --reload --port 8000

# 4) Run tests
pytest backend/tests -q
```

Required environment variables (example)
```
# OpenAI
OPENAI_API_KEY=

# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=

# pgAdmin
PGADMIN_DEFAULT_EMAIL=
PGADMIN_DEFAULT_PASSWORD=
```

## Logging System

- Dual output: console (developer-friendly) + file (detailed with function:line)
- File naming: `YYYYMMDD_HHMMSS_service.log`
- Root log directory: `logs/` (created automatically)

Setup snippet
```python
from core.logging import setup_logging

setup_logging(
    level="DEBUG",
    enable_file_logging=True,
    log_directory="logs",
    service_name="backend"
)
```

CLI utilities
```
# List log files
python scripts/dev/view_logs.py --list

# Tail latest log
python scripts/dev/view_logs.py --tail 50

# Search across logs
python scripts/dev/view_logs.py --search "error"

# Follow a log
python scripts/dev/view_logs.py --follow
```

## Data Model Summary

Sessions
- session_id (UUID), user_id (str), agent_type (REALTIME|STANDARD), conversation_mode (FREE_TOPIC|REVIEW_PREVIOUS|SITUATIONAL|DYNAMIC|CHALLENGE)
- duration_seconds (float), message_count (int), total_cost (float), total_tokens (int)
- created_at, updated_at

Transcripts
- transcript_id (UUID), session_id (UUID FK), conversation_json (JSON, structured messages with timestamps), created_at

Feedback (one row per session)
- id (int), session_id (int, unique)
- overall_score (float)
- general_feedback (text), general_errors (JSON[]), general_suggestions (JSON[])
- pronunciation_[score, summary, errors, suggestions]
- fluency_[score, summary, errors, suggestions]
- grammar_[score, summary, errors, suggestions]
- expressions_[score, summary, errors, suggestions]
- vocabulary_[score, summary, errors, suggestions]
- comprehension_[score, summary, errors, suggestions]
- created_at, generated_by

Homework Items
- homework_id (UUID), session_id (UUID FK), category, title, description, difficulty, estimated_time, priority, created_at

Vocabulary Items
- vocabulary_id (UUID), session_id (UUID FK), word, definition, example_sentence, difficulty, created_at

## Implemented Features

RealtimeAgent (voice)
- OpenAI Realtime API bridge (WebSocket)
- Full duplex audio, natural barge-in, transcript assembly
- Clean session lifecycle and persistence

StandardAgent (analysis/feedback)
- 6-pillar feedback, homework & exercises, advice
- Flashcards planned

PersistenceService (DB operations)
- Transactional operations, centralized error handling, structured logging

Structured transcripts
- Individual messages with timestamps in chronological order
- JSON storage (no concatenation)

Robust configuration
- Centralized environment-based settings with validation

## Data Flow
```
User (voice/text)
  → RealtimeAgent
  → ConversationService (state management)
  → ConversationFlow (analysis & feedback)
  → PersistenceService (transactional writes)
  → PostgreSQL
```

## API Surface

Implemented, versioned under `/api/v1`.
- Conversations: start, realtime (WebSocket), end, get details, get transcript
- Feedback: get, summary, generate (placeholder)
- Sessions: list user sessions

See `docs/API.md` for detailed request/response schemas and WebSocket protocol.

## Known Gaps / Next Steps
- Implement full feedback generation for `POST /api/v1/feedback/{session_id}/generate` using StandardAgent + PersistenceService
- Frontend integration to consume REST + WebSocket APIs
- Realtime client polish (reconnection/backpressure)
- Auth and user management (as needed)

## Migrations & Notable Changes

January 2025 – Feedback columns renamed to English
- All column names migrated to English across model/CRUD/services and DB
- Script: `backend/db/migrations/migrate_feedback_columns_to_english.py`
- Verified by tests: feedback creation/retrieval across all 6 pillars
