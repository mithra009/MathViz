import { motion } from 'framer-motion'
import { Play, Download, Share2 } from 'lucide-react'

const VideoGallery = ({ videos }) => {
  if (videos.length === 0) return null

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h2 className="text-3xl font-semibold text-text-primary mb-2">
          Your Videos
        </h2>
        <p className="text-text-secondary">
          Videos you've generated with AI
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {videos.map((video, index) => (
          <motion.div
            key={video.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-input-surface rounded-2xl overflow-hidden hover:ring-1 hover:ring-gray-700 transition-all group"
          >
            {/* Video Player */}
            <div className="relative aspect-video bg-black/50">
              <video
                src={video.url}
                controls
                className="w-full h-full object-contain"
                preload="metadata"
              >
                Your browser does not support the video tag.
              </video>
              
              {/* Overlay Controls */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  className="p-4 bg-white/20 backdrop-blur-sm rounded-full"
                >
                  <Play className="w-8 h-8 text-white" fill="white" />
                </motion.button>
              </div>
            </div>

            {/* Video Info */}
            <div className="p-4">
              <p className="text-text-primary text-sm font-medium line-clamp-2 mb-3">
                {video.prompt}
              </p>
              
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">
                  {new Date(video.timestamp).toLocaleDateString()}
                </span>
                
                <div className="flex gap-2">
                  <motion.a
                    href={video.url}
                    download
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 rounded-full hover:bg-white/10 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                  </motion.a>
                  
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="p-2 rounded-full hover:bg-white/10 transition-colors"
                    onClick={() => {
                      navigator.clipboard.writeText(video.url)
                      alert('Video URL copied to clipboard!')
                    }}
                  >
                    <Share2 className="w-4 h-4" />
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default VideoGallery
