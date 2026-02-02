import { motion } from 'framer-motion'

const Tooltip = ({ text }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 5 }}
      className="
        absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2
        bg-gray-200 text-black text-xs font-medium
        px-3 py-1.5 rounded-lg whitespace-nowrap
        pointer-events-none z-50
        drop-shadow-lg
      "
    >
      {text}
      <div className="
        absolute top-full left-1/2 transform -translate-x-1/2
        w-0 h-0 border-l-4 border-r-4 border-t-4
        border-transparent border-t-gray-200
      " />
    </motion.div>
  )
}

export default Tooltip
