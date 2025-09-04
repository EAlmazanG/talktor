# Talktor Frontend Overview

This document describes the architecture, structure, and usage of the Talktor frontend application. It complements `docs/ARCHITECTURE.md` and `docs/API.md` with a focus on the web UI and client integration.

- App type: Next.js (App Router) + React + TypeScript
- Styling: Tailwind CSS v4
- Linting: ESLint (Next.js config), Prettier (via Next defaults)
- Runtime: Dev at http://localhost:3000 (proxy to backend at http://localhost:8000)

## Tech Stack

- React 19, Next.js 15 (App Router)
- TypeScript (strict)
- Tailwind CSS v4 (via `@tailwindcss/postcss`)
- Node and npm (see `frontend/package.json` for scripts)

## Project Location & Structure

Frontend lives under `frontend/`:

```
frontend/
├── .env.local                        # Frontend environment (see below)
├── package.json                      # Scripts: dev, build, start, lint
├── postcss.config.mjs                # Tailwind v4 PostCSS plugin
├── src/
│   ├── app/
│   │   ├── layout.tsx               # Root layout incl. top TabNav
│   │   ├── globals.css              # Tailwind import and theme vars
│   │   ├── page.tsx                 # Redirects to /practice
│   │   ├── practice/page.tsx        # Realtime conversation UI
│   │   ├── learn/page.tsx           # Sessions list
│   │   ├── learn/feedback/[sessionId]/page.tsx  # Feedback details view
│   │   ├── progress/page.tsx        # Progress analytics & charts
│   │   └── config/page.tsx          # Local user settings
│   ├── components/
│   │   ├── TabNav.tsx               # Top tabs (Practice/Learn/Progress/Config)
│   │   ├── MiniLineChart.tsx        # Lightweight SVG line chart used on Progress
│   │   ├── FeedbackDetails.tsx      # Reusable full feedback UI (general + pillars)
│   │   └── AiRadialVisualizer.tsx   # AI audio radial visualizer (Practice)
│   └── lib/
│       ├── api.ts                   # REST helpers
│       └── ws.ts                    # WebSocket helper
└── tsconfig.json                     # Path alias `@/*` -> `src/*`
```

## Environment

Frontend reads a single env var:

- `NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`)
  - Used for REST calls and as base to derive `ws://` or `wss://` for realtime.
  - Configure in `frontend/.env.local`.

Example:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Commands

From `frontend/` directory:

- `npm run dev` – Start Next dev server (Turbopack) at http://localhost:3000
- `npm run build` – Build the production bundle
- `npm start` – Run the production server
- `npm run lint` – Run ESLint

## Navigation & Pages

- `src/components/TabNav.tsx`
  - Provides top-level tabs with labels and compact SVG icons:
    - 🟢 Practice (`/practice`)
    - 🔵 Learn (`/learn`)
    - 🟣 Progress (`/progress`)
    - ⚙️ Config (`/config`)
  - Highlights the active tab (supports nested routes).

- `src/app/layout.tsx`
  - Global layout, imports `TabNav`, sets metadata (title/description/icons), and main container.
  - Favicon and Apple touch icon are set via `metadata.icons` to Talktor assets at `public/assets/icons/`.

- `src/app/page.tsx`
  - Redirects to `/practice` by default.

### Practice: Realtime Conversation
File: `src/app/practice/page.tsx`

- Start conversation (POST `/api/v1/conversations/start`).
- Connect to returned `websocket_url` using `ws.ts` helper.
- Send user messages as text JSON: `{ type: "input_text", text }`.
- End session (POST `/api/v1/conversations/{session_id}/end` or `{ type: "end" }` over WS).
- Displays incremental transcripts:
  - `user_transcript.delta` / `user_transcript.completed`
  - `ai_transcript.delta` / `ai_transcript.completed`
- On session end, fetches feedback summary: GET `/api/v1/feedback/{session_id}/summary`.

Notes:
- Current UI streams text only. Audio streaming (PCM16 24kHz mono) can be added later by sending raw binary frames and committing with `{ type: "audio_commit" }` per `docs/API.md`.
- Bottom-right status panel shows WebSocket/mic/ended status, current session id, and active user id.
- After session end, the page shows the feedback summary and a "Show details" toggle that fetches full feedback (`GET /api/v1/feedback/{session_id}`) and renders `FeedbackDetails` inline.

### Learn: Sessions & Feedback Summary
Files:
- `src/app/learn/page.tsx` – Lists sessions for the current user.
- `src/app/learn/feedback/[sessionId]/page.tsx` – Shows full structured feedback (general + per-pillar) using `FeedbackDetails`.

Endpoints:
- GET `/api/v1/users/{user_id}/sessions`
- GET `/api/v1/feedback/{session_id}/summary`
- GET `/api/v1/feedback/{session_id}`

UI notes:
- Minimal, modern table with the following columns only: Started, Duration, Feedback (badge with optional score), Actions (View details).
- Collapsible view shows the latest items, with a "Show all" button to expand and paginate. A Refresh action is provided.

### Progress: Analytics & Charts
File: `src/app/progress/page.tsx`
- Displays analytics over the last N days (7/14/30 toggle) with:
  - Overall evolution chart (0–10 scale)
  - Six pillar charts: pronunciation, fluency, grammar, expressions, vocabulary, comprehension
- Charts use `MiniLineChart` with a lightweight SVG implementation and shared theming.
- Axis label styling is tuned per design:
  - Overall chart uses thinner weight, smaller size, and lower opacity labels for a subtle look.
  - Pillar charts use larger axis labels for readability.
- Data pipeline:
  - Loads all user sessions via `getAllUserSessions()` and per-session summaries via `getFeedbackSummary()`.
  - Aggregates per-day averages and renders points within the selected date range.
  - Includes a Refresh action and section pills for visual hierarchy.

### Config: Local User Settings
File: `src/app/config/page.tsx`
- Simplified, consistent UI with a section pill header and a subtle, bordered card.
- Allows setting the current `userId` (saved to `localStorage`).
- REST helpers attach the `X-User-Id` header for the active user.

## REST & WebSocket Helpers

- `src/lib/api.ts`
  - `getApiBaseUrl()` – Resolves base from env.
  - `getUserId()` – Reads from `localStorage` or defaults to `default_user`.
  - `startConversation()` – POST `/api/v1/conversations/start`
  - `endConversation(sessionId)` – POST `/api/v1/conversations/{id}/end`
  - `getFeedbackSummary(sessionId)` – GET `/api/v1/feedback/{id}/summary`
  - `getFeedback(sessionId)` – GET `/api/v1/feedback/{id}` (full structured feedback)
  - `getUserSessions(userId?)` – GET `/api/v1/users/{user_id}/sessions`
  - `getAllUserSessions(userId?, pageSize?)` – Helper to fetch and merge all session pages

- `src/lib/ws.ts`
  - `openRealtimeWebSocket(websocketUrl, listeners)` – Connects and dispatches events:
    - Handles JSON events: `user_transcript.delta`, `user_transcript.completed`, `ai_transcript.delta`, `ai_transcript.completed`, `playback.clear`, `ended`, and a generic passthrough.
    - Handles binary AI audio frames (emitted by the server); consumer can play or buffer.
  - Utilities: `sendText()`, `sendJson()`, `end()`, `close()`.

## UI Components

- `MiniLineChart` (`src/components/MiniLineChart.tsx`)
  - Minimal SVG line chart with no external deps.
  - Key props: `points`, `yDomain`, `xDomain`, `heightPx`, `axisMode`, `axisOpacity`, `autoY`, `yPadding`, `minYRange`.
  - Axis label styling props (new):
    - `axisLabelWeightClass` – override font weight (e.g., `font-thin`).
    - `axisLabelOpacity` – control text opacity (default `0.42`).
    - `axisLabelSizeClass` – Tailwind size classes (default `text-[7px] md:text-[9px]`).
  - Used on the Progress page for overall and per-pillar charts.

- `FeedbackDetails` (`src/components/FeedbackDetails.tsx`)
  - Renders full structured feedback: overall summary/assessment and six pillar sections (scores, summaries, errors, suggestions).
  - Input type: `FeedbackResponse` with nested `PillarFeedback` (see `src/lib/api.ts`).
  - Used on Learn (details page) and Practice (Show/Hide details toggle after session end).

- `TabNav` (`src/components/TabNav.tsx`)
  - Compact SVG icons, active tab highlighting, and brand logo.

- `AiRadialVisualizer` (`src/components/AiRadialVisualizer.tsx`)
  - Displays the AI audio level as a radial animation on Practice.

## Identity & Headers

- Active user is stored under `localStorage["userId"]`.
- All REST calls attach `X-User-Id` automatically.
- The WebSocket endpoint does not require the header (user is derived from the session).

## Styling

- Tailwind v4 is imported in `src/app/globals.css` using `@import "tailwindcss";`.
- Global CSS defines basic CSS variables for foreground/background and fonts.

## Conventions & Code Quality

- TypeScript strict mode (see `tsconfig.json`).
- Path alias: `@/*` maps to `src/*` for clean imports.
- Linting via `eslint.config.mjs` and `eslint-config-next`.
- All code and comments are in English.

## Troubleshooting

- Backend not reachable: ensure FastAPI is running at `http://localhost:8000` and `/health` returns healthy.
- CORS/WS issues: backend CORS is configured permissively for development; verify network policies and `NEXT_PUBLIC_API_BASE_URL`.
- Empty sessions in Learn: verify the same user ID is set in Config and used during Practice.
- WebSocket drops: check backend logs and that `websocket_url` resolves to `ws://<host>/...` (or `wss://` when using HTTPS).

## Future Enhancements

- Microphone capture and audio streaming (PCM16 24kHz mono), plus audio playback of AI responses.
- Conversation transcripts view and per-message feedback.
- Progress dashboards with pillar trends and recommendations.
- Homework, flashcards, and personalized advice under Learn.

## References

- API: `docs/API.md`
- Backend Architecture: `docs/ARCHITECTURE.md`
- Repository Context: `docs/CONTEXT_REPOSITORY.md`
