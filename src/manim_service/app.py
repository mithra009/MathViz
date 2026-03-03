"""
Phase 1, 2 & 3: Manim Rendering Node - AI-Driven Compute Layer
A lightweight FastAPI webhook receiver that accepts natural language prompts,
generates Manim code using LLMs, executes with self-correction, and tracks
state in Redis. Implements iterative test-time compute for high reliability.

UPDATED: 2026-02-23 20:36 - ThreeDScene detection fixed with colon patterns
"""

import os
import uuid
import subprocess
import signal
import threading
import logging
import json
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from upstash_redis import Redis
from mistralai import Mistral
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Phase 2: Environment Configuration for Upstash Redis
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")

# Phase 3: Environment Configuration for Mistral AI (LLM Provider)
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Phase 4: Environment Configuration for Supabase Database & Storage
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# Use service role key for backend operations (has full permissions)
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "manim-videos")

# Initialize Redis client (optional - gracefully handle missing credentials)
redis_client = None
if REDIS_URL and REDIS_TOKEN:
    try:
        redis_client = Redis(url=REDIS_URL, token=REDIS_TOKEN)
        logger.info("Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis client: {e}")
        logger.warning("Service will run without state management")
else:
    logger.warning("Redis credentials not provided - running in stateless mode")

# Initialize Mistral AI client (Phase 3 - LLM for code generation)
mistral_client = None
if MISTRAL_API_KEY:
    try:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
        logger.info("Mistral AI client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Mistral client: {e}")
        logger.warning("Service will run without LLM code generation")
else:
    logger.warning("Mistral API key not provided - LLM features disabled")

# Initialize Supabase client (Phase 4 - Database & Storage)
# Service role client for backend operations (full permissions, bypasses RLS)
supabase_client: Optional[Client] = None
# Anon client for user-facing auth operations (respects RLS)
supabase_auth_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully (Database + Storage)")
        
        # Verify storage bucket exists
        try:
            supabase_client.storage.get_bucket(SUPABASE_STORAGE_BUCKET)
            logger.info(f"Supabase Storage bucket '{SUPABASE_STORAGE_BUCKET}' verified")
        except Exception as bucket_error:
            logger.warning(f"Storage bucket '{SUPABASE_STORAGE_BUCKET}' may not exist. Create it in Supabase dashboard.")
            logger.warning(f"Bucket error: {bucket_error}")
            
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        logger.warning("Service will run without database and storage persistence")
else:
    logger.warning("Supabase credentials not provided - database and storage features disabled")

# Initialize anon client for auth
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase_auth_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("Supabase Auth client initialized (anon key)")
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase Auth client: {e}")

# Initialize FastAPI application
app = FastAPI(
    title="Manim Rendering Node",
    description="AI-driven serverless compute layer: natural language → Manim code → video with self-correction",
    version="3.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phase 3: LLM Prompt Templates
SYSTEM_PROMPT = r"""You are a world-class Manim (Community Edition v0.18+) code generator.
Your goal is to produce **visually stunning, broadcast-quality** mathematical animations.

CRITICAL RULES:
1. Use ONLY manim Community Edition syntax (from manim import *)
2. NEVER use manimlib or old Manim syntax
3. ALWAYS create exactly ONE class that inherits from Scene or ThreeDScene
4. Use clear, descriptive class names (e.g., LaplacianVisualization, not Scene1)
5. Always include self.wait() at the end of the animation
6. Use proper indentation (4 spaces)
7. For 3D scenes, use ThreeDScene instead of Scene

LAYOUT & POSITIONING — CRITICAL to prevent overlapping:
- ALWAYS use .to_edge(UP) for titles/headings, then .next_to(title, DOWN, buff=0.5) for content below
- NEVER place objects at the same position — always use .shift(), .to_edge(), .next_to() with adequate buff
- Use buff=0.4 to 0.8 between adjacent elements (NEVER less than 0.3)
- For multi-step content: clear previous objects with FadeOut before showing new ones, OR
  shift old content up/aside before adding new content below
- Use .scale_to_fit_width(config.frame_width - 2) if text/formulas might be too wide
- For VGroups with multiple items, use .arrange(DOWN, buff=0.5) or .arrange(RIGHT, buff=0.5)
- Title goes to_edge(UP), main content stays at ORIGIN or slightly below, footnotes to_edge(DOWN)
- When showing equations + explanatory text together, put text ABOVE or BELOW the equation with .next_to(eq, DOWN, buff=0.5), never on top
- Before animating new content, ALWAYS check if previous content overlaps and FadeOut or reposition it
- Use .to_corner(UL), .to_corner(UR), etc. for corner placement
- Maximum font_size for formulas: 40 (to avoid overflow). Use 32-36 for complex LaTeX expressions

GRAPHS/AXES OVERLAP PREVENTION — EXTREMELY IMPORTANT:
- When a scene has BOTH a title AND a graph/axes, you MUST shrink the axes so they fit BELOW the title
- ALWAYS scale axes: axes.scale(0.6) or axes.scale(0.65) when there is a title present
- ALWAYS shift axes down: axes.shift(DOWN * 0.5) after scaling, or use axes.next_to(title, DOWN, buff=0.4)
- Set y_range to only what is needed — do NOT let the y-axis extend above the title
- The Manim frame is 8 units wide x ~4.5 units tall (for 16:9). Title at top uses ~0.8 units. So axes must fit in ~3.5 units
- For x_range and y_range, use tight ranges. For example y_range=[0, 10, 2] instead of y_range=[0, 100, 10]
- Always test mentally: if your y-axis goes from 0-10 with scale(0.6), it takes 6 units — TOO TALL. Use scale(0.45) or reduce y_range.
- FORMULA: max_axes_scale = 3.2 / (y_range_max - y_range_min). If y_range spans 10 units, scale must be ≤ 0.32
- Place the equation label OUTSIDE the graph area, e.g., to_corner(UR) or next_to(axes, RIGHT)
- Prefer using x_length and y_length params in Axes() to control physical size:
  Axes(x_range=[...], y_range=[...], x_length=6, y_length=3) — this guarantees the axes fit
- Data points (Dot) plotted on axes will stay within the axes bounds automatically if you use axes.c2p(x, y)
- NEVER let plotted elements extend above the top 0.8 units of the frame (that space is reserved for titles)

QUALITY GUIDELINES — follow these to make animations look professional:
- Use smooth animations with appropriate run_time (e.g., 1.5-2.5 seconds per animation)
- Add gentle pauses between animation steps (self.wait(0.5) to self.wait(2))
- Use color palettes effectively: BLUE, TEAL, GREEN, YELLOW, GOLD, RED, PURPLE, PINK, WHITE
- Apply .set_color(), .set_fill(opacity=...), .set_stroke(width=...) for visual richness
- Group related objects with VGroup and animate them together
- Use rate_func (e.g., smooth, there_and_back, ease_in_out_sine) for polished motion
- For titles/labels, use font_size=42 for titles, 32 for subtitles, 24-28 for labels
- Add subtle background elements or reference frames when appropriate
- Use .animate.shift(), .animate.scale(), .animate.set_color() for fluid transitions
- Prefer ReplacementTransform over Transform when morphing between objects
- Use SurroundingRectangle, Brace, Arrow to annotate and highlight key parts
- For graphs, use smooth curves and label axes clearly
- When showing step-by-step derivations, FadeOut previous steps or shift them up before showing next

TEXT AND MATH RENDERING (Full LaTeX is available):
- Use Text() for plain text (e.g., Text("Hello World", font_size=48))
- Use MathTex() for LaTeX math (e.g., MathTex(r"e^{i\pi} + 1 = 0"))
- Use Tex() for mixed text+math (e.g., Tex(r"The formula is $E = mc^2$"))
- ALWAYS use raw strings (r"...") for LaTeX to avoid escape issues
- MathTex supports full LaTeX: fractions, integrals, matrices, Greek letters, etc.
- For axis labels, you may use MathTex() for math symbols or Text() for words

Common animations: Create, Write, FadeIn, FadeOut, Transform, ReplacementTransform,
                   GrowFromCenter, GrowArrow, DrawBorderThenFill, Indicate, Circumscribe,
                   AnimationGroup, LaggedStart, Succession, MoveAlongPath
Common 2D objects: Circle, Square, Rectangle, Text, Tex, MathTex, VGroup, Dot, Arrow,
                   Line, DashedLine, Axes, NumberPlane, NumberLine, BarChart,
                   SurroundingRectangle, Brace, DecimalNumber, Integer,
                   Polygon, RegularPolygon, Star, Annulus, AnnularSector, Sector
Common 3D objects: Sphere, Cube, Cylinder, Cone, Torus, Surface, ThreeDAxes,
                   ParametricSurface, Arrow3D, Line3D, Dot3D

Example 2D with Math (note proper layout spacing):
```python
from manim import *

class QuadraticFormula(Scene):
    def construct(self):
        title = Text("Quadratic Formula", font_size=42, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.wait(0.5)
        
        equation = MathTex(r"ax^2 + bx + c = 0", font_size=36, color=WHITE)
        equation.next_to(title, DOWN, buff=0.6)
        self.play(Write(equation))
        self.wait(0.5)
        
        formula = MathTex(r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", font_size=38)
        formula.next_to(equation, DOWN, buff=0.8)
        self.play(Write(formula), run_time=2)
        
        box = SurroundingRectangle(formula, color=YELLOW, buff=0.3)
        self.play(Create(box))
        self.wait(2)
```

Example 2D Graph (note x_length/y_length to control size, and positioning below title):
```python
from manim import *

class SimpleGraph(Scene):
    def construct(self):
        title = Text("Parabola", font_size=42, color=BLUE).to_edge(UP, buff=0.3)
        self.play(Write(title))
        
        axes = Axes(
            x_range=[-3, 3, 1], y_range=[-1, 9, 2],
            x_length=6, y_length=3,
            axis_config={"include_numbers": True}
        ).next_to(title, DOWN, buff=0.3)
        labels = axes.get_axis_labels(x_label="x", y_label="y")
        graph = axes.plot(lambda x: x**2, color=BLUE, x_range=[-3, 3])
        graph_label = axes.get_graph_label(graph, label=MathTex(r"x^2"), x_val=2, direction=UR)
        self.play(Create(axes), Write(labels), run_time=1.5)
        self.play(Create(graph), Write(graph_label), run_time=2)
        self.wait(2)
```

Example 3D:
```python
from manim import *

class SphereVisualization(ThreeDScene):
    def construct(self):
        axes = ThreeDAxes()
        sphere = Sphere(radius=1.5, resolution=(32, 32)).set_color(BLUE).set_opacity(0.7)
        self.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
        self.add(axes)
        self.play(Create(sphere), run_time=2)
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(4)
```

MANDATORY: Your response must start with 'from manim import *' followed by exactly one class definition.
Return ONLY the Python code, no explanations or markdown formatting."""

def generate_manim_code(prompt: str, error_feedback: Optional[str] = None) -> str:
    """
    Phase 3: Generate Manim code using Mistral AI
    
    Args:
        prompt: User's natural language description
        error_feedback: Optional error message from previous attempt (for self-correction)
    
    Returns:
        Generated Python code as string
    """
    if not mistral_client:
        raise HTTPException(
            status_code=503,
            detail="LLM code generation not available - Mistral API key not configured"
        )
    
    # Build messages for LLM
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    if error_feedback:
        # Self-correction: include previous error
        messages.append({
            "role": "user",
            "content": f"Previous attempt failed with this error:\n{error_feedback}\n\nOriginal request: {prompt}\n\nGenerate corrected code that fixes this error."
        })
    else:
        # Initial generation
        messages.append({
            "role": "user",
            "content": f"Generate Manim code for: {prompt}"
        })
    
    try:
        response = mistral_client.chat.complete(
            model="mistral-large-latest",  # Mistral's most capable model for highest quality code
            messages=messages,
            temperature=0.3,  # Slightly higher for more creative, detailed animations
            max_tokens=8192   # More room for complex, high-quality scenes
        )
        
        code = response.choices[0].message.content.strip()
        
        # Extract code from markdown blocks if present
        if "```python" in code:
            parts = code.split("```python", 1)
            if len(parts) > 1:
                code = parts[1].split("```", 1)[0].strip()
        elif "```" in code:
            parts = code.split("```", 1)
            if len(parts) > 1:
                code = parts[1].split("```", 1)[0].strip()
        
        # Remove any leading/trailing whitespace and ensure it starts with imports
        code = code.strip()
        
        logger.info(f"Generated code preview (first 300 chars): {code[:300]}")
        
        return code
        
    except Exception as e:
        logger.error(f"LLM code generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate code: {str(e)}"
        )


def extract_scene_name(code: str) -> Optional[str]:
    """
    Phase 3: Extract the Scene class name from generated code
    
    Args:
        code: Python code string
    
    Returns:
        Scene class name or None if not found
    """
    # Try multiple patterns to match Scene classes
    patterns = [
        r'class\s+(\w+)\s*\(\s*Scene\s*\):',           # class Name(Scene):
        r'class\s+(\w+)\s*\(\s*ThreeDScene\s*\):',    # class Name(ThreeDScene):
        r'class\s+(\w+)\s*\(\s*manim\.Scene\s*\):',   # class Name(manim.Scene):
        r'class\s+(\w+)\s*\(\s*manim\.ThreeDScene\s*\):',  # class Name(manim.ThreeDScene):
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, code, re.MULTILINE)
        if match:
            scene_name = match.group(1)
            logger.info(f"Scene class detected with pattern {i}: {scene_name}")
            return scene_name
    
    # Log the code snippet for debugging if no match found
    logger.error(f"Could not extract Scene class from {len(code)} chars of code:")
    logger.error(f"Full code:\n{code}")
    logger.error(f"Checking class lines:")
    for line in code.split('\n'):
        if 'class ' in line:
            logger.error(f"  Found class line: {repr(line)}")
    return None

# Pydantic models for request/response validation
class RenderRequest(BaseModel):
    """Request payload for /render endpoint - Phase 3: Accepts natural language prompts"""
    prompt: str = Field(..., description="Natural language description of the animation to create")
    quality: Optional[str] = Field(default="h", description="Render quality: l(low), m(medium), h(high), k(4k)")
    max_retries: Optional[int] = Field(default=5, description="Maximum self-correction attempts")
    user_id: Optional[str] = Field(default=None, description="Authenticated user ID")

class RenderRequestLegacy(BaseModel):
    """Legacy request format for backward compatibility (Phase 1/2)"""
    code: str = Field(..., description="Manim Python script to execute")
    scene_name: str = Field(..., description="Target scene class name to render")
    quality: Optional[str] = Field(default="h", description="Render quality: l(low), m(medium), h(high), k(4k)")

class RenderResponse(BaseModel):
    """Response payload for /render endpoint"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(default="accepted", description="Job acceptance status")
    message: str = Field(..., description="Human-readable status message")

class HealthResponse(BaseModel):
    """Response payload for /health endpoint"""
    status: str = Field(default="healthy", description="Service health status")
    message: str = Field(..., description="Health check message")

class JobStatusResponse(BaseModel):
    """Response payload for /status/{job_id} endpoint"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: queued, processing, completed, failed")
    created_at: Optional[str] = Field(None, description="Job creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    video_url: Optional[str] = Field(None, description="Video URL if completed")
    video_path: Optional[str] = Field(None, description="Local video path if completed")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================
# Phase 5: Auth Pydantic Models
# ============================================================
class SignUpRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    display_name: Optional[str] = Field(default=None, description="Display name")

class SignInRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="Password")

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None
    session: Optional[dict] = None

class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    total_videos: int = 0
    created_at: Optional[str] = None

class VideoHistoryItem(BaseModel):
    job_id: str
    prompt: str
    video_url: Optional[str] = None
    status: str
    created_at: str
    quality: Optional[str] = None


# ============================================================
# Phase 5: Auth Helper - Extract user from token
# ============================================================
async def get_current_user(authorization: Optional[str] = Header(default=None)) -> Optional[dict]:
    """Extract user from Bearer token. Returns None if not authenticated (allows anonymous usage)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    if not supabase_client:
        return None
    
    try:
        user_response = supabase_client.auth.get_user(token)
        if user_response and user_response.user:
            return {
                "id": str(user_response.user.id),
                "email": user_response.user.email
            }
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
    return None


# Helper function: Update job status in Redis
# Track active subprocesses per job_id so they can be killed on cancel
_active_processes: Dict[str, subprocess.Popen] = {}
_active_processes_lock = threading.Lock()


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in Redis if client is available"""
    if not redis_client:
        return
    
    try:
        job_data = {
            "job_id": job_id,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        job_data.update(kwargs)
        
        # Store with 7-day TTL (604800 seconds)
        redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=604800)
        logger.info(f"[Job {job_id}] Redis status updated: {status}")
    except Exception as e:
        logger.error(f"[Job {job_id}] Failed to update Redis: {e}")


# Phase 4: Upload video to Supabase Storage
def upload_to_supabase_storage(file_path: Path, job_id: str, scene_name: str) -> Optional[str]:
    """
    Upload video to Supabase Storage bucket and return public URL
    
    Args:
        file_path: Local path to the video file
        job_id: Unique job identifier for organizing files
        scene_name: Scene class name for file naming
    
    Returns:
        Public URL if upload successful, None otherwise
    """
    if not supabase_client or not SUPABASE_STORAGE_BUCKET:
        logger.warning("Supabase Storage not configured - skipping upload")
        return None
    
    try:
        # Generate storage path: videos/{job_id}/{scene_name}.mp4
        storage_path = f"videos/{job_id}/{scene_name}.mp4"
        
        logger.info(f"[Job {job_id}] Uploading to Supabase Storage: {storage_path}")
        
        # Read video file
        with open(file_path, 'rb') as video_file:
            video_data = video_file.read()
        
        # Upload to Supabase Storage
        response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            path=storage_path,
            file=video_data,
            file_options={
                "content-type": "video/mp4",
                "x-upsert": "true"  # Overwrite if exists
            }
        )
        
        # Get public URL
        public_url = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
        
        logger.info(f"[Job {job_id}] Video uploaded successfully to Supabase Storage")
        logger.info(f"[Job {job_id}] Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Supabase Storage upload failed: {e}", exc_info=True)
        return None


# Phase 3: Helper function to extract scene class name from code
def extract_scene_name(code: str) -> Optional[str]:
    """Extract the Scene class name from generated code"""
    try:
        # Match patterns for Scene, ThreeDScene, and module-qualified versions
        patterns = [
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*Scene\s*\):',
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*ThreeDScene\s*\):',
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*manim\.Scene\s*\):',
            r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*manim\.ThreeDScene\s*\):',
        ]
        for pattern in patterns:
            match = re.search(pattern, code)
            if match:
                logger.info(f"Scene class found: {match.group(1)}")
                return match.group(1)
        return None
    except Exception as e:
        logger.error(f"Failed to extract scene name: {e}")
        return None


# Phase 3: Self-Correction Wrapper with LLM Retry Logic
def execute_manim_with_retries(
    job_id: str, 
    prompt: str, 
    quality: str = "h",
    max_retries: int = 3,
    user_id: Optional[str] = None
):
    """
    Phase 3: AI-Driven Rendering with Self-Correction Loop
    
    This function implements Test-Time Compute:
    1. Generate Manim code from natural language prompt
    2. Execute the code
    3. If it fails, send error back to LLM for correction
    4. Retry up to max_retries times
    
    Args:
        job_id: Unique identifier for this render job
        prompt: Natural language description from user
        quality: Render quality flag (l/m/h/k)
        max_retries: Maximum correction attempts (default 3)
    """
    update_job_status(job_id, "processing", prompt=prompt, attempt=1, max_retries=max_retries)
    
    error_feedback = None
    
    def is_cancelled():
        """Check if the job has been cancelled by the user"""
        if not redis_client:
            return False
        try:
            job_data_json = redis_client.get(f"job:{job_id}")
            if job_data_json:
                job_data = json.loads(job_data_json)
                return job_data.get("status") == "cancelled"
        except Exception:
            pass
        return False

    for attempt in range(1, max_retries + 1):
        # Check for cancellation before each attempt
        if is_cancelled():
            logger.info(f"[Job {job_id}] Cancelled by user before attempt {attempt}")
            return
        
        logger.info(f"[Job {job_id}] Attempt {attempt}/{max_retries}")
        
        try:
            # Step 1: Generate code using LLM
            logger.info(f"[Job {job_id}] Generating Manim code from prompt: {prompt[:100]}...")
            code = generate_manim_code(prompt, error_feedback)
            logger.info(f"[Job {job_id}] Code generated ({len(code)} chars)")
            
            # Step 2: Extract scene name
            scene_name = extract_scene_name(code)
            if not scene_name:
                error_msg = "Generated code does not contain a Scene class. Remember to create a class that inherits from Scene."
                logger.error(f"[Job {job_id}] {error_msg}")
                error_feedback = error_msg
                update_job_status(
                    job_id, 
                    "processing", 
                    attempt=attempt + 1,
                    last_error=error_msg,
                    generated_code=code[:500]
                )
                continue
            
            logger.info(f"[Job {job_id}] Extracted scene name: {scene_name}")
            update_job_status(
                job_id,
                "processing",
                attempt=attempt,
                scene_name=scene_name,
                generated_code=code[:500]
            )
            
            # Check for cancellation before rendering
            if is_cancelled():
                logger.info(f"[Job {job_id}] Cancelled by user before rendering")
                return
            
            # Step 3: Execute Manim rendering
            result = execute_manim_core(job_id, code, scene_name, quality)
            
            if result.get("cancelled"):
                logger.info(f"[Job {job_id}] Render was cancelled - stopping")
                return
            
            if result["success"]:
                # Check cancellation one final time before saving
                if is_cancelled():
                    logger.info(f"[Job {job_id}] Cancelled after render - skipping save")
                    return
                
                # Success! Update Redis and return
                logger.info(f"[Job {job_id}] Render succeeded on attempt {attempt}")
                
                # Phase 4: Include CDN URL if available
                status_data = {
                    "video_path": result["video_path"],
                    "file_size": result.get("file_size"),
                    "scene_name": scene_name,
                    "quality": quality,
                    "attempts": attempt,
                    "final_code": code
                }
                
                if "storage_url" in result:
                    status_data["video_url"] = result["storage_url"]
                
                update_job_status(job_id, "completed", **status_data)
                
                # Phase 5: Save to Supabase DB for user history
                if supabase_client:
                    try:
                        # Insert render_jobs record
                        job_record = {
                            "job_id": job_id,
                            "prompt": prompt,
                            "status": "completed",
                            "retry_count": attempt,
                            "metadata": {"quality": quality, "scene_name": scene_name}
                        }
                        if user_id:
                            job_record["user_id"] = user_id
                        supabase_client.table("render_jobs").upsert(job_record, on_conflict="job_id").execute()
                        
                        # Insert generated_videos record
                        video_record = {
                            "job_id": job_id,
                            "video_url": result.get("storage_url", ""),
                            "file_size_bytes": result.get("file_size"),
                            "resolution": {"l": "480p", "m": "720p", "h": "1080p", "k": "4K"}.get(quality, "1080p"),
                            "metadata": {"scene_name": scene_name, "attempts": attempt}
                        }
                        if user_id:
                            video_record["user_id"] = user_id
                        supabase_client.table("generated_videos").insert(video_record).execute()
                        logger.info(f"[Job {job_id}] Saved to Supabase DB (user_id={user_id})")
                    except Exception as db_err:
                        logger.error(f"[Job {job_id}] Failed to save to Supabase DB: {db_err}")
                
                return
            else:
                # Manim execution failed, prepare feedback for next attempt
                error_feedback = result["error"]
                
                # Detect LaTeX errors and provide specific guidance
                if "latex" in error_feedback.lower() or "tex" in error_feedback.lower():
                    error_feedback += "\n\nNote: Full LaTeX IS available. If you got a LaTeX error, check for: unescaped special characters, missing braces, or unsupported packages. Use raw strings r'...' for all LaTeX. Prefer MathTex() for math and Text() for plain text."
                
                logger.warning(f"[Job {job_id}] Attempt {attempt} failed: {error_feedback[:200]}...")
                update_job_status(
                    job_id,
                    "processing",
                    attempt=attempt + 1,
                    last_error=error_feedback[:500],
                    generated_code=code[:500]
                )
                
        except Exception as e:
            error_feedback = str(e)
            logger.error(f"[Job {job_id}] Attempt {attempt} crashed: {e}", exc_info=True)
            update_job_status(
                job_id,
                "processing",
                attempt=attempt + 1,
                last_error=str(e)[:500]
            )
    
    # All retries exhausted - mark as failed
    logger.error(f"[Job {job_id}] All {max_retries} attempts failed")
    update_job_status(
        job_id,
        "failed",
        error=f"Failed after {max_retries} attempts. Last error: {error_feedback[:500]}",
        attempts=max_retries
    )


# Core Manim Execution Engine (refactored from Phase 1/2)
def execute_manim_core(job_id: str, code: str, scene_name: str, quality: str = "h") -> Dict:
    """
    Phase 3 Refactor: Core Manim rendering logic (now returns Dict instead of updating Redis)
    
    This function handles:
    - Script materialization to /tmp
    - Subprocess execution with sandboxing
    - Constraint #5: Caching suppression via --disable_caching
    - Constraint #4: All I/O operations redirected to /tmp
    - Error capture for self-correction
    - Ephemeral cleanup
    
    Args:
        job_id: Unique identifier for this render job
        code: Manim Python script as string
        scene_name: Target scene class to render
        quality: Render quality flag (l/m/h/k)
    
    Returns:
        Dict with keys: success (bool), video_path (str), file_size (int), error (str)
    """
    # Constraint #4: Strict Filesystem Redirection
    # Use platform-appropriate temp directory (cross-platform)
    import tempfile
    tmp_dir = Path(tempfile.gettempdir())
    script_path = tmp_dir / f"{job_id}_attempt.py"
    media_dir = tmp_dir / f"media_{job_id}"
    
    logger.info(f"[Job {job_id}] Starting Manim render for scene: {scene_name}")
    
    try:
        # Script Materialization: Write code to temporary file
        logger.info(f"[Job {job_id}] Writing script to {script_path}")
        script_path.write_text(code, encoding='utf-8')
        
        # Build Manim CLI command
        # Constraint #5: Caching Suppression - inject --disable_caching flag
        quality_flag = f"-q{quality}"  # -ql (low), -qm (medium), -qh (high), -qk (4k)
        
        # Use sys.executable to ensure we use the same Python environment
        import sys
        manim_command = [
            sys.executable,
            "-m",
            "manim",
            quality_flag,
            "--disable_caching",  # Constraint #5: Prevent disk exhaustion
            "--media_dir", str(media_dir),  # Constraint #4: Redirect to /tmp
            str(script_path),
            scene_name
        ]
        
        logger.info(f"[Job {job_id}] Executing command: {' '.join(manim_command)}")
        
        # Subprocess Execution with Popen so we can cancel mid-render
        proc = subprocess.Popen(
            manim_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Register the process so the cancel endpoint can kill it
        with _active_processes_lock:
            _active_processes[job_id] = proc
        
        try:
            stdout, stderr = proc.communicate(timeout=300)  # 5 minute timeout
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            with _active_processes_lock:
                _active_processes.pop(job_id, None)
            raise
        finally:
            with _active_processes_lock:
                _active_processes.pop(job_id, None)
        
        # Check if process was killed (cancelled)
        # On Linux, killed processes have negative returncode (-9 for SIGKILL)
        # On Windows, TerminateProcess gives returncode 1, so also check Redis
        was_killed_by_signal = proc.returncode != 0 and proc.returncode < 0
        was_cancelled_in_redis = False
        if redis_client:
            try:
                job_data_json = redis_client.get(f"job:{job_id}")
                if job_data_json:
                    job_data = json.loads(job_data_json)
                    was_cancelled_in_redis = job_data.get("status") == "cancelled"
            except Exception:
                pass
        
        if was_killed_by_signal or was_cancelled_in_redis:
            logger.info(f"[Job {job_id}] Process was cancelled (returncode={proc.returncode}, redis_cancelled={was_cancelled_in_redis})")
            return {"success": False, "error": "Cancelled by user", "cancelled": True}
        
        if proc.returncode != 0:
            error_msg = f"Manim execution failed:\n{stderr if stderr else stdout}"
            return {"success": False, "error": error_msg}
        
        logger.info(f"[Job {job_id}] Render completed successfully")
        logger.info(f"[Job {job_id}] STDOUT: {stdout}")
        
        # Find the generated video file
        video_files = list(media_dir.glob(f"**/{scene_name}.mp4"))
        if video_files:
            video_path = video_files[0]
            logger.info(f"[Job {job_id}] Video generated at: {video_path}")
            logger.info(f"[Job {job_id}] File size: {video_path.stat().st_size} bytes")
            
            # Check cancellation one more time before uploading
            if redis_client:
                try:
                    _jd = redis_client.get(f"job:{job_id}")
                    if _jd and json.loads(_jd).get("status") == "cancelled":
                        logger.info(f"[Job {job_id}] Cancelled - skipping storage upload")
                        return {"success": False, "error": "Cancelled by user", "cancelled": True}
                except Exception:
                    pass
            
            # Phase 4: Upload to Supabase Storage
            storage_url = upload_to_supabase_storage(video_path, job_id, scene_name)
            
            result_data = {
                "success": True,
                "video_path": str(video_path),
                "file_size": video_path.stat().st_size
            }
            
            # If Supabase Storage upload succeeded, add URL and clean up local file
            if storage_url:
                result_data["storage_url"] = storage_url
                logger.info(f"[Job {job_id}] Storage URL: {storage_url}")
                
                # Delete local file to save disk space
                try:
                    video_path.unlink()
                    logger.info(f"[Job {job_id}] Local video file deleted (uploaded to Supabase Storage)")
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Failed to delete local file: {e}")
            
            return result_data
        else:
            logger.warning(f"[Job {job_id}] No video file found in {media_dir}")
            return {
                "success": False,
                "error": "No video file generated - Manim completed but no output found"
            }
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"[Job {job_id}] Rendering timed out after 5 minutes")
        return {
            "success": False,
            "error": "Rendering timed out after 5 minutes - animation too complex or infinite loop"
        }
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Unexpected error: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }
        
    finally:
        # Ephemeral Cleanup: Aggressively delete temporary files
        try:
            if script_path.exists():
                script_path.unlink()
                logger.info(f"[Job {job_id}] Cleaned up script file: {script_path}")
        except Exception as e:
            logger.warning(f"[Job {job_id}] Failed to cleanup script: {e}")


# Legacy function for backward compatibility (Phase 1/2 direct code execution)
def execute_manim_legacy(job_id: str, code: str, scene_name: str, quality: str = "l"):
    """
    Legacy rendering function for backward compatibility with Phase 1/2 API
    Accepts pre-written code instead of prompts
    """
    update_job_status(job_id, "processing")
    
    result = execute_manim_core(job_id, code, scene_name, quality)
    
    if result["success"]:
        update_job_status(
            job_id,
            "completed",
            video_path=result["video_path"],
            file_size=result.get("file_size"),
            scene_name=scene_name,
            quality=quality
        )
    else:
        update_job_status(
            job_id,
            "failed",
            error=result["error"],
            scene_name=scene_name
        )
        
        # Optional: Clean up media directory after processing
        # Uncomment if you want to delete rendered videos after processing
        # try:
        #     if media_dir.exists():
        #         import shutil
        #         shutil.rmtree(media_dir)
        #         logger.info(f"[Job {job_id}] Cleaned up media directory: {media_dir}")
        # except Exception as e:
        #     logger.warning(f"[Job {job_id}] Failed to cleanup media: {e}")


# Core Endpoints

@app.get("/api", response_model=dict)
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Manim Rendering Node",
        "phase": "Phase 4 - Supabase Database & Storage Integration",
        "status": "operational",
        "redis_enabled": redis_client is not None,
        "llm_enabled": mistral_client is not None,
        "supabase_enabled": supabase_client is not None,
        "endpoints": {
            "health": "/health",
            "render": "/render (POST with prompt)",
            "render_legacy": "/render-code (POST with code)",
            "status": "/status/{job_id}"
        },
        "features": [
            "Natural language to Manim code generation",
            "Self-correction loop (up to 3 retries)",
            "Job state tracking in Redis",
            "Asynchronous background processing",
            "Zero-egress video delivery via Cloudflare R2"
        ]
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    GET /health - Synthetic Monitoring Endpoint
    
    Purpose: Used by external cron jobs (e.g., GitHub Actions) to keep
    the container "warm" and prevent scaling to zero on free-tier hosts.
    
    This artificial traffic mitigates cold start latency.
    """
    logger.info("Health check endpoint pinged")
    
    return HealthResponse(
        status="healthy",
        message="Manim Rendering Node is operational and ready to process requests"
    )


@app.post("/render", response_model=RenderResponse)
async def render(request: RenderRequest, background_tasks: BackgroundTasks, current_user: Optional[dict] = Depends(get_current_user)):
    """
    POST /render - Phase 3: AI-Driven Render Endpoint
    
    Purpose: Accept natural language prompts and generate Manim videos with self-correction
    
    Phase 3 Enhancement:
    - Accepts natural language prompts instead of code
    - Uses LLM to generate Manim code
    - Implements self-correction loop (retries on failure)
    - Automatically extracts scene names
    
    Args:
        request: RenderRequest containing prompt, quality, max_retries
        background_tasks: FastAPI background task manager
    
    Returns:
        RenderResponse with job_id and acceptance status
    """
    # Validate LLM is available
    if not mistral_client:
        raise HTTPException(
            status_code=503,
            detail="LLM code generation not available. Please configure MISTRAL_API_KEY environment variable."
        )
    
    # Generate unique job identifier
    job_id = str(uuid.uuid4())
    
    logger.info(f"[Job {job_id}] Received AI render request")
    logger.info(f"[Job {job_id}] Prompt: {request.prompt[:100]}...")
    
    # Validate quality parameter
    valid_qualities = ['l', 'm', 'h', 'k']
    if request.quality not in valid_qualities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid quality '{request.quality}'. Must be one of: {valid_qualities}"
        )
    
    # Validate max_retries
    if request.max_retries < 1 or request.max_retries > 10:
        raise HTTPException(
            status_code=400,
            detail="max_retries must be between 1 and 10"
        )
    
    # Phase 2 & 3: Initialize job in Redis with 'queued' status
    update_job_status(
        job_id,
        "queued",
        created_at=datetime.utcnow().isoformat(),
        prompt=request.prompt,
        quality=request.quality,
        max_retries=request.max_retries,
        mode="ai-generated"
    )
    
    # Delegate to Phase 3 self-correction pipeline
    # Phase 5: Pass user_id from auth token or request body
    user_id = None
    if current_user:
        user_id = current_user["id"]
    elif request.user_id:
        user_id = request.user_id
    
    background_tasks.add_task(
        execute_manim_with_retries,
        job_id=job_id,
        prompt=request.prompt,
        quality=request.quality,
        max_retries=request.max_retries,
        user_id=user_id
    )
    
    logger.info(f"[Job {job_id}] AI render job accepted and queued")
    
    # Immediately return acknowledgment
    return RenderResponse(
        job_id=job_id,
        status="accepted",
        message=f"AI render job {job_id} accepted. Code will be generated and executed with self-correction."
    )


@app.post("/render-code", response_model=RenderResponse)
async def render_code(request: RenderRequestLegacy, background_tasks: BackgroundTasks):
    """
    POST /render-code - Legacy Endpoint (Phase 1/2 Compatibility)
    
    Purpose: Direct code execution without LLM generation (for testing or advanced users)
    
    Args:
        request: RenderRequestLegacy containing code and scene_name
        background_tasks: FastAPI background task manager
    
    Returns:
        RenderResponse with job_id and acceptance status
    """
    # Generate unique job identifier
    job_id = str(uuid.uuid4())
    
    logger.info(f"[Job {job_id}] Received legacy render request for scene: {request.scene_name}")
    logger.info(f"[Job {job_id}] Code length: {len(request.code)} characters")
    
    # Validate quality parameter
    valid_qualities = ['l', 'm', 'h', 'k']
    if request.quality not in valid_qualities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid quality '{request.quality}'. Must be one of: {valid_qualities}"
        )
    
    # Initialize job in Redis
    update_job_status(
        job_id,
        "queued",
        created_at=datetime.utcnow().isoformat(),
        scene_name=request.scene_name,
        quality=request.quality,
        code_length=len(request.code),
        mode="direct-code"
    )
    
    # Delegate to legacy execution (no self-correction)
    background_tasks.add_task(
        execute_manim_legacy,
        job_id=job_id,
        code=request.code,
        scene_name=request.scene_name,
        quality=request.quality
    )
    
    logger.info(f"[Job {job_id}] Legacy render job accepted and queued")
    
    return RenderResponse(
        job_id=job_id,
        status="accepted",
        message=f"Render job {job_id} accepted and queued for processing"
    )


@app.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """
    POST /cancel/{job_id} - Cancel a running job
    
    Sets the job status to 'cancelled' in Redis so the background
    processing loop will stop at the next check point.
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="State management not available")
    
    try:
        job_data_json = redis_client.get(f"job:{job_id}")
        if not job_data_json:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job_data = json.loads(job_data_json)
        current_status = job_data.get("status")
        
        if current_status in ("completed", "failed", "cancelled"):
            return {"message": f"Job already {current_status}", "job_id": job_id}
        
        update_job_status(job_id, "cancelled", previous_status=current_status)
        
        # Kill the active subprocess if it's running
        with _active_processes_lock:
            proc = _active_processes.pop(job_id, None)
        if proc:
            try:
                proc.kill()
                logger.info(f"[Job {job_id}] Killed active rendering subprocess")
            except Exception as kill_err:
                logger.warning(f"[Job {job_id}] Failed to kill subprocess: {kill_err}")
        
        logger.info(f"[Job {job_id}] Cancelled by user (was: {current_status})")
        return {"message": "Job cancelled successfully", "job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Job {job_id}] Cancel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    GET /status/{job_id} - Job Status Query Endpoint
    
    Phase 2: Query job status from Redis
    
    Args:
        job_id: Unique job identifier
    
    Returns:
        JobStatusResponse with current job status and details
    """
    if not redis_client:
        raise HTTPException(
            status_code=503,
            detail="State management not available - Redis not configured"
        )
    
    try:
        # Query Redis for job data
        job_data_json = redis_client.get(f"job:{job_id}")
        
        if not job_data_json:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found or expired"
            )
        
        # Parse job data
        job_data = json.loads(job_data_json)
        
        logger.info(f"[Job {job_id}] Status queried: {job_data.get('status')}")
        
        return JobStatusResponse(**job_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Job {job_id}] Error querying status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query job status: {str(e)}"
        )


# ============================================================
# Phase 5: Authentication Endpoints
# ============================================================

@app.post("/auth/signup", response_model=AuthResponse)
async def signup(request: SignUpRequest):
    """Register a new user with email and password"""
    if not supabase_auth_client:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Sign up with Supabase Auth
        options = {}
        if request.display_name:
            options["data"] = {"display_name": request.display_name}
        
        response = supabase_auth_client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": options
        })
        
        if response.user:
            user_data = {
                "id": str(response.user.id),
                "email": response.user.email,
                "created_at": str(response.user.created_at) if response.user.created_at else None
            }
            session_data = None
            if response.session:
                session_data = {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_in": response.session.expires_in,
                    "token_type": "bearer"
                }
            return AuthResponse(
                success=True,
                message="Account created successfully. Please check your email to confirm.",
                user=user_data,
                session=session_data
            )
        else:
            return AuthResponse(success=False, message="Sign up failed. Please try again.")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Sign up failed: {error_msg}")
        if "already registered" in error_msg.lower() or "already been registered" in error_msg.lower():
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        raise HTTPException(status_code=400, detail=f"Sign up failed: {error_msg}")


@app.post("/auth/signin", response_model=AuthResponse)
async def signin(request: SignInRequest):
    """Sign in with email and password"""
    if not supabase_auth_client:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        response = supabase_auth_client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user and response.session:
            user_data = {
                "id": str(response.user.id),
                "email": response.user.email,
            }
            session_data = {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_in": response.session.expires_in,
                "token_type": "bearer"
            }
            return AuthResponse(
                success=True,
                message="Signed in successfully.",
                user=user_data,
                session=session_data
            )
        else:
            return AuthResponse(success=False, message="Invalid credentials.")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Sign in failed: {error_msg}")
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@app.post("/auth/signout")
async def signout(current_user: Optional[dict] = Depends(get_current_user)):
    """Sign out the current user"""
    return {"success": True, "message": "Signed out successfully."}


@app.get("/auth/me", response_model=UserProfileResponse)
async def get_me(current_user: Optional[dict] = Depends(get_current_user)):
    """Get current authenticated user's profile"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = supabase_client.table("user_profiles").select("*").eq("id", current_user["id"]).single().execute()
        if result.data:
            return UserProfileResponse(
                id=result.data["id"],
                email=result.data["email"],
                display_name=result.data.get("display_name"),
                total_videos=result.data.get("total_videos", 0),
                created_at=str(result.data.get("created_at", ""))
            )
    except Exception as e:
        logger.error(f"Failed to fetch profile: {e}")
    
    # Fallback: return basic info from token
    return UserProfileResponse(
        id=current_user["id"],
        email=current_user["email"],
        total_videos=0
    )


# ============================================================
# Phase 5: User History Endpoint
# ============================================================

@app.get("/user/history")
async def get_user_history(current_user: Optional[dict] = Depends(get_current_user)):
    """Get all videos created by the authenticated user"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated. Please sign in.")
    
    if not supabase_client:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        # Fetch user's render jobs with video URLs
        result = supabase_client.table("render_jobs").select(
            "job_id, prompt, status, created_at, metadata, generated_videos(video_url, file_size_bytes, resolution, created_at)"
        ).eq("user_id", current_user["id"]).order("created_at", desc=True).limit(50).execute()
        
        videos = []
        if result.data:
            for job in result.data:
                video_url = None
                if job.get("generated_videos") and len(job["generated_videos"]) > 0:
                    video_url = job["generated_videos"][0].get("video_url")
                
                videos.append({
                    "job_id": job["job_id"],
                    "prompt": job["prompt"],
                    "status": job["status"],
                    "video_url": video_url,
                    "quality": job.get("metadata", {}).get("quality", "h"),
                    "created_at": job["created_at"]
                })
        
        return {"videos": videos, "total": len(videos)}
        
    except Exception as e:
        logger.error(f"Failed to fetch user history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("=" * 80)
    logger.info("Manim Rendering Node - Phase 3: AI-Driven Compute with Self-Correction")
    logger.info("=" * 80)
    logger.info("Service starting up...")
    logger.info(f"Python version: {os.sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Temp directory: /tmp")
    logger.info("Phase 1 Constraints:")
    logger.info("   Constraint #1: Base Image Substitution (python:3.9-slim)")
    logger.info("   Constraint #2: Dependency Pruning & Minimalist Typography")
    logger.info("   Constraint #3: Container Layer Consolidation")
    logger.info("   Constraint #4: Strict Filesystem Redirection (/tmp)")
    logger.info("   Constraint #5: Caching Suppression (--disable_caching)")
    logger.info("   Constraint #6: Asynchronous API Orchestration")
    logger.info("Phase 2 Features:")
    if redis_client:
        logger.info("   Redis State Management: ENABLED")
        logger.info(f"   Redis URL: {REDIS_URL[:30]}...")
    else:
        logger.info("   Redis State Management: DISABLED (no credentials)")
    logger.info("Phase 3 Features:")
    if mistral_client:
        logger.info("   LLM Code Generation: ENABLED (Mistral AI)")
        logger.info("   Model: mistral-large-latest")
        logger.info("   Self-Correction Loop: ENABLED (max 3 retries)")
        logger.info("   Natural Language Processing: ENABLED")
    else:
        logger.info("   LLM Features: DISABLED (no Mistral API key)")
        logger.info("  ℹ Service will only accept pre-written code via /render-code")
    logger.info("Phase 4 Features:")
    if supabase_client:
        logger.info("   Supabase Database: ENABLED")
        logger.info("   Supabase Storage: ENABLED")
        logger.info(f"   Storage Bucket: {SUPABASE_STORAGE_BUCKET}")
        logger.info("   Job tracking, logs, and video metadata stored")
    else:
        logger.info("   Supabase: DISABLED (no credentials)")
        logger.info("  ℹ Videos will remain on local disk only")
    logger.info("=" * 80)
    logger.info("Service ready to accept render requests")
    logger.info("AI Mode: Use POST /render with {prompt: 'your description'}")
    logger.info("Legacy Mode: Use POST /render-code with {code: '...', scene_name: '...'}")
    logger.info("=" * 80)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Service shutting down...")

# Serve frontend static files (must be mounted after all API routes)
_frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    # Add /api/* aliases so the frontend (which uses /api/render etc.) works in production
    app.add_api_route("/api/render", render, methods=["POST"], response_model=RenderResponse)
    app.add_api_route("/api/status/{job_id}", get_job_status, methods=["GET"], response_model=JobStatusResponse)
    app.add_api_route("/api/cancel/{job_id}", cancel_job, methods=["POST"])
    # Phase 5: Auth and History API routes
    app.add_api_route("/api/auth/signup", signup, methods=["POST"], response_model=AuthResponse)
    app.add_api_route("/api/auth/signin", signin, methods=["POST"], response_model=AuthResponse)
    app.add_api_route("/api/auth/signout", signout, methods=["POST"])
    app.add_api_route("/api/auth/me", get_me, methods=["GET"], response_model=UserProfileResponse)
    app.add_api_route("/api/user/history", get_user_history, methods=["GET"])

    # Mount static assets
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    # Catch-all: serve index.html for all unmatched routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = _frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))

    @app.get("/")
    async def serve_root():
        return FileResponse(str(_frontend_dist / "index.html"))

    logger.info(f"Serving frontend from {_frontend_dist}")
else:
    logger.warning(f"Frontend dist not found at {_frontend_dist} - serving API only")

# Entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)