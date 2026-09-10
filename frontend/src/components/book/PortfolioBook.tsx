import { AnimatePresence, motion } from 'framer-motion'
import { useLocation, useOutlet } from 'react-router-dom'

const pageVariants = {
  initial: {
    opacity: 0,
    x: '-70%',
  },

  animate: {
    opacity: 1,
    x: 0,
  },

  exit: {
    opacity: 0,
    x: '-70%',
  },
}

export function PortfolioBook() {
  const location = useLocation()
  const outlet = useOutlet()

  return (
    <div className="ryan-card-stage">
      <AnimatePresence mode="sync" initial={false}>
        <motion.div
          key={location.pathname}
          className="ryan-card-inner"
          variants={pageVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{
            duration: 0.6,
            ease: 'easeInOut',
          }}
        >
          <div className="ryan-card-wrap">
            {outlet}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
