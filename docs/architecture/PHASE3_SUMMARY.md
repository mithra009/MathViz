# Phase 3 Implementation Complete! 

## Summary

**Phase 3: AI-Driven Manim Code Generation with Self-Correction Loop** has been successfully implemented!

Your system now accepts natural language prompts and automatically:
1.  Generates Manim code using **Mistral AI** (mistral-small-latest)
2.  Executes the code in a sandboxed environment
3.  If it fails, sends the error back to the LLM for correction
4.  Retries up to 3 times (configurable)
5.  Tracks full job lifecycle in Redis

---

## What's New in Phase 3

### 1. **Natural Language Interface**
- **Before (Phase 1/2)**: Had to write Manim code manually
- **Now (Phase 3)**: Just describe what you want in plain English!

**Example**:
```
"Create a blue circle that fades in, then transforms into a red square"
```

### 2. **Self-Correction Loop (Test-Time Compute)**
If the LLM generates broken code:
-  System catches the Manim error
-  Sends error message back to LLM: *"Your code failed with this error. Fix it."*
-  LLM generates corrected code
-  Retries automatically (up to 3 attempts by default)

### 3. **Two API Modes**

#### **AI Mode** (New!)
```bash
POST /render
{
  "prompt": "Draw a rotating cube",
  "quality": "l",
  "max_retries": 3
}
```

#### **Legacy Mode** (Backward Compatible)
```bash
POST /render-code
{
  "code": "from manim import *\n\nclass MyScene(Scene):...",
  "scene_name": "MyScene",
  "quality": "l"
}
```

---

## Quick Start Guide

### Step 1: Set Environment Variables

**Option A: Using the provided script**
```powershell
.\start_server_phase3.ps1
```

**Option B: Manual setup**
```powershell
# Redis (from Phase 2)
$env:UPSTASH_REDIS_REST_URL = "https://YOUR-REDIS-URL.upstash.io"
$env:UPSTASH_REDIS_REST_TOKEN = "your-upstash-redis-token-here"

# Mistral AI API Key
$env:MISTRAL_API_KEY = "your-mistral-api-key-here"

# Start server
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

### Step 2: Verify Service is Running

Expected startup logs:
```
Phase 3 Features:
   LLM Code Generation: ENABLED (Mistral AI)
   Self-Correction Loop: ENABLED (max 3 retries)
   Natural Language Processing: ENABLED
```

### Step 3: Test with AI-Driven Rendering

**Option A: Using the test script**
```powershell
# In a new terminal
python test_phase3.py
```

**Option B: Manual API call**
```powershell
$body = @{
    prompt = "Create a simple animation with a pink circle that grows larger"
    quality = "l"
    max_retries = 3
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:7860/render -Method Post -Body $body -ContentType "application/json"
$jobId = $response.job_id
Write-Host "Job ID: $jobId"

# Check status
Invoke-RestMethod -Uri "http://localhost:7860/status/$jobId"
```

---

## Testing Phase 3

### Test 1: Simple Animation
```powershell
$body = @{
    prompt = "Draw a red circle"
    quality = "l"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:7860/render -Method Post -Body $body -ContentType "application/json"
```

### Test 2: Complex Animation
```powershell
$body = @{
    prompt = "Create a blue square that rotates 360 degrees and then fades out"
    quality = "l"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:7860/render -Method Post -Body $body -ContentType "application/json"
```

### Test 3: Self-Correction (Intentional Error)
```powershell
$body = @{
    prompt = "Use ShowCreation to animate a circle"  # ShowCreation is deprecated
    quality = "l"
    max_retries = 2
} | ConvertTo-Json

# The LLM should detect the error and fix it to use Create() instead
Invoke-RestMethod -Uri http://localhost:7860/render -Method Post -Body $body -ContentType "application/json"
```

---

## How It Works

### The Self-Correction Pipeline

```
User Prompt
    ↓
[Attempt 1]
     LLM generates code
     Extract scene name
     Execute with Manim
      Fails with error
         ↓
[Attempt 2]
     Send error to LLM: "Fix this: AttributeError..."
     LLM generates corrected code
     Execute with Manim
      Success!
         ↓
    Update Redis: status=completed
    Return video path
```

### System Prompt (What We Tell the LLM)

The LLM is instructed to:
-  Use **only** Manim Community Edition syntax
-  Never use old `manimlib` imports
-  Use modern methods (`Create` not `ShowCreation`)
-  Always include `self.wait()` at the end
-  Return clean Python code without markdown

---

## API Reference

### POST /render (Phase 3 - AI Mode)

**Request**:
```json
{
  "prompt": "Natural language description",
  "quality": "l",  // Optional: l, m, h, k
  "max_retries": 3  // Optional: 1-5
}
```

**Response**:
```json
{
  "job_id": "uuid-here",
  "status": "accepted",
  "message": "AI render job accepted. Code will be generated and executed with self-correction."
}
```

### GET /status/{job_id}

**Example Response (Processing)**:
```json
{
  "job_id": "uuid",
  "status": "processing",
  "attempt": 2,
  "max_retries": 3,
  "last_error": "NameError: name 'ShowCreation' is not defined",
  "generated_code": "from manim import *\n\nclass..."
}
```

**Example Response (Completed)**:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "video_path": "/tmp/media_.../MyScene.mp4",
  "file_size": 15234,
  "attempts": 2,
  "final_code": "from manim import *\n\nclass MyScene(Scene):\n...",
  "scene_name": "MyScene"
}
```

**Example Response (Failed)**:
```json
{
  "job_id": "uuid",
  "status": "failed",
  "error": "Failed after 3 attempts. Last error: SyntaxError...",
  "attempts": 3
}
```

---

## Monitoring Self-Correction in Action

Watch the server logs to see the self-correction loop:

```
[Job abc123] Attempt 1/3
[Job abc123] Generating Manim code from prompt: Draw a circle...
[Job abc123] Code generated (245 chars)
[Job abc123] Extracted scene name: CircleAnimation
[Job abc123] Executing command: manim -ql...
[Job abc123] Attempt 1 failed: NameError: name 'ShowCreation' is not defined

[Job abc123] Attempt 2/3
[Job abc123] Generating Manim code from prompt: Draw a circle...
[Job abc123] Code generated (241 chars)
[Job abc123] Extracted scene name: CircleAnimation
[Job abc123] Executing command: manim -ql...
[Job abc123] Render succeeded on attempt 2
[Job abc123] Video generated at: /tmp/media_.../CircleAnimation.mp4
```

---

## Architecture

```

  User Browser   

          POST /render {prompt: "..."}
         ↓

         FastAPI Server (main.py)        
                                         
  1. Accept prompt                       
  2. Generate job_id                     
  3. Update Redis: status=queued         
  4. Return job_id immediately           
  5. Start background task               

         
         ↓

  execute_manim_with_retries()           
                                         
  for attempt in 1..max_retries:         
     Call LLM (Mistral AI)            
     Extract scene name                
     Execute Manim                     
     If fails:                         
          Send error to LLM            
          Retry                        

         
         ↓

           Upstash Redis                 
  job:abc123 = {                         
    status: "completed",                 
    video_path: "/tmp/...",              
    attempts: 2,                         
    final_code: "..."                    
  }                                      

```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `UPSTASH_REDIS_REST_URL` | Optional | Redis REST endpoint (Phase 2) |
| `UPSTASH_REDIS_REST_TOKEN` | Optional | Redis authentication token |
| `MISTRAL_API_KEY` | **Required** | Mistral AI API key for code generation |

**Note**: Service will work without Redis but you won't be able to query job status.

---

## Troubleshooting

### Error: "LLM code generation not available"

**Cause**: `MISTRAL_API_KEY` not set

**Solution**:
```powershell
$env:MISTRAL_API_KEY = "your-api-key-here"
```

### Error: "State management not available"

**Cause**: Redis credentials not set

**Impact**: Service works but `/status/{job_id}` endpoint won't work

**Solution**: Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`

### LLM generates broken code repeatedly

**Symptoms**: All 3 attempts fail with same error

**Possible causes**:
1. Prompt is too vague
2. Requesting deprecated Manim features
3. LLM hallucinating

**Solution**:
- Be more specific in prompts
- Check server logs for error patterns
- Try simpler prompts first

---

## Performance Metrics

### Expected Timings (with Mistral AI)

| Operation | Time |
|-----------|------|
| LLM Code Generation | 0.5-2s |
| Manim Rendering (low quality) | 3-10s |
| Total (success on attempt 1) | 5-15s |
| Total (with 1 retry) | 10-25s |

### API Rate Limits (Mistral AI Free Tier)

- **Requests per day**: 14,400
- **Requests per minute**: 30
- **Tokens per minute**: 14,400

---

## Next Steps

### Phase 4: Video Storage & Public URLs
- Integrate Cloudflare R2 for video storage
- Return public URLs instead of local paths
- Implement video cleanup policies

### Phase 5: Frontend Interface
- Build web UI for prompt submission
- Real-time status updates via WebSockets
- Video player with download button

### Phase 6: Advanced Features
- Custom scene templates
- Video editing (trim, merge)
- Batch processing
- User authentication

---

## Files Changed

| File | Status | Description |
|------|--------|-------------|
| `main.py` |  Updated | Added LLM orchestration & self-correction loop |
| `requirements.txt` |  Updated | Added `mistralai==1.0.0` |
| `test_phase3.py` |  New | Phase 3 AI-driven test suite |
| `start_server_phase3.ps1` |  New | Server startup script with credentials |
| `PHASE3_SUMMARY.md` |  New | This file |

---

## Testing Checklist

- [ ] Server starts with LLM enabled
- [ ] POST /render accepts prompts
- [ ] Job ID is returned immediately
- [ ] Status endpoint shows "queued" → "processing" → "completed"
- [ ] Self-correction loop works (check logs)
- [ ] Video file is generated
- [ ] Legacy /render-code endpoint still works

---

## Your Credentials (Already Configured)

 **Redis Token**: `<set in .env file>`
 **Mistral AI API Key**: `<set in .env file>`

**Note**: You still need to get your full `UPSTASH_REDIS_REST_URL` from the Upstash dashboard. It should look like: `https://xxxxx-xxxxx.upstash.io`

---

## Ready to Test?

1. **Update Redis URL** in `start_server_phase3.ps1` with your actual Upstash URL
2. **Run**: `.\start_server_phase3.ps1`
3. **In a new terminal**: `python test_phase3.py`
4. **Watch the magic happen!** 

---

**Questions or issues?** Check the server logs or refer to `PHASE2_SETUP.md` for Redis setup.
