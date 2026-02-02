import { useState } from 'react'
import { motion } from 'framer-motion'
import ChatInterface from './components/ChatInterface'
import SingleVideoPlayer from './components/SingleVideoPlayer'

function App() {
  const [currentVideo, setCurrentVideo] = useState(null)

  const handleVideoGenerated = (videoData) => {
    setCurrentVideo(videoData)
  }

  return (
    <div className="min-h-screen bg-dark-bg text-white flex flex-col">
      {/* Header with glassmorphism */}
      <header className="sticky top-0 z-50 py-4 px-6 bg-dark-bg/80 backdrop-blur-md border-b border-gray-800/50 flex items-center gap-3">
        <motion.img 
          src="/logo.svg" 
          alt="MathViz Logo" 
          className="w-10 h-10"
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={{ type: "spring", stiffness: 400, damping: 10 }}
        />
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent tracking-wide">MathViz</h1>
          <p className="text-gray-500 text-xs">Math Visualization Tool</p>
        </div>
        {/* Subtle gradient accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-gray-600/50 to-transparent" />
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <ChatInterface onVideoGenerated={handleVideoGenerated} />
        {currentVideo && <SingleVideoPlayer video={currentVideo} />}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 border-t border-gray-800/50 bg-gradient-to-t from-gray-900/20 to-transparent">
        <p className="text-gray-600 text-sm">
          Developed by <span className="font-semibold bg-gradient-to-r from-gray-400 to-gray-300 bg-clip-text text-transparent">MITHRA</span>
        </p>
      </footer>
    </div>
  )
}

export default App
