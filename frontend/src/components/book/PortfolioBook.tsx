import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useLocation, useOutlet } from 'react-router-dom'
import { getPortfolioRouteIndex } from '../../routes/portfolioRoutes'

type BookPageLayerProps = {
  pathname: string
  pageIndex: number
  nextPageIndex: number
  children: ReactNode
}

const pageVariants = {
  initial: {
    opacity: 1,
    rotateY: 0,
    zIndex: 1,
  },

  animate: {
    opacity: 1,
    rotateY: 0,
    zIndex: 1,
  },

  exit: ({
    pageIndex,
    nextPageIndex,
  }: {
    pageIndex: number
    nextPageIndex: number
  }) => {
    const isForward = nextPageIndex > pageIndex
    const isBackward = nextPageIndex < pageIndex

    if (!isForward && !isBackward) {
      return {
        opacity: 0,
        transition: {
          duration: 0.2,
        },
      }
    }

    return {
      rotateY: isForward ? -180 : 180,
      zIndex: 20,
      transformOrigin: isForward
        ? 'left center'
        : 'right center',

      transition: {
        duration: 0.9,
        ease: [0.65, 0, 0.2, 1] as const,
      },
    }
  },
}

function BookPageLayer({
  pathname,
  pageIndex,
  nextPageIndex,
  children,
}: BookPageLayerProps) {
  return (
    <motion.div
      key={pathname}
      className="book-motion-page"
      custom={{
        pageIndex,
        nextPageIndex,
      }}
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <div className="book-face book-face-front">
        <div className="book-page">
          {children}
        </div>

        <div className="page-turn-shadow" />
      </div>

      <div className="book-face book-face-back">
        <div className="book-page book-page-back-surface">
          <div className="page-back-texture" />
        </div>

        <div className="page-turn-back-shadow" />
      </div>
    </motion.div>
  )
}

export function PortfolioBook() {
  const location = useLocation()
  const outlet = useOutlet()

  const currentPageIndex = getPortfolioRouteIndex(location.pathname)

  return (
    <main className="portfolio-book">
      <div className="book-spine" aria-hidden="true" />

      <div className="book-stage">
        <AnimatePresence
          initial={false}
          mode="sync"
          custom={{
            pageIndex: currentPageIndex,
            nextPageIndex: currentPageIndex,
          }}
        >
          <BookPageLayer
            key={location.pathname}
            pathname={location.pathname}
            pageIndex={currentPageIndex}
            nextPageIndex={currentPageIndex}
          >
            {outlet}
          </BookPageLayer>
        </AnimatePresence>
      </div>
    </main>
  )
}
