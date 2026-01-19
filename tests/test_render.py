"""
Quick Test - Submit a new render job to test the fix
"""

import requests
import time

API_URL = "http://localhost:8000"

def test_render():
    print(" Testing Fixed Video Upload")
    print("=" * 70)
    print()
    
    # Submit new job
    print(" Submitting render job...")
    response = requests.post(
        f"{API_URL}/render",
        json={"prompt": "A red square rotating 360 degrees"}
    )
    
    if response.status_code != 200:
        print(f" Failed to submit job: {response.status_code}")
        print(response.text)
        return
    
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f" Job submitted: {job_id}")
    print()
    
    # Poll status
    print("⏳ Waiting for completion...")
    for i in range(60):  # Wait up to 60 seconds
        time.sleep(2)
        
        status_response = requests.get(f"{API_URL}/status/{job_id}")
        status = status_response.json()
        
        current_status = status.get("status", "unknown")
        print(f"   Status: {current_status}", end="\r")
        
        if current_status == "completed":
            print()
            print()
            print("=" * 70)
            print(" RENDER COMPLETED!")
            print("=" * 70)
            print()
            
            video_url = status.get("video_url")
            if video_url:
                print(" SUCCESS! Video uploaded to Supabase Storage!")
                print()
                print(" Video URL:")
                print(video_url)
                print()
            else:
                print("  Video rendered but URL still missing")
                print("Check server logs for upload errors")
                print()
            
            print(f" Local path: {status.get('video_path')}")
            print(f" Status: {status.get('status')}")
            print()
            return
        
        elif current_status == "failed":
            print()
            print(f" Job failed: {status.get('error')}")
            return
    
    print()
    print("⏱  Timeout - job is still processing")

if __name__ == "__main__":
    test_render()
