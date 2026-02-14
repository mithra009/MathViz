#  Quick Start Guide - Phase 4 Complete Setup

##  Setup Status

### Completed:
-  Redis (State Management) - Connected
-  Mistral AI (LLM Provider) - Ready
-  Supabase Database - Connected  
-  Supabase Storage Bucket - Created
-  Database Schema - Executed
-  Cloudflare R2 - Removed (using Supabase Storage instead)

---

##  Next Steps

### Step 1: Start the API Server

```bash
cd c:\Users\mithr\Desktop\Manim\manim-image
C:/Users/mithr/Desktop/Manim/venv/Scripts/python.exe -m uvicorn main:app --reload --port 8000
```

The server will start at: **http://localhost:8000**

### Step 2: Access Interactive API Documentation

Open your browser and go to:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Step 3: Test the `/generate` Endpoint

#### Using the Browser (Swagger UI):

1. Go to http://localhost:8000/docs
2. Click on **POST /generate**
3. Click **"Try it out"**
4. Enter this test prompt:
   ```json
   {
     "prompt": "Create a blue circle that moves to the right"
   }
   ```
5. Click **Execute**
6. Copy the `job_id` from the response

#### Using cURL:

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Create a blue circle that moves to the right\"}"
```

#### Using Python:

```python
import requests

response = requests.post(
    "http://localhost:8000/generate",
    json={"prompt": "Create a blue circle that moves to the right"}
)
print(response.json())
```

### Step 4: Check Job Status

Use the `/status/{job_id}` endpoint:

```bash
curl http://localhost:8000/status/YOUR_JOB_ID
```

Or visit in browser:
```
http://localhost:8000/status/YOUR_JOB_ID
```

### Step 5: Monitor in Supabase Dashboard

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Table Editor**
4. View data in:
   - `render_jobs` - See job status in real-time
   - `generation_logs` - View LLM iterations and errors
   - `generated_videos` - See completed videos with URLs

5. Go to **Storage** → `manim-videos` bucket
   - View uploaded videos
   - Get public URLs

---

##  Example Test Prompts

Try these prompts to test different Manim features:

### Basic Shapes:
```
"Create a red square that rotates 360 degrees"
```

### Text Animation:
```
"Write the text 'Hello World' with a typewriter effect"
```

### Mathematical:
```
"Draw a sine wave that animates from left to right"
```

### Complex:
```
"Create a blue circle and a red square, make them switch positions"
```

---

##  Monitoring & Debugging

### Check Server Logs
The terminal where you ran `uvicorn` will show:
- Incoming requests
- LLM generation attempts  
- Rendering progress
- Upload status
- Any errors

### View Database Records

**Check all jobs:**
```sql
SELECT job_id, prompt, status, created_at 
FROM render_jobs 
ORDER BY created_at DESC 
LIMIT 10;
```

**Check logs for a specific job:**
```sql
SELECT iteration_number, log_level, message, timestamp
FROM generation_logs
WHERE job_id = 'your-job-id'
ORDER BY iteration_number;
```

**View completed videos:**
```sql
SELECT job_id, video_url, file_size_bytes, created_at
FROM generated_videos
ORDER BY created_at DESC;
```

---

##  Expected Workflow

1. **POST /generate** → Returns `job_id` immediately (202 Accepted)
2. **Background Processing:**
   - Record created in `render_jobs` table (status: pending)
   - LLM generates Manim code (logged in `generation_logs`)
   - Status updates to: processing → rendering
   - Manim executes code and renders video
   - Video uploads to Supabase Storage (status: uploading)
   - Record created in `generated_videos` table
   - Status updates to: completed
3. **GET /status/{job_id}** → Returns current status and video URL when done

---

##  Troubleshooting

### Server won't start:
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Use a different port
uvicorn main:app --reload --port 8001
```

### Database connection issues:
- Verify tables exist in Supabase Table Editor
- Check if RLS (Row Level Security) is disabled for development
- Confirm API key is correct in `.env`

### Storage bucket issues:
- Make sure bucket is **public** in Supabase Dashboard
- Check bucket name matches: `manim-videos`
- Verify storage is enabled in your Supabase project

### Rendering fails:
- Check `generation_logs` table for error details
- Verify Manim is installed: `manim --version`
- Check system has enough disk space
- Review iteration attempts (max 3 retries)

---

##  API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/generate` | POST | Create new video render job |
| `/status/{job_id}` | GET | Get job status and result |
| `/docs` | GET | Interactive API documentation |
| `/redoc` | GET | Alternative API documentation |

---

##  Production Readiness Checklist

Before deploying to production:

- [ ] Enable Row Level Security (RLS) in Supabase
- [ ] Use service role key for backend operations
- [ ] Set up proper error monitoring (Sentry, etc.)
- [ ] Configure rate limiting on API endpoints
- [ ] Set up automated backups in Supabase
- [ ] Configure CDN caching for video URLs
- [ ] Set up monitoring dashboards
- [ ] Document API for end users
- [ ] Load test the system
- [ ] Set up CI/CD pipeline

---

##  Additional Resources

- **Project Documentation:** See `PHASE4_SETUP.md`
- **Database Schema:** See `supabase_schema.sql`
- **API Tests:** Run `test_api.py`
- **Health Check:** Run `health_check.py`

---

**You're all set! Start the server and create your first AI-generated Manim video! **
