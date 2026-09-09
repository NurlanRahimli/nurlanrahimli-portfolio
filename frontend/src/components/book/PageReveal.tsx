import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

type PageRevealProps = {
  number: string
  title: string
  children: ReactNode
}

export function PageReveal({
  number,
  title,
  children,
}: PageRevealProps) {
  const reduceMotion = useReducedMotion()

  return (
    <motion.section
      className="portfolio-page"
      initial={reduceMotion ? false : 'hidden'}
      animate="visible"
      variants={{
        hidden: {},
        visible: {
          transition: {
            delayChildren: 0.12,
            staggerChildren: 0.1,
          },
        },
      }}
    >
      <motion.div
        className="page-kicker-wrap"
        variants={{
          hidden: {
            opacity: 0,
            y: 10,
          },
          visible: {
            opacity: 1,
            y: 0,
            transition: {
              duration: 0.4,
            },
          },
        }}
      >
        <span className="page-kicker">{number}</span>
      </motion.div>

      <div className="page-title-mask">
        <motion.h1
          initial={
            reduceMotion
              ? false
              : {
                  y: '115%',
                }
          }
          animate={{
            y: '0%',
          }}
          transition={{
            duration: reduceMotion ? 0 : 0.68,
            delay: reduceMotion ? 0 : 0.08,
            ease: [0.16, 1, 0.3, 1],
          }}
        >
          {title}
        </motion.h1>
      </div>

      <motion.div
        className="page-reveal-content"
        variants={{
          hidden: {
            opacity: 0,
            y: 18,
          },
          visible: {
            opacity: 1,
            y: 0,
            transition: {
              duration: 0.55,
              ease: [0.22, 1, 0.36, 1],
            },
          },
        }}
      >
        {children}
      </motion.div>
    </motion.section>
  )
}
