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
# with UID 1000, so just ensure directories are writable.
RUN mkdir -p /tmp /app && \
    chown -R 1000:1000 /tmp /app

# Copy requirements and install extra Python dependencies
# (Manim itself is already installed in the base image)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (new src structure)
COPY src/ ./src/

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Switch to non-root user by UID (Constraint #4)
USER 1000

# Expose port for FastAPI
EXPOSE 7860

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    PYTHONPATH=/app

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "src.manim_service.app:app", "--host", "0.0.0.0", "--port", "7860"]
