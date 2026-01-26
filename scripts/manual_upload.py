"""
Manual Upload Script - Upload existing video to Supabase Storage
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "manim-videos")

# Your video path
VIDEO_PATH = r"\tmp\media_b687ea50-e9fe-4681-9703-98839ef5d8c9\videos\b687ea50-e9fe-4681-9703-98839ef5d8c9_attempt\480p15\MovingCircle.mp4"
JOB_ID = "b687ea50-e9fe-4681-9703-98839ef5d8c9"

def upload_video():
    print(" Manual Video Upload to Supabase Storage")
    print("=" * 70)
    print()
    
    # Check if video exists
    video_path = Path(VIDEO_PATH)
    if not video_path.exists():
        print(f" Video file not found: {VIDEO_PATH}")
        return
    
    print(f" Found video: {video_path}")
    print(f"   Size: {video_path.stat().st_size:,} bytes")
    print()
    
    # Create Supabase client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(" Connected to Supabase")
    print()
    
    # Read video file
    print(" Uploading to Supabase Storage...")
    with open(video_path, 'rb') as video_file:
        video_data = video_file.read()
    
    # Upload path
    storage_path = f"videos/{JOB_ID}/MovingCircle.mp4"
    
    try:
        # Upload to Supabase Storage
        response = client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            path=storage_path,
            file=video_data,
            file_options={
                "content-type": "video/mp4",
                "x-upsert": "true"
            }
        )
        
        print(f" Upload successful!")
        print()
        
        # Get public URL
        public_url = client.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
        
        print(" PUBLIC URL:")
        print(public_url)
        print()
        print("=" * 70)
        print(" Done! You can now access your video at the URL above")
        print()
        
    except Exception as e:
        print(f" Upload failed: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check if bucket 'manim-videos' exists")
        print("2. Ensure bucket is PUBLIC")
        print("3. Check storage policies allow INSERT operations")
        print()

if __name__ == "__main__":
    upload_video()
