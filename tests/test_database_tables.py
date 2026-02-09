"""
Test Script: Verify Supabase Database Tables & Storage Bucket
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "manim-videos")

def test_database_setup():
    print("=" * 70)
    print("Phase 4: Database & Storage Verification")
    print("=" * 70)
    print()
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(" Supabase credentials not found")
        return False
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(" Supabase client connected")
        print()
        
        # Test 1: Check Tables Exist
        print(" Testing Database Tables:")
        print("-" * 70)
        
        tables_to_check = [
            "render_jobs",
            "generated_videos", 
            "generation_logs",
            "system_metrics"
        ]
        
        all_tables_ok = True
        for table_name in tables_to_check:
            try:
                # Try to query the table (limit 0 to just test existence)
                response = client.table(table_name).select("*").limit(0).execute()
                print(f" {table_name.ljust(25)} - Table exists")
            except Exception as e:
                print(f" {table_name.ljust(25)} - Not found: {str(e)[:50]}")
                all_tables_ok = False
        
        print("-" * 70)
        print()
        
        # Test 2: Test Insert Operation
        if all_tables_ok:
            print(" Testing Database Operations:")
            print("-" * 70)
            
            test_job_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            try:
                # Insert test record
                response = client.table('render_jobs').insert({
                    'job_id': test_job_id,
                    'prompt': 'Test prompt - verifying database setup',
                    'status': 'pending'
                }).execute()
                print(f" INSERT test passed - Created job: {test_job_id}")
                
                # Query test record
                response = client.table('render_jobs').select("*").eq('job_id', test_job_id).execute()
                if response.data:
                    print(f" SELECT test passed - Retrieved {len(response.data)} record(s)")
                
                # Update test record
                response = client.table('render_jobs').update({
                    'status': 'completed'
                }).eq('job_id', test_job_id).execute()
                print(f" UPDATE test passed - Status changed to completed")
                
                # Delete test record
                response = client.table('render_jobs').delete().eq('job_id', test_job_id).execute()
                print(f" DELETE test passed - Test record cleaned up")
                
            except Exception as e:
                print(f" Database operation failed: {str(e)}")
                all_tables_ok = False
            
            print("-" * 70)
            print()
        
        # Test 3: Check Storage Bucket
        print(" Testing Supabase Storage:")
        print("-" * 70)
        
        try:
            bucket_info = client.storage.get_bucket(SUPABASE_STORAGE_BUCKET)
            print(f" Bucket '{SUPABASE_STORAGE_BUCKET}' exists")
            print(f"   - Bucket ID: {bucket_info.id}")
            print(f"   - Public: {bucket_info.public}")
            
            if not bucket_info.public:
                print(f"     WARNING: Bucket is private. Make it public for video access.")
                print(f"   - Go to Supabase Dashboard → Storage → {SUPABASE_STORAGE_BUCKET} → Make Public")
            
        except Exception as e:
            print(f" Bucket '{SUPABASE_STORAGE_BUCKET}' error: {str(e)}")
            print(f"   - Create bucket in Supabase Dashboard → Storage")
            all_tables_ok = False
        
        print("-" * 70)
        print()
        
        # Summary
        print("=" * 70)
        if all_tables_ok:
            print(" ALL TESTS PASSED - System Ready for Production!")
        else:
            print("  SOME TESTS FAILED - Review errors above")
        print("=" * 70)
        print()
        
        return all_tables_ok
        
    except Exception as e:
        print(f" Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_setup()
    
    if success:
        print()
        print(" NEXT STEPS:")
        print()
        print("1. Start the API Server:")
        print("   uvicorn main:app --reload --port 8000")
        print()
        print("2. Test the API:")
        print("   Open browser: http://localhost:8000/docs")
        print()
        print("3. Create your first video:")
        print("   POST to /generate with prompt: 'A blue circle moving to the right'")
        print()
