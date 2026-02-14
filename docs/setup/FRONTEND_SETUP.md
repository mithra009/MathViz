#  Manim AI - Complete Setup Guide

## System Overview

You now have a complete **AI-powered video generation system**:

- **Backend API** (Python/FastAPI) - Generates videos from natural language
- **Frontend UI** (React/Vite) - Premium chat interface
- **Database** (Supabase) - Stores jobs, logs, and videos
- **Storage** (Supabase) - Hosts generated videos with public URLs

---

##  Installation & Setup

### 1. Backend Setup (Already Complete!)

Your backend is running on `http://localhost:8000`

### 2. Frontend Setup (New!)

```powershell
# Navigate to frontend directory
cd c:\Users\mithr\Desktop\Manim\manim-image\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at: **http://localhost:3000**

---

##  How to Use

### Step 1: Start Both Servers

**Terminal 1 - Backend:**
```powershell
cd c:\Users\mithr\Desktop\Manim\manim-image
C:/Users/mithr/Desktop/Manim/venv/Scripts/uvicorn.exe main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd c:\Users\mithr\Desktop\Manim\manim-image\frontend
npm run dev
```

### Step 2: Open the App

Visit **http://localhost:3000** in your browser

### Step 3: Generate Videos

1. Type a video description (e.g., "A blue circle moving to the right")
2. Press **Enter** or wait
3. Watch the loading animation while AI generates your video
4. Video appears in the gallery below when ready
5. Click to play, download, or share!

---

##  Example Prompts

### Simple Animations:
- "A red square rotating 360 degrees"
- "A blue circle bouncing up and down"
- "A yellow triangle moving in a circle"

### Text Animations:
- "Write 'Hello World' with a typewriter effect"
- "Show the text 'AI is amazing' fading in"
- "Display 'Manim AI' with a glow effect"

### Mathematical:
- "Draw a sine wave that animates from left to right"
- "Show the Pythagorean theorem with animation"
- "Animate a growing spiral"

### Complex Scenes:
- "A circle transforming into a square"
- "Two objects switching positions smoothly"
- "Create a flow chart with three connected boxes"

---

##  UI Features

### Ultra-Smooth Animations
- Framer Motion powers all transitions
- Micro-interactions on every element
- Smooth tooltips on hover
- Scale effects on button presses

### Smart Input
- Auto-resizing textarea
- Keyboard shortcuts (Enter to submit)
- Loading states with animations
- Real-time status updates

### Video Gallery
- Grid layout with responsive design
- Hover effects on video cards
- Play, download, and share buttons
- Automatic timestamp display

---

##  Configuration

### Backend URL

If your backend is on a different port, edit `frontend/vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:YOUR_PORT',
    // ...
  }
}
```

### Styling

Colors and theme can be customized in `frontend/tailwind.config.js`:

```javascript
colors: {
  'dark-bg': '#000000',        // Main background
  'input-surface': '#1E1E20',  // Input box background
  'text-primary': '#E3E3E3',   // Main text color
  // ... more
}
```

---

##  Architecture

```

                  User's Browser                      
            http://localhost:3000                     
                                                      
     
           React Frontend (Port 3000)             
    • Premium UI with Framer Motion               
    • Real-time polling for job status            
    • Video gallery with playback                 
     

                        HTTP API Calls
                        (via Vite proxy)
                       

           FastAPI Backend (Port 8000)                
  • POST /render - Submit video generation            
  • GET /status/{job_id} - Check progress             
  • Background job processing                         

                   
         
                                        
               
     Redis            Mistral    Supabase 
    (State)            AI        Database 
               (LLM)     & Storage
                         
```

---

##  Troubleshooting

### Frontend can't connect to backend

**Solution:** Check CORS is enabled in `main.py` (already done) and both servers are running

### Videos not displaying

**Solution:** Check the video URL in Supabase Dashboard → Storage → manim-videos

### "npm not found" error

**Solution:** Install Node.js from https://nodejs.org/ (LTS version recommended)

### Port 3000 already in use

**Solution:** Edit `frontend/vite.config.js` and change the port:
```javascript
server: {
  port: 3001, // or any other port
  // ...
}
```

---

##  You're Ready!

Your complete AI video generation system is now operational:

 Backend API with self-correction  
 Premium chat interface  
 Real-time video generation  
 Cloud storage and delivery  
 Database persistence  

**Start creating amazing videos!** 
