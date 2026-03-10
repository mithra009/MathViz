# MathViz — AI-Powered Mathematical Animation Service

Convert natural language descriptions into mathematical animations using [Manim](https://www.manim.community/) and Mistral AI. Type a prompt, get an MP4.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Docker](#docker)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

MathViz accepts a plain-English description of a mathematical concept (e.g. *"animate the Fourier series approximation of a square wave"*) and returns a rendered MP4. The backend uses **Mistral Large** to generate Manim Python code, executes it in a sandboxed environment, and if rendering fails it feeds the error back to the LLM for self-correction — repeating up to three times. Completed videos are persisted in **Supabase Storage** and their metadata is written to a Supabase Postgres database. Job state is tracked in **Upstash Redis**.

---

## Features

| Feature | Details |
|---|---|
| Natural language → animation | Describe any mathematical concept in plain English |
| Self-correcting LLM pipeline | Up to 3 automatic retry attempts with error feedback |
| 2D & 3D scene support | Detects `Scene` and `ThreeDScene` classes automatically |
| Persistent video storage | Uploaded to Supabase Storage with a public CDN URL |
| Job status polling | Redis-backed job tracking with 7-day TTL |
| Legacy code execution | Direct Manim script submission via `/render-code` |
| Containerised & serverless-ready | Runs on Hugging Face Spaces free tier |
| Non-root Docker execution | UID 1000 for HuggingFace Spaces compliance |
| React chat interface | Real-time progress bar, video gallery, and playback |
| Sign in / Sign up | Secure authentication with email/password |
| User video history | View, search, and manage your previously rendered videos |

---

## Tech Stack

**Backend**
- Python 3.10+
- [FastAPI](https://fastapi.tiangolo.com/) — async HTTP framework
- [Manim Community Edition 0.18](https://www.manim.community/) — animation engine
- [Mistral AI](https://mistral.ai/) (`mistral-large-latest`) — code generation & self-correction
- [Upstash Redis](https://upstash.com/) — serverless job state management
- [Supabase](https://supabase.com/) — Postgres database + object storage

**Frontend**
- [React 18](https://react.dev/) + [Vite 5](https://vitejs.dev/)
- [Tailwind CSS 3](https://tailwindcss.com/)
- [Framer Motion](https://www.framer.com/motion/) — animations
- [Axios](https://axios-http.com/) — HTTP client

**Infrastructure**
- Docker (multi-stage build — Node 18 + Python 3.9-slim)
- FFmpeg, Cairo, Pango, LaTeX (texlive-latex-extra)
- Hugging Face Spaces (target deployment)

---

## Architecture

```
User Prompt
    |
    v
React Frontend  --POST /render-->  FastAPI Backend
                                        |
                                        v
                                  Mistral Large
                                  (code generation)
                                        |
                                        v
                                  Manim Renderer
                                  (subprocess)
                                   /        \
                                 OK        Error
                                  |           |
                                  |   <-- LLM self-correction
                                  |       (up to 3 retries)
                                  v
                           Supabase Storage
                           (MP4 upload -> CDN URL)
                                  |
                                  v
                           Supabase Postgres
                           (job metadata)
                                  |
                                  v
                           Upstash Redis
                           (job status, 7-day TTL)
                                  |
                                  v
                        GET /status/{job_id}
                                  |
                                  v
                           React Frontend
                           (video playback)
```

### Six Container Optimisation Constraints

1. **Base image substitution** — `python:3.9-slim` instead of the 4.5 GB official Manim image
2. **Dependency pruning** — minimalist LaTeX (`texlive-latex-extra` only)
3. **Layer consolidation** — single chained `RUN` with aggressive cache cleanup
4. **Strict filesystem redirection** — all I/O in `/tmp`; non-root user UID 1000
5. **Cache suppression** — `--disable_caching` prevents disk exhaustion
6. **Async API orchestration** — instant `202 Accepted` + background task processing

---

## Project Structure

```
manim-image/
├── src/
│   └── manim_service/
│       ├── app.py              # FastAPI application, routes, LLM pipeline
│       └── utils/
│           └── health_check.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── ChatInterface.jsx   # Prompt input & progress bar
│   │       ├── VideoGallery.jsx    # Rendered video list
│   │       ├── SingleVideoPlayer.jsx
│   │       └── Tooltip.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── database/
│   └── supabase_schema.sql     # Postgres table definitions
├── docker/
│   └── Dockerfile              # Multi-stage build
├── scripts/
│   ├── start_server.ps1        # Windows dev launcher
│   └── manual_upload.py        # Manually push a video to Supabase
├── tests/
│   ├── test_api.py
│   ├── test_render.py
│   ├── test_database_tables.py
│   └── ...
├── docs/
│   ├── architecture/           # Phase summaries
│   └── setup/                  # Detailed setup guides
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```env
# Upstash Redis (state management)
UPSTASH_REDIS_REST_URL=https://<your-id>.upstash.io
UPSTASH_REDIS_REST_TOKEN=<your-token>

# Mistral AI (LLM code generation)
MISTRAL_API_KEY=<your-key>

# Supabase (database + storage)
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=manim-videos
```

> **Note:** All services are optional — if credentials are missing the backend runs in a degraded but functional mode (no persistence, no LLM, no state tracking).

---

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- FFmpeg (`winget install ffmpeg` / `brew install ffmpeg`)
- A LaTeX distribution (MiKTeX on Windows, MacTeX on macOS, texlive on Linux)

### 1 — Backend

```powershell
# From the workspace root, create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

cd manim-image
pip install -r requirements.txt

# Start the API server (auto-reload)
python -m uvicorn src.manim_service.app:app --host 0.0.0.0 --port 7860 --reload
```

Or use the convenience script on Windows:

```powershell
.\scripts\start_server.ps1
```

The API will be available at `http://localhost:7860`.
Interactive Swagger docs: `http://localhost:7860/docs`

### 2 — Frontend (development mode with HMR)

```powershell
cd frontend
npm install
npm run dev          # Starts on http://localhost:5173
```

The Vite config proxies `/api` and `/render` to `http://localhost:7860`, so no CORS setup is needed during development.

### 3 — Run tests

```powershell
pytest tests/ -v
```

---

## Docker

### Build

```bash
docker build -f docker/Dockerfile -t mathviz .
```

### Run

```bash
docker run -p 7860:7860 \
  -e MISTRAL_API_KEY=<key> \
  -e UPSTASH_REDIS_REST_URL=<url> \
  -e UPSTASH_REDIS_REST_TOKEN=<token> \
  -e SUPABASE_URL=<url> \
  -e SUPABASE_SERVICE_ROLE_KEY=<key> \
  -e SUPABASE_STORAGE_BUCKET=manim-videos \
  mathviz
```

The container serves both the API and the pre-built React frontend from port `7860`.

---

## API Reference

Base URL: `http://localhost:7860` (or your deployed URL)

### `GET /health`

Returns service health and the status of all integrated services.

**Response**
```json
{
  "status": "healthy",
  "message": "Manim Rendering Node is operational"
}
```

---

### `POST /render`

Submit a natural language prompt. The job is accepted immediately and processed asynchronously.

**Request body**
```json
{
  "prompt": "Animate the Pythagorean theorem with a right triangle",
  "quality": "h",
  "max_retries": 3
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | required | Natural language animation description |
| `quality` | string | `"h"` | `l` low  `m` medium  `h` high  `k` 4K |
| `max_retries` | integer | `3` | Max LLM self-correction attempts |

**Response `202`**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Render job accepted. Poll /status/{job_id} for progress."
}
```

---

### `POST /render-code`

Submit a raw Manim Python script directly (legacy / advanced use).

**Request body**
```json
{
  "code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        ...",
  "scene_name": "MyScene",
  "quality": "h"
}
```

---

### `GET /status/{job_id}`

Poll the status of a submitted render job.

**Response**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-02-25T12:00:00Z",
  "updated_at": "2026-02-25T12:01:30Z",
  "video_url": "https://<project>.supabase.co/storage/v1/object/public/manim-videos/videos/<job_id>/MyScene.mp4",
  "video_path": "/tmp/manim_output/<job_id>/MyScene.mp4",
  "error": null
}
```

| `status` value | Meaning |
|---|---|
| `queued` | Accepted, not yet started |
| `processing` | LLM generating / Manim rendering |
| `completed` | Video ready |
| `failed` | All retry attempts exhausted |

---

## Frontend

The React SPA is automatically served by FastAPI from `frontend/dist` after the Docker build. In development, run `npm run dev` inside `frontend/` for hot module replacement.

**Key components**

| Component | Purpose |
|---|---|
| `ChatInterface.jsx` | Prompt input, submission, and progress polling |
| `VideoGallery.jsx` | Grid of previously rendered videos |
| `SingleVideoPlayer.jsx` | Full-screen video playback |
| `Tooltip.jsx` | Hover helpers |

**Authentication & User History**

- `AuthPage.jsx`: Handles user sign in, sign up, and error feedback. New users can register with email, password, and display name. Email confirmation is supported. Existing users can sign in securely.
- `VideoHistory.jsx`: Displays a searchable, filterable list of all videos rendered by the signed-in user. Users can view, download, and search their video history. Fetches data from `/api/user/history`.

**User Flow**

1. **Sign Up / Sign In**: Users can create an account or log in using their email and password. After sign up, email confirmation may be required.
2. **Video History**: Once signed in, users can access their personal video history, search previous prompts, and manage their videos directly from the interface.

---

## Deployment

### Hugging Face Spaces

1. Create a new Space with the **Docker** SDK.
2. Push this repository (the `Dockerfile` lives at `docker/Dockerfile`).
3. Add all environment variables under **Settings → Repository secrets**.
4. The Space will build and serve on port `7860`.

### Database setup

Run the SQL in `database/supabase_schema.sql` against your Supabase project to create the required tables and RLS policies.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Run `pytest tests/ -v` before opening a PR.
3. Format with `black` and sort imports with `isort`.

---

## License

MIT — see `pyproject.toml` for details.
