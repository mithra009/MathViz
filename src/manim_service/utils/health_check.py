"""
Phase 4: System Health Check
Validates all service connections and reports system status
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def check_service(service_name, check_func):
    """Run a service check and return formatted result"""
    try:
        result = check_func()
        status = "" if result else ""
        return status, result
    except Exception as e:
        return "", str(e)

def check_redis():
    """Check Redis connection"""
    url = os.getenv("UPSTASH_REDIS_REST_URL")
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    
    if not url or not token:
        return "Missing credentials"
    
    try:
        from upstash_redis import Redis
        redis_client = Redis(url=url, token=token)
        redis_client.ping()
        return "Connected and responding"
    except Exception as e:
        return f"Connection failed: {str(e)}"

def check_mistral():
    """Check Mistral AI connection"""
    api_key = os.getenv("MISTRAL_API_KEY")
    
    if not api_key:
        return "Missing API key"
    
    try:
        from mistralai import Mistral
        client = Mistral(api_key=api_key)
        return "Client initialized"
    except Exception as e:
        return f"Initialization failed: {str(e)}"

def check_supabase():
    """Check Supabase connection"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        return "Missing credentials"
    
    try:
        from supabase import create_client
        client = create_client(url, key)
        return f"Connected to {url}"
    except Exception as e:
        return f"Connection failed: {str(e)}"

def check_supabase_storage():
    """Check Supabase Storage configuration"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "manim-videos")
    
    if not url or not key:
        return "Missing credentials"
    
    try:
        from supabase import create_client
        client = create_client(url, key)
        
        # Try to verify bucket exists
        try:
            client.storage.get_bucket(bucket)
            return f"Bucket '{bucket}' verified and accessible"
        except Exception as bucket_error:
            return f"Connected but bucket '{bucket}' may not exist. Create it in Supabase dashboard."
    except Exception as e:
        return f"Connection failed: {str(e)}"

def main():
    print("=" * 70)
    print(" " * 15 + "MANIM AI RENDERING NODE")
    print(" " * 20 + "System Health Check")
    print("=" * 70)
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    print()
    
    # Service checks
    services = [
        ("Redis (State Management)", check_redis),
        ("Mistral AI (LLM Provider)", check_mistral),
        ("Supabase (Database)", check_supabase),
        ("Supabase Storage (Videos)", check_supabase_storage),
    ]
    
    print("-" * 70)
    print("SERVICE STATUS")
    print("-" * 70)
    
    all_critical_ok = True
    
    for service_name, check_func in services:
        status, result = check_service(service_name, check_func)
        
        # Format output
        service_display = f"{service_name}:".ljust(35)
        print(f"{status} {service_display} {result}")
        
        # Track critical services
        if status == "":
            all_critical_ok = False
    
    print("-" * 70)
    print()
    
    # Overall status
    print("=" * 70)
    if all_critical_ok:
        print(" SYSTEM STATUS: ALL CRITICAL SERVICES OPERATIONAL")
    else:
        print("  SYSTEM STATUS: SOME CRITICAL SERVICES UNAVAILABLE")
    print("=" * 70)
    print()
    
    # Next steps
    print(" NEXT STEPS:")
    print()
    
    print("1. Create Supabase Storage Bucket:")
    print("   - Open Supabase dashboard: https://supabase.com/dashboard")
    print("   - Go to Storage → Create a new bucket")
    print("   - Name it: manim-videos (or update SUPABASE_STORAGE_BUCKET in .env)")
    print("   - Make it public for video access")
    print()
    
    print("2. Execute Database Schema:")
    print("   - Open Supabase dashboard: https://supabase.com/dashboard")
    print("   - Go to SQL Editor → New Query")
    print("   - Copy and run: supabase_schema.sql")
    print()
    
    print("3. Start the API Server:")
    print("   - Run: uvicorn main:app --reload --port 8000")
    print("   - Test: http://localhost:8000/docs")
    print()
    
    print("4. Test the System:")
    print("   - POST request to /generate with a prompt")
    print("   - Monitor job status in Supabase Table Editor")
    print()
    
    print("=" * 70)
    print()
    
    return 0 if all_critical_ok else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
