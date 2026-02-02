# Manim AI Frontend - Premium Chat Interface

A ultra-smooth, modern chat interface for generating Manim videos with AI.

##  Features

- **Premium UI/UX** - Inspired by modern AI chat interfaces
- **Ultra-Smooth Animations** - Powered by Framer Motion
- **Real-time Video Generation** - Watch your prompts transform into videos
- **Video Gallery** - View, download, and share generated videos
- **Responsive Design** - Works beautifully on all devices

##  Quick Start

### Prerequisites

- Node.js 18+ installed
- Manim AI Backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

##  Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icons
- **Axios** - HTTP client

##  Usage

1. Start the backend API server (port 8000)
2. Start the frontend dev server (port 3000)
3. Open `http://localhost:3000` in your browser
4. Type a video description (e.g., "A blue circle moving to the right")
5. Press Enter or wait for generation to complete
6. View your generated video in the gallery below

##  Customization

### Colors

Edit `tailwind.config.js` to customize the color scheme:

```js
colors: {
  'dark-bg': '#000000',
  'input-surface': '#1E1E20',
  'text-primary': '#E3E3E3',
  // ... more colors
}
```

### API Endpoint

To change the backend URL, edit `vite.config.js`:

```js
proxy: {
  '/api': {
    target: 'http://your-api-url:8000',
    // ...
  }
}
```

##  Example Prompts

- "A red square rotating 360 degrees"
- "Write 'Hello World' with a fade in effect"
- "A sine wave animation"
- "Two circles switching positions"
- "A circle transforming into a square"

##  Troubleshooting

### CORS Errors

Make sure your backend has CORS enabled for `http://localhost:3000`

### Videos not loading

Check that the Supabase Storage bucket is public and accessible

### Polling timeout

Default timeout is 5 minutes. Adjust in `ChatInterface.jsx` if needed

##  License

MIT
