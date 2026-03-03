import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Clock, Play, Download, ExternalLink, Film, 
  AlertCircle, Loader2, ChevronDown, Search
} from 'lucide-react'
import axios from 'axios'

const VideoHistory = () => {
  const [videos, setVideos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get('/api/user/history')
      setVideos(res.data.videos || [])
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to load history'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const filteredVideos = videos.filter(v =>
    v.prompt.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatDate = (dateStr) => {
    const d = new Date(dateStr)
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  }

  const qualityBadge = (q) => {
    const map = { l: '480p', m: '720p', h: '1080p', k: '4K' }
    const colorMap = { l: 'bg-gray-700', m: 'bg-blue-900', h: 'bg-purple-900', k: 'bg-amber-900' }
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full ${colorMap[q] || 'bg-gray-700'} text-white`}>
        {map[q] || q}
      </span>
    )
  }

  const statusBadge = (status) => {
    const config = {
      completed: { color: 'bg-green-500/20 text-green-400', label: 'Completed' },
      processing: { color: 'bg-yellow-500/20 text-yellow-400', label: 'Processing' },
      failed: { color: 'bg-red-500/20 text-red-400', label: 'Failed' },
      pending: { color: 'bg-gray-500/20 text-gray-400', label: 'Pending' }
    }
    const s = config[status] || config.pending
    return <span className={`text-xs px-2 py-0.5 rounded-full ${s.color}`}>{s.label}</span>
  }

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
        >
          <Loader2 className="w-8 h-8 text-text-secondary" />
        </motion.div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Film className="w-6 h-6" />
            My Videos
          </h2>
          <p className="text-text-secondary text-sm mt-1">
            {videos.length} video{videos.length !== 1 ? 's' : ''} generated
          </p>
        </div>
        <button
          onClick={fetchHistory}
          className="px-4 py-2 bg-input-surface border border-gray-800 rounded-xl text-sm text-text-secondary hover:text-white hover:border-gray-600 transition-all"
        >
          Refresh
        </button>
      </div>

      {/* Search */}
      {videos.length > 0 && (
        <div className="relative mb-6">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your videos..."
            className="w-full bg-input-surface border border-gray-800 rounded-xl py-3 pl-11 pr-4 
              text-text-primary placeholder-text-secondary text-sm
              focus:outline-none focus:border-gray-600 focus:ring-1 focus:ring-gray-700 transition-all"
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm mb-6 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Empty State */}
      {videos.length === 0 && !error && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-20"
        >
          <Film className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-text-primary mb-2">No videos yet</h3>
          <p className="text-text-secondary text-sm">
            Start creating animations and they'll appear here.
          </p>
        </motion.div>
      )}

      {/* Video Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnimatePresence>
          {filteredVideos.map((video, index) => (
            <motion.div
              key={video.job_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ delay: index * 0.05 }}
              className="bg-input-surface border border-gray-800/50 rounded-2xl overflow-hidden hover:border-gray-700 transition-all group"
            >
              {/* Video Preview / Player */}
              {video.video_url && video.status === 'completed' ? (
                <div 
                  className="relative aspect-video bg-black cursor-pointer"
                  onClick={() => setSelectedVideo(selectedVideo === video.job_id ? null : video.job_id)}
                >
                  {selectedVideo === video.job_id ? (
                    <video
                      src={video.video_url}
                      controls
                      autoPlay
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-900 to-black">
                      <motion.div
                        whileHover={{ scale: 1.1 }}
                        className="w-14 h-14 bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/20"
                      >
                        <Play className="w-6 h-6 text-white ml-1" />
                      </motion.div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="aspect-video bg-gradient-to-br from-gray-900 to-black flex items-center justify-center">
                  {video.status === 'processing' ? (
                    <Loader2 className="w-8 h-8 text-yellow-400 animate-spin" />
                  ) : video.status === 'failed' ? (
                    <AlertCircle className="w-8 h-8 text-red-400" />
                  ) : (
                    <Film className="w-8 h-8 text-gray-600" />
                  )}
                </div>
              )}

              {/* Info */}
              <div className="p-4">
                <p className="text-text-primary text-sm font-medium line-clamp-2 mb-3">
                  {video.prompt}
                </p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {statusBadge(video.status)}
                    {video.quality && qualityBadge(video.quality)}
                  </div>
                  <div className="flex items-center gap-2">
                    {video.video_url && (
                      <a
                        href={video.video_url}
                        download
                        onClick={(e) => e.stopPropagation()}
                        className="p-1.5 text-text-secondary hover:text-white transition-colors"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 mt-2 text-xs text-text-secondary">
                  <Clock className="w-3 h-3" />
                  {formatDate(video.created_at)}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* No search results */}
      {searchQuery && filteredVideos.length === 0 && videos.length > 0 && (
        <p className="text-center text-text-secondary text-sm mt-8">
          No videos matching "{searchQuery}"
        </p>
      )}
    </div>
  )
}

export default VideoHistory
