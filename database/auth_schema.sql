-- Phase 5: User Authentication & History Schema
-- Manim AI Video Rendering System
-- Execute this SQL in the Supabase SQL Editor AFTER the base schema

-- ============================================================
-- Table: user_profiles
-- Extends Supabase Auth users with app-specific profile data
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_videos INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- Add user_id column to render_jobs (link jobs to users)
-- ============================================================
ALTER TABLE render_jobs 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- ============================================================
-- Add user_id column to generated_videos (link videos to users)
-- ============================================================
ALTER TABLE generated_videos 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- ============================================================
-- Indexes for user-based queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_render_jobs_user_id ON render_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_user_id ON generated_videos(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);

-- ============================================================
-- Auto-update trigger for user_profiles
-- ============================================================
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Function: Auto-create user profile on signup
-- Triggered when a new user signs up via Supabase Auth
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- Row Level Security (RLS) Policies
-- ============================================================

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_videos ENABLE ROW LEVEL SECURITY;

-- user_profiles: Users can read/update only their own profile
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- render_jobs: Users can see their own jobs; service role can do everything
CREATE POLICY "Users can view own jobs" ON render_jobs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to jobs" ON render_jobs
    FOR ALL USING (auth.role() = 'service_role');

-- generated_videos: Users can see their own videos; public can see all (gallery)
CREATE POLICY "Users can view own videos" ON generated_videos
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role full access to videos" ON generated_videos
    FOR ALL USING (auth.role() = 'service_role');

-- ============================================================
-- Increment video count function
-- ============================================================
CREATE OR REPLACE FUNCTION increment_user_video_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id IS NOT NULL THEN
        UPDATE user_profiles 
        SET total_videos = total_videos + 1 
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_video_created
    AFTER INSERT ON generated_videos
    FOR EACH ROW
    EXECUTE FUNCTION increment_user_video_count();
