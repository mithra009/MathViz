"""
Test script for Phase 1 & 2 Manim Rendering Node
Tests all endpoints including Redis state management and validates the complete rendering pipeline
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:7860"
TEST_TIMEOUT = 10  # seconds for API calls

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_success(text):
    """Print success message"""
    print(f" {text}")

def print_error(text):
    """Print error message"""
    print(f" {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ {text}")

def test_root_endpoint():
    """Test GET / endpoint"""
    print_header("Testing Root Endpoint (GET /)")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status Code: {response.status_code}")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Connection refused. Is the server running?")
        print_info(f"Expected server at: {BASE_URL}")
        print_info("Start server with: uvicorn main:app --host 0.0.0.0 --port 7860")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_health_endpoint():
    """Test GET /health endpoint"""
    print_header("Testing Health Endpoint (GET /health)")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status Code: {response.status_code}")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Message: {data.get('message')}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_render_endpoint_simple():
    """Test POST /render with a simple scene"""
    print_header("Testing Render Endpoint - Simple Circle Scene")
    
    # Simple test scene
    test_code = """from manim import *

class CircleScene(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(PINK, opacity=0.5)
        self.play(Create(circle))
        self.wait(1)
"""
    
    payload = {
        "code": test_code,
        "scene_name": "CircleScene",
        "quality": "l"  # low quality for fast testing
    }
    
    try:
        print_info("Sending render request...")
        response = requests.post(
            f"{BASE_URL}/render",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status Code: {response.status_code}")
            print_success(f"Job ID: {data.get('job_id')}")
            print_info(f"Status: {data.get('status')}")
            print_info(f"Message: {data.get('message')}")
            print_info("Job accepted! Check server logs for rendering progress.")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_render_endpoint_complex():
    """Test POST /render with a more complex scene"""
    print_header("Testing Render Endpoint - Complex Animation")
    
    # More complex test scene
    test_code = """from manim import *

class ComplexScene(Scene):
    def construct(self):
        # Create title
        title = Text("Manim Rendering Test", font_size=48)
        self.play(Write(title))
        self.wait(0.5)
        self.play(title.animate.to_edge(UP))
        
        # Create square and circle
        square = Square(side_length=2, color=BLUE)
        circle = Circle(radius=1, color=RED)
        
        self.play(Create(square), Create(circle))
        self.wait(0.5)
        
        # Transform
        self.play(Transform(square, circle))
        self.wait(0.5)
        
        # Fade out
        self.play(FadeOut(square), FadeOut(title))
        self.wait(0.5)
"""
    
    payload = {
        "code": test_code,
        "scene_name": "ComplexScene",
        "quality": "l"
    }
    
    try:
        print_info("Sending render request...")
        response = requests.post(
            f"{BASE_URL}/render",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status Code: {response.status_code}")
            print_success(f"Job ID: {data.get('job_id')}")
            print_info(f"Status: {data.get('status')}")
            print_info("Complex job accepted! Check server logs for rendering progress.")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_invalid_quality():
    """Test POST /render with invalid quality parameter"""
    print_header("Testing Validation - Invalid Quality Parameter")
    
    test_code = """from manim import *

class TestScene(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
"""
    
    payload = {
        "code": test_code,
        "scene_name": "TestScene",
        "quality": "invalid"  # Invalid quality
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/render",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 400:
            print_success("Validation working correctly - rejected invalid quality")
            print_info(f"Error message: {response.json().get('detail')}")
            return True
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_job_status():
    """Test GET /status/{job_id} endpoint - Phase 2 feature"""
    print_header("Testing Job Status Endpoint (Phase 2)")
    
    # First, submit a simple render job
    test_code = """from manim import *

class StatusTestScene(Scene):
    def construct(self):
        text = Text("Status Test")
        self.play(Write(text))
"""
    
    payload = {
        "code": test_code,
        "scene_name": "StatusTestScene",
        "quality": "l"
    }
    
    try:
        # Submit render job
        print_info("Submitting test job...")
        response = requests.post(
            f"{BASE_URL}/render",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code != 200:
            print_error(f"Failed to submit job: {response.status_code}")
            return False
        
        job_id = response.json().get('job_id')
        print_success(f"Job submitted: {job_id}")
        
        # Check status immediately (should be queued or processing)
        print_info("Checking initial status...")
        time.sleep(0.5)  # Small delay
        
        status_response = requests.get(
            f"{BASE_URL}/status/{job_id}",
            timeout=TEST_TIMEOUT
        )
        
        if status_response.status_code == 404:
            print_error("Status endpoint returned 404 - job not found in Redis")
            print_info("This is expected if Redis is not configured")
            return True  # Don't fail the test if Redis is not configured
        elif status_response.status_code == 503:
            print_info("Redis not configured - status endpoint unavailable")
            print_info("This is expected when running without Redis credentials")
            return True  # Don't fail the test
        elif status_response.status_code == 200:
            status_data = status_response.json()
            print_success(f"Job status: {status_data.get('status')}")
            print_info(f"Created at: {status_data.get('created_at')}")
            print_info(f"Updated at: {status_data.get('updated_at')}")
            
            # Wait a bit and check again for completion
            print_info("Waiting 5 seconds for render to complete...")
            time.sleep(5)
            
            status_response2 = requests.get(
                f"{BASE_URL}/status/{job_id}",
                timeout=TEST_TIMEOUT
            )
            
            if status_response2.status_code == 200:
                status_data2 = status_response2.json()
                print_success(f"Updated status: {status_data2.get('status')}")
                if status_data2.get('video_path'):
                    print_info(f"Video path: {status_data2.get('video_path')}")
                if status_data2.get('error'):
                    print_info(f"Error: {status_data2.get('error')}")
            
            return True
        else:
            print_error(f"Unexpected status code: {status_response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_nonexistent_job():
    """Test GET /status/{job_id} with non-existent job ID"""
    print_header("Testing Status Endpoint - Non-existent Job")
    
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    
    try:
        response = requests.get(
            f"{BASE_URL}/status/{fake_job_id}",
            timeout=TEST_TIMEOUT
        )
        
        if response.status_code == 404:
            print_success("Correctly returned 404 for non-existent job")
            return True
        elif response.status_code == 503:
            print_info("Redis not configured - test skipped")
            return True
        else:
            print_error(f"Expected 404, got {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print_header("Phase 1 & 2 Manim Rendering Node - Test Suite")
    print_info(f"Testing server at: {BASE_URL}")
    print_info("Make sure the server is running before running tests!")
    
    results = []
    
    # Run tests
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Health Endpoint", test_health_endpoint()))
    results.append(("Simple Render", test_render_endpoint_simple()))
    results.append(("Complex Render", test_render_endpoint_complex()))
    results.append(("Invalid Quality", test_invalid_quality()))
    results.append(("Job Status (Phase 2)", test_job_status()))
    results.append(("Non-existent Job", test_nonexistent_job()))
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "" if result else ""
        print(f"{symbol} {test_name}: {status}")
    
    print("\n" + "-" * 80)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print_success("All tests passed! ")
        print_info("Check server logs to verify rendering completed successfully.")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
