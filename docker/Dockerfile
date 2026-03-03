# Manim Rendering Node - Full Quality Compute Layer
# Multi-stage build: Stage 1 builds the frontend
FROM node:18-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Full Manim Community image (includes Cairo, Pango, FFmpeg,
#           full TeX Live, all fonts, OpenGL support, and Manim itself)
FROM manimcommunity/manim:latest

# Switch to root to install additional Python packages and set up the app
USER root

# Set working directory
WORKDIR /app

# HuggingFace Spaces requires UID 1000. The base image already has a user
# with UID 1000, so reuse it (or create if missing) and ensure /tmp and /app
# are writable.
RUN existing_user=$(getent passwd 1000 | cut -d: -f1) && \
    if [ -z "$existing_user" ]; then \
        useradd -m -u 1000 manim_user; \
    else \
        usermod -l manim_user -d /home/manim_user -m "$existing_user" 2>/dev/null || true; \
    fi && \
    mkdir -p /tmp /home/manim_user && \
    chown -R 1000:1000 /tmp /app /home/manim_user

# Copy requirements and install extra Python dependencies
# (Manim itself is already installed in the base image)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (new src structure)
COPY src/ ./src/

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Switch to non-root user (Constraint #4)
USER manim_user

# Expose port for FastAPI
EXPOSE 7860

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONPATH=/app

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "src.manim_service.app:app", "--host", "0.0.0.0", "--port", "7860"]
