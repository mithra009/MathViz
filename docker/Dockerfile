# Phase 1 & 2: Manim Rendering Node - Optimized Compute Layer with State Management
# Multi-stage build: Stage 1 builds the frontend
FROM node:18-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Container Layer Consolidation (Constraint #3) & Dependency Pruning (Constraint #2)
# All system dependencies installed in a single chained RUN command with cache cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # Build tools for compiling Python packages with C extensions
    gcc \
    g++ \
    build-essential \
    # Core system dependencies for Manim
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    pkg-config \
    python3-dev \
    # Minimalist Typography - only essential LaTeX packages
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-science \
    texlive-xetex \
    # Additional dependencies for rendering
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Strict Filesystem Redirection (Constraint #4)
# Create non-root user with UID 1000 for HuggingFace Spaces compliance
RUN useradd -m -u 1000 manim_user && \
    mkdir -p /tmp && \
    chown -R manim_user:manim_user /tmp /app

# Copy requirements and install Python dependencies
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
