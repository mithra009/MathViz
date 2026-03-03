import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Sparkles,
  Send,
  Square
} from 'lucide-react'
import axios from 'axios'

const ChatInterface = ({ onVideoGenerated }) => {
  const [prompt, setPrompt] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentJobId, setCurrentJobId] = useState(null)
  const textareaRef = useRef(null)
  const pollIntervalRef = useRef(null)
  const progressIntervalRef = useRef(null)
  const timeoutRef = useRef(null)
  const isCancelledRef = useRef(false)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [prompt])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearInterval(pollIntervalRef.current)
      clearInterval(progressIntervalRef.current)
      clearTimeout(timeoutRef.current)
    }
  }, [])

  const cleanupTimers = useCallback(() => {
    clearInterval(pollIntervalRef.current)
    clearInterval(progressIntervalRef.current)
    clearTimeout(timeoutRef.current)
    pollIntervalRef.current = null
    progressIntervalRef.current = null
    timeoutRef.current = null
  }, [])

  const handleStop = useCallback(async () => {
    isCancelledRef.current = true
    cleanupTimers()
    
    // Tell the backend to cancel the job
    if (currentJobId) {
      try {
        await axios.post(`/api/cancel/${currentJobId}`)
      } catch (err) {
        console.error('Cancel request failed:', err)
      }
    }
    
    setIsLoading(false)
    setProgress(0)
    setCurrentJobId(null)
  }, [currentJobId, cleanupTimers])

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!prompt.trim() || isLoading) return

    setIsLoading(true)
    setProgress(0)
    isCancelledRef.current = false
    
    try {
      // Submit render job
      const response = await axios.post('/api/render', {
        prompt: prompt.trim()
      })

      const { job_id } = response.data
      setCurrentJobId(job_id)

      // Simulate progress while polling
      let progressValue = 0
      progressIntervalRef.current = setInterval(() => {
        progressValue += Math.random() * 15
        if (progressValue > 90) progressValue = 90
        setProgress(progressValue)
      }, 500)

      // Poll for completion
      pollIntervalRef.current = setInterval(async () => {
        if (isCancelledRef.current) return
        try {
          const statusResponse = await axios.get(`/api/status/${job_id}`)
          const { status, video_url, error } = statusResponse.data

          if (status === 'completed') {
            cleanupTimers()
            setProgress(100)
            const savedPrompt = prompt.trim()
            setTimeout(() => {
              setIsLoading(false)
              setProgress(0)
              setPrompt('')
              setCurrentJobId(null)
            }, 500)
            
            if (video_url) {
              onVideoGenerated({
                id: job_id,
                prompt: savedPrompt,
                url: video_url,
                timestamp: new Date().toISOString()
              })
            }
          } else if (status === 'failed') {
            cleanupTimers()
            setIsLoading(false)
            setProgress(0)
            setCurrentJobId(null)
            alert(`Video generation failed: ${error || 'Unknown error'}`)
          } else if (status === 'cancelled') {
            cleanupTimers()
            setIsLoading(false)
            setProgress(0)
            setCurrentJobId(null)
          }
        } catch (err) {
          console.error('Polling error:', err)
        }
      }, 2000)

      // Timeout after 5 minutes
      timeoutRef.current = setTimeout(() => {
        if (!isCancelledRef.current) {
          cleanupTimers()
          setIsLoading(false)
          setProgress(0)
          setCurrentJobId(null)
          alert('Video generation timed out. Please try again.')
        }
      }, 300000)

    } catch (error) {
      console.error('Error submitting prompt:', error)
      setIsLoading(false)
      setProgress(0)
      setCurrentJobId(null)
      alert('Failed to submit prompt. Please try again.')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start pt-[15vh] px-4 sm:px-6">
      <div className="w-full max-w-3xl">
        {/* Greeting Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <div className="flex items-center gap-3 mb-4">
            <motion.div
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles className="w-8 h-8" style={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                filter: 'drop-shadow(0 0 8px rgba(102, 126, 234, 0.3))'
              }} />
            </motion.div>
            <span className="text-xl font-medium text-text-primary">
              Hi there
            </span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-semibold tracking-tight text-text-primary">
            What video should we create?
          </h1>
        </motion.div>

        {/* Smart Input Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="relative"
        >
          <div className={`
            w-full bg-input-surface rounded-pill p-2 flex flex-col
            transition-all duration-300 border border-transparent
            ${prompt ? 'focus-within:bg-input-focus focus-within:ring-1 focus-within:ring-gray-700 focus-within:shadow-lg' : ''}
          `}>
            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              placeholder="Describe the math animation you want to create..."
              className="
                w-full bg-transparent border-none focus:ring-0 resize-none 
                px-6 pt-4 pb-2 text-text-primary placeholder-text-secondary
                text-base sm:text-lg outline-none min-h-[60px] max-h-[300px]
                disabled:opacity-50 disabled:cursor-not-allowed
              "
              rows={1}
            />

            {/* Send / Stop Button */}
            <div className="flex justify-end px-4 pb-3">
              {isLoading ? (
                <motion.button
                  onClick={handleStop}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className="p-3 rounded-full transition-all duration-300 bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/20"
                  title="Stop generation"
                >
                  <Square className="w-5 h-5 fill-current" />
                </motion.button>
              ) : (
                <motion.button
                  onClick={handleSubmit}
                  disabled={!prompt.trim()}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className={`
                    p-3 rounded-full transition-all duration-300
                    ${prompt.trim()
                      ? 'bg-white text-black hover:bg-gray-200 shadow-lg shadow-white/20'
                      : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  <Send className="w-5 h-5" />
                </motion.button>
              )}
            </div>
          </div>

          {/* Progress Bar */}
          <AnimatePresence>
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-6"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-text-secondary">Generating your video...</span>
                  <span className="text-sm text-text-secondary font-mono">{Math.round(progress)}%</span>
                </div>
                <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-gray-400 via-gray-300 to-white"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Submit Hint */}
        {prompt && !isLoading && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-4 text-center text-sm text-text-secondary"
          >
            Press <kbd className="px-2 py-1 bg-white/10 rounded font-mono text-xs">Enter</kbd> to generate
          </motion.p>
        )}
      </div>
    </div>
  )
}

export default ChatInterface
