import { motion } from 'framer-motion'
import { Download } from 'lucide-react'

const SingleVideoPlayer = ({ video }) => {
  if (!video) return null

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-input-surface rounded-2xl overflow-hidden shadow-2xl"
      >
        {/* Video Player */}
        <div className="relative aspect-video bg-black">
          <video
            src={video.url}
            controls
            autoPlay
            className="w-full h-full object-contain"
            preload="auto"
          >
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Video Info */}
        <div className="p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-text-primary mb-2">
                Your Video
              </h3>
              <p className="text-text-secondary text-sm mb-3">
                {video.prompt}
              </p>
              <span className="text-xs text-text-secondary">
                Generated on {new Date(video.timestamp).toLocaleString()}
              </span>
            </div>
            
            <motion.a
              href={video.url}
              download={`manim-video-${video.id}.mp4`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full hover:from-blue-700 hover:to-purple-700 transition-all text-white font-medium shadow-lg"
            >
              <Download className="w-4 h-4" />
              <span>Download</span>
            </motion.a>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default SingleVideoPlayer
