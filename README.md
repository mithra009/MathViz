# Phase 1: Manim Rendering Node - Compute Layer

A zero-cost, serverless compute layer for AI-driven Manim video generation. This service receives dynamically generated Python scripts from an LLM, executes them in a heavily sandboxed environment, and outputs MP4/GIF video artifacts.

##  Overview

The compute layer is optimized for deployment on free-tier serverless environments (specifically Hugging Face Spaces) with the following characteristics:

- **Minimal footprint**: Uses `python:3.9-slim` instead of 4.49GB official Manim image
- **Read-only filesystem compliant**: All I/O redirected to `/tmp` directory
- **Non-root execution**: Runs as UID 1000 for security compliance
- **Asynchronous processing**: Instant webhook acknowledgment to prevent timeouts
- **Cache suppression**: Prevents disk exhaustion on constrained environments

##  System Architecture

### Six Core Optimization Constraints

1. **Base Image Substitution**: `python:3.9-slim` for rapid container initialization
2. **Dependency Pruning**: Minimalist LaTeX installation (texlive-latex-extra only)
3. **Container Layer Consolidation**: Chained RUN commands with aggressive cache cleanup
4. **Strict Filesystem Redirection**: All operations in `/tmp`, non-root user (UID 1000)
5. **Caching Suppression**: `--disable_caching` flag prevents disk exhaustion
6. **Asynchronous API Orchestration**: Background task processing with instant acknowledgment

##  Project Structure

```
manim-ai-service/
 src/                         # Source code
    manim_service/
        __init__.py
        app.py               # FastAPI application & routes
        utils/
            __init__.py
            health_check.py
 tests/                       # Test suite
    __init__.py
    test_api.py
    test_render.py
    ...
 docs/                        # Documentation
    setup/                   # Setup guides
       QUICK_START.md
       FRONTEND_SETUP.md
       ...
    architecture/            # Architecture docs
        PHASE2_SUMMARY.md
        ...
 scripts/                     # Utility scripts
    start_server.ps1
    manual_upload.py
 database/                    # Database schemas
    supabase_schema.sql
 docker/                      # Docker configuration
    Dockerfile
    .dockerignore
 frontend/                    # React frontend
    src/
    package.json
    ...
 .env.example                 # Environment template
 .gitignore
 pyproject.toml               # Project configuration
 requirements.txt             # Python dependencies
 README.md                    # This file
```

##  Quick Start

### Local Development Setup

1. **Prerequisites**
   ```bash
   - Python 3.9+
   - Docker Desktop (for containerized testing)
   - 2GB+ free disk space
   ```

2. **Install Dependencies** (in virtual environment in root folder)
   ```bash
   # Activate virtual environment
   cd ..
   .\venv\Scripts\activate  # Windows
   # or
   source ../venv/bin/activate  # Linux/Mac
   
   # Install dependencies
   cd manim-image
   pip install -r requirements.txt
   ```

3. **Run Locally (Non-Docker)**
   ```bash
   # From project root
   python -m uvicorn src.manim_service.app:app --host 0.0.0.0 --port 7860 --reload
   
   # Or use the start script (Windows)
   .\scripts\start_server.ps1
   ```
   
   The service will be available at `http://localhost:7860`

### Docker Build & Test

1. **Build the Optimized Image**
   ```bash
   docker build -t minimal-manim-worker .
   ```
   
   Expected build time: 5-10 minutes (depending on network speed)
   Expected image size: ~2GB (vs 4.49GB official image)

2. **Run the Container**
   ```bash
   docker run -p 7860:7860 minimal-manim-worker
   ```

3. **Verify Health Endpoint**
   ```bash
   curl http://localhost:7860/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "message": "Manim Rendering Node is operational and ready to process requests"
   }
   ```

##  Testing the Render Endpoint

### Simple Test Scene

```bash
curl -X POST http://localhost:7860/render \
  -H "Content-Type: application/json" \
  -d '{
    "scene_name": "CircleScene",
    "quality": "l",
    "code": "from manim import *\n\nclass CircleScene(Scene):\n    def construct(self):\n        circle = Circle()\n        circle.set_fill(PINK, opacity=0.5)\n        self.play(Create(circle))\n        self.wait(1)"
  }'
```

Expected response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Render job 550e8400-e29b-41d4-a716-446655440000 accepted and queued for processing"
}
```

### Check Docker Logs

```bash
docker logs <container_id>
```

You should see:
1. Job acceptance log
2. Manim rendering progress
3. Video generation confirmation
4. File cleanup logs

##  API Endpoints

### `GET /`
Root endpoint with service information.

**Response:**
```json
{
  "service": "Manim Rendering Node",
  "phase": "Phase 1 - Compute Layer",
  "status": "operational",
  "endpoints": {
    "health": "/health",
    "render": "/render"
  }
}
```

### `GET /health`
Synthetic monitoring endpoint for keeping the service warm.

**Response:**
```json
{
  "status": "healthy",
  "message": "Manim Rendering Node is operational and ready to process requests"
}
```

### `POST /render`
Primary webhook ingestion endpoint for render jobs.

**Request Body:**
```json
{
  "code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        ...",
  "scene_name": "MyScene",
  "quality": "l"  // Optional: "l" (low), "m" (medium), "h" (high), "k" (4k)
}
```

**Response:**
```json
{
  "job_id": "uuid-v4-string",
  "status": "accepted",
  "message": "Render job {job_id} accepted and queued for processing"
}
```

**Quality Options:**
- `l` (low): 480p @ 15fps - fastest, smallest file
- `m` (medium): 720p @ 30fps - balanced
- `h` (high): 1080p @ 60fps - high quality
- `k` (4k): 2160p @ 60fps - maximum quality

##  Debugging & Troubleshooting

### Viewing Logs

**Local (non-Docker):**
Logs print directly to console.

**Docker:**
```bash
docker logs -f <container_id>
```

### Common Issues

1. **"No module named 'manim'"**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. **"Permission denied" errors in Docker**
   - Verify non-root user setup in Dockerfile
   - Check `/tmp` directory permissions

3. **"Disk quota exceeded"**
   - Enable caching suppression flag
   - Implement aggressive cleanup in `finally` blocks

4. **Render timeout**
   - Default timeout: 5 minutes
   - Adjust in `main.py` `subprocess.run(timeout=300)`

5. **LaTeX rendering fails**
   - Verify texlive packages installed in Docker
   - Check logs for missing LaTeX packages

##  Deployment to Hugging Face Spaces

### Prerequisites
- Hugging Face account
- Docker Space (not Gradio/Streamlit)

### Deployment Steps

1. **Create a New Space**
   - Go to https://huggingface.co/new-space
   - Select: **Docker** as SDK
   - Choose: **Blank** template

2. **Push Your Code**
   ```bash
   git init
   git remote add hf https://huggingface.co/spaces/{username}/{space-name}
   git add Dockerfile main.py requirements.txt
   git commit -m "Initial Phase 1 deployment"
   git push hf main
   ```

3. **Configure Space Settings**
   - Set port: `7860`
   - Enable: **Persistent storage** (optional, for logs)

4. **Monitor Deployment**
   - Watch build logs in HF dashboard
   - First build takes ~10-15 minutes
   - Subsequent builds use layer caching

5. **Test Deployed Service**
   ```bash
   curl https://{username}-{space-name}.hf.space/health
   ```

### Keep-Alive Strategy

To prevent cold starts, set up a GitHub Actions cron job:

`.github/workflows/keep-alive.yml`:
```yaml
name: Keep Manim Node Warm
on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping health endpoint
        run: curl https://{username}-{space-name}.hf.space/health
```

##  Security Considerations

1. **Sandboxed Execution**: All code runs in isolated `/tmp` directory
2. **Non-root User**: Container runs as UID 1000
3. **No Persistent State**: Ephemeral cleanup after each job
4. **Resource Limits**: 5-minute timeout prevents runaway processes
5. **Input Validation**: Pydantic models enforce schema validation

##  Performance Metrics

**Expected Performance (HuggingFace Free Tier):**
- Cold start latency: 30-60 seconds
- Warm request latency: <100ms (acknowledgment)
- Render time (low quality, simple scene): 10-30 seconds
- Render time (high quality, complex scene): 2-5 minutes
- Concurrent job limit: 1 (free tier limitation)

##  Next Steps (Phase 2 & 3)

This compute layer is designed to integrate with:

- **Phase 2**: Message queue orchestration (QStash/Redis)
- **Phase 3**: LLM agent with iterative self-correction
- **Phase 4**: Frontend interface for video generation requests

##  License

This project is part of a zero-cost AI video generation pipeline.

##  Contributing

Considerations for optimization:
1. Further reduce Docker image size (current: ~2GB)
2. Implement video artifact storage (S3/R2)
3. Add progress tracking for long renders
4. Implement render result caching
5. Add support for multiple scene rendering

##  Reference Documentation

- [Manim Documentation](https://docs.manim.community/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Spaces](https://huggingface.co/docs/hub/spaces)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**Built with  for the zero-cost AI video generation community**
