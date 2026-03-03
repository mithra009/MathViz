import { useState } from 'react'
import { motion } from 'framer-motion'
import { LogOut, Film, MessageSquare, User } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import AuthPage from './components/AuthPage'
import ChatInterface from './components/ChatInterface'
import SingleVideoPlayer from './components/SingleVideoPlayer'
import VideoHistory from './components/VideoHistory'

const PAGES = { CREATE: 'create', HISTORY: 'history' }

function AppContent() {
  const { user, isAuthenticated, signout } = useAuth()
  const [currentVideo, setCurrentVideo] = useState(null)
  const [page, setPage] = useState(PAGES.CREATE)
  const [signingOut, setSigningOut] = useState(false)

  const handleVideoGenerated = (videoData) => {
    setCurrentVideo(videoData)
  }

  const handleSignout = async () => {
    setSigningOut(true)
    await signout()
    setSigningOut(false)
  }

  // Show auth page if not logged in
  if (!isAuthenticated) {
    return <AuthPage />
  }

  return (
    <div className="min-h-screen bg-dark-bg text-white flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 py-3 px-6 bg-dark-bg/80 backdrop-blur-md border-b border-gray-800/50 flex items-center gap-3">
        <motion.img 
          src="/logo.svg" 
          alt="MathViz Logo" 
          className="w-10 h-10 cursor-pointer"
          whileHover={{ scale: 1.1, rotate: 5 }}
          transition={{ type: "spring", stiffness: 400, damping: 10 }}
          onClick={() => setPage(PAGES.CREATE)}
        />
        <div className="cursor-pointer" onClick={() => setPage(PAGES.CREATE)}>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent tracking-wide">MathViz</h1>
          <p className="text-gray-500 text-xs">Math Visualization Tool</p>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 ml-8">
          <button
            onClick={() => setPage(PAGES.CREATE)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              page === PAGES.CREATE
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            Create
          </button>
          <button
            onClick={() => setPage(PAGES.HISTORY)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              page === PAGES.HISTORY
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <Film className="w-4 h-4" />
            My Videos
          </button>
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User Menu */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-xl border border-gray-800/50">
            <User className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-300 max-w-[150px] truncate">
              {user?.display_name || user?.email || 'User'}
            </span>
          </div>
          <button
            onClick={handleSignout}
            disabled={signingOut}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-gray-600/50 to-transparent" />
      </header>

      {/* Main Content — both views stay mounted to preserve state */}
      <main className="flex-1">
        <div style={{ display: page === PAGES.CREATE ? 'block' : 'none' }}>
          <ChatInterface onVideoGenerated={handleVideoGenerated} />
          {currentVideo && <SingleVideoPlayer video={currentVideo} />}
        </div>
        <div style={{ display: page === PAGES.HISTORY ? 'block' : 'none' }}>
          <VideoHistory />
        </div>
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

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
