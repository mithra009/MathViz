-- Phase 4: Supabase Database Schema
-- Manim AI Video Rendering System
-- Execute this SQL in the Supabase SQL Editor

-- ============================================================
-- Table 1: render_jobs
-- Tracks all rendering job requests and their status
-- ============================================================
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) UNIQUE NOT NULL,
    prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'rendering', 'uploading', 'completed', 'failed'))
);

-- ============================================================
-- Table 2: generated_videos
-- Stores metadata for successfully rendered videos
-- ============================================================
CREATE TABLE IF NOT EXISTS generated_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) NOT NULL REFERENCES render_jobs(job_id) ON DELETE CASCADE,
    video_url TEXT NOT NULL,
    cdn_url TEXT,
    file_size_bytes BIGINT,
    duration_seconds NUMERIC(10, 2),
    resolution VARCHAR(20),
    format VARCHAR(10) DEFAULT 'mp4',
    thumbnail_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    views_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================
-- Table 3: generation_logs
-- Detailed logs for each generation attempt (LLM iterations, errors, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS generation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(255) NOT NULL REFERENCES render_jobs(job_id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    log_level VARCHAR(20) NOT NULL DEFAULT 'INFO',
    message TEXT NOT NULL,
    generated_code TEXT,
    error_details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT valid_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- ============================================================
-- Table 4: system_metrics
-- Track system performance and usage metrics
-- ============================================================
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(50) NOT NULL,
    metric_value NUMERIC(15, 2) NOT NULL,
    tags JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- Indexes for Performance Optimization
-- ============================================================

-- Jobs table indexes
CREATE INDEX IF NOT EXISTS idx_render_jobs_job_id ON render_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created_at ON render_jobs(created_at DESC);

-- Videos table indexes
CREATE INDEX IF NOT EXISTS idx_generated_videos_job_id ON generated_videos(job_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_created_at ON generated_videos(created_at DESC);

-- Logs table indexes
CREATE INDEX IF NOT EXISTS idx_generation_logs_job_id ON generation_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_generation_logs_timestamp ON generation_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_generation_logs_log_level ON generation_logs(log_level);

-- Metrics table indexes
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp DESC);

-- ============================================================
-- Triggers for Auto-Update Timestamps
-- ============================================================

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for render_jobs table
CREATE TRIGGER update_render_jobs_updated_at
    BEFORE UPDATE ON render_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Row Level Security (RLS) Policies
-- IMPORTANT: Enable RLS only if you have authentication enabled
-- For now, these are commented out for development
-- ============================================================

-- Enable RLS on all tables (uncomment when ready for production)
-- ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE generated_videos ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE generation_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow all operations for authenticated users
-- CREATE POLICY "Allow all for authenticated users" ON render_jobs
--     FOR ALL USING (auth.role() = 'authenticated');

-- Example policy: Allow read access for anonymous users
-- CREATE POLICY "Allow read for anonymous" ON generated_videos
--     FOR SELECT USING (true);

-- ============================================================
-- Sample Queries for Testing
-- ============================================================

-- View all jobs
-- SELECT * FROM render_jobs ORDER BY created_at DESC LIMIT 10;

-- View all videos
-- SELECT * FROM generated_videos ORDER BY created_at DESC LIMIT 10;

-- View logs for a specific job
-- SELECT * FROM generation_logs WHERE job_id = 'your-job-id' ORDER BY iteration_number;

-- Count jobs by status
-- SELECT status, COUNT(*) as count FROM render_jobs GROUP BY status;

-- Average rendering duration
-- SELECT AVG(duration_seconds) as avg_duration FROM render_jobs WHERE status = 'completed';
