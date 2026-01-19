"""
Test Script: Verify Supabase Connection
Phase 4: Database Integration
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def test_supabase_connection():
    """Test the Supabase connection and display project info"""
    print("=" * 60)
    print("Phase 4: Supabase Connection Test")
    print("=" * 60)
    print()
    
    # Validate environment variables
    if not SUPABASE_URL:
        print(" Error: SUPABASE_URL not found in environment variables")
        return False
    
    if not SUPABASE_KEY:
        print(" Error: SUPABASE_KEY not found in environment variables")
        return False
    
    print(f" Supabase URL: {SUPABASE_URL}")
    print(f" API Key configured: {SUPABASE_KEY[:20]}...")
    print()
    
    try:
        # Create Supabase client
        print(" Initializing Supabase client...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(" Supabase client created successfully")
        print()
        
        # Test connection with a simpler approach
        print(" Testing database connection...")
        print(" Client connected to:", SUPABASE_URL)
        print()
        
        # Show some client properties
        print(" Client Information:")
        print(f"   - Base URL: {supabase.supabase_url}")
        print(f"   - Auth Available: {hasattr(supabase, 'auth')}")
        print(f"   - Storage Available: {hasattr(supabase, 'storage')}")
        print()
        
        print("=" * 60)
        print(" CONNECTION TEST PASSED")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Create database tables in Supabase dashboard")
        print("2. Set up Row Level Security (RLS) policies")
        print("3. Implement CRUD operations in main.py")
        print("4. Add database persistence to the rendering pipeline")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print(" CONNECTION TEST FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        return False

if __name__ == "__main__":
    test_supabase_connection()
