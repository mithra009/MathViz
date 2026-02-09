"""
Phase 3 Test Script - AI-Driven Manim Generation
Tests the /render endpoint with natural language prompts
"""

import requests
import json
import time

BASE_URL = "http://localhost:7860"

def test_phase3_ai_render():
    """Test the AI-driven /render endpoint with a simple prompt"""
    print("\n" + "="*80)
    print("Phase 3 Test: AI-Driven Rendering")
    print("="*80)
    
    prompt = "Create a simple animation with a blue circle that fades in, then transforms into a red square"
    
    payload = {
        "prompt": prompt,
        "quality": "l",
        "max_retries": 3
    }
    
    print(f"\n Prompt: {prompt}")
    print(f"\nSending request to {BASE_URL}/render...")
    
    try:
        # Submit the job
        response = requests.post(
            f"{BASE_URL}/render",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            job_id = data['job_id']
            print(f"\n Job submitted successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {data['status']}")
            print(f"   Message: {data['message']}")
            
            # Poll for completion
            print(f"\n⏳ Polling job status...")
            for i in range(30):  # Poll for up to 30 seconds
                time.sleep(1)
                
                try:
                    status_response = requests.get(f"{BASE_URL}/status/{job_id}", timeout=5)
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_status = status_data['status']
                        
                        print(f"   [{i+1}s] Status: {current_status}", end="")
                        
                        if 'attempt' in status_data:
                            print(f" (Attempt {status_data['attempt']})", end="")
                        
                        print()  # Newline
                        
                        if current_status == "completed":
                            print(f"\n SUCCESS! Video generated")
                            print(f"   Video Path: {status_data.get('video_path', 'N/A')}")
                            print(f"   File Size: {status_data.get('file_size', 'N/A')} bytes")
                            print(f"   Attempts: {status_data.get('attempts', 1)}")
                            if 'final_code' in status_data:
                                print(f"\n Generated Code (first 500 chars):")
                                print(f"   {status_data['final_code'][:500]}...")
                            return True
                        elif current_status == "failed":
                            print(f"\n Job failed!")
                            print(f"   Error: {status_data.get('error', 'Unknown error')}")
                            print(f"   Attempts: {status_data.get('attempts', 'N/A')}")
                            return False
                        elif current_status in ["queued", "processing"]:
                            # Still in progress
                            if 'last_error' in status_data:
                                print(f"   Last error: {status_data['last_error'][:100]}...")
                            continue
                            
                except requests.exceptions.RequestException as e:
                    print(f"   Error checking status: {e}")
                    continue
            
            print(f"\n⏱ Timeout: Job still processing after 30 seconds")
            print(f"   Check status later with: GET {BASE_URL}/status/{job_id}")
            return False
            
        elif response.status_code == 503:
            print(f"\n  LLM not available (503)")
            print(f"   Response: {response.json()}")
            print(f"\n Make sure GROQ_API_KEY or MISTRAL_API_KEY is set")
            return False
        else:
            print(f"\n Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n Connection failed - is the server running?")
        print(f"   Start server with: uvicorn main:app --host 0.0.0.0 --port 7860 --reload")
        return False
    except Exception as e:
        print(f"\n Error: {e}")
        return False


def test_simple_prompts():
    """Test multiple simple prompts"""
    print("\n" + "="*80)
    print("Phase 3 Test: Multiple Prompts")
    print("="*80)
    
    prompts = [
        "Draw a red circle",
        "Create a blue square that rotates 360 degrees",
        "Show the text 'Hello Manim!'",
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] Testing: {prompt}")
        
        payload = {"prompt": prompt, "quality": "l", "max_retries": 2}
        
        try:
            response = requests.post(f"{BASE_URL}/render", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"    Submitted: {data['job_id']}")
            else:
                print(f"    Failed: {response.status_code}")
        except Exception as e:
            print(f"    Error: {e}")
            break
        
        time.sleep(1)  # Be nice to the API


def check_service_info():
    """Check service information"""
    print("\n" + "="*80)
    print("Service Information")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"\nService: {data['service']}")
            print(f"Phase: {data['phase']}")
            print(f"Status: {data['status']}")
            print(f"Redis Enabled: {data.get('redis_enabled', False)}")
            print(f"LLM Enabled: {data.get('llm_enabled', False)}")
            print(f"\nEndpoints:")
            for name, path in data.get('endpoints', {}).items():
                print(f"  • {name}: {path}")
            print(f"\nFeatures:")
            for feature in data.get('features', []):
                print(f"  • {feature}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("  Phase 3: AI-Driven Manim Rendering Test Suite")
    print("="*80)
    print("\nMake sure:")
    print("  1. Server is running (uvicorn main:app --reload)")
    print("  2. GROQ_API_KEY or MISTRAL_API_KEY environment variable is set")
    print("  3. UPSTASH_REDIS_REST_URL and TOKEN are set (optional)")
    
    input("\nPress Enter to continue...")
    
    # Run tests
    check_service_info()
    test_phase3_ai_render()
    
    # Optional: test multiple prompts
    choice = input("\n\nTest multiple prompts? (y/n): ")
    if choice.lower() == 'y':
        test_simple_prompts()
    
    print("\n" + "="*80)
    print("Tests complete!")
    print("="*80 + "\n")
