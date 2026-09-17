import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from 'lucide-react'
import {
  type FormEvent,
  useState,
} from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/authContext'

export function LoginPage() {
  const navigate = useNavigate()
  const {
    isAuthenticated,
    isLoading: isSessionLoading,
    login,
  } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isSessionLoading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!email.trim() || !password) {
      setError('Enter your email and password.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await login({
        email: email.trim().toLowerCase(),
        password,
      })

      navigate('/', { replace: true })
    } catch (loginError) {
      setError(
        loginError instanceof Error
          ? loginError.message
          : 'Unable to sign in. Please try again.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-page__glow login-page__glow--one" />
      <div className="login-page__glow login-page__glow--two" />
      <div className="login-page__grid" />

      <motion.section
        className="login-intro"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, ease: 'easeOut' }}
      >
        <div className="brand-mark" aria-label="Nurlan Rahimli">
          NR
        </div>

        <div className="login-intro__content">
          <span className="login-eyebrow">
            <ShieldCheck size={17} />
            Private workspace
          </span>

          <h1>
            Portfolio
            <span>Control Center.</span>
          </h1>

          <p>
            Manage the projects, experience, media, and content
            behind nurlanrahimli.com.
          </p>
        </div>

        <p className="login-intro__footer">
          Nurlan Rahimli · Administration
        </p>
      </motion.section>

      <motion.section
        className="login-panel"
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{
          duration: 0.65,
          delay: 0.08,
          ease: 'easeOut',
        }}
      >
        <div className="login-card">
          <div className="login-card__heading">
            <span>Secure access</span>
            <h2>Welcome back.</h2>
            <p>
              Sign in with your administrator credentials to
              continue.
            </p>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <label className="field">
              <span>Email address</span>

              <div className="field__control">
                <Mail size={20} />

                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value)
                    setError(null)
                  }}
                  placeholder="you@example.com"
                  disabled={isSubmitting}
                />
              </div>
            </label>

            <label className="field">
              <span>Password</span>

              <div className="field__control">
                <LockKeyhole size={20} />

                <input
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value)
                    setError(null)
                  }}
                  placeholder="Enter your password"
                  disabled={isSubmitting}
                />

                <button
                  className="password-toggle"
                  type="button"
                  onClick={() =>
                    setShowPassword((current) => !current)
                  }
                  aria-label={
                    showPassword
                      ? 'Hide password'
                      : 'Show password'
                  }
                >
                  {showPassword ? (
                    <EyeOff size={20} />
                  ) : (
                    <Eye size={20} />
                  )}
                </button>
              </div>
            </label>

            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  className="login-error"
                  role="alert"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -5 }}
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            <button
              className="login-submit"
              type="submit"
              disabled={isSubmitting}
            >
              <span>
                {isSubmitting
                  ? 'Signing in...'
                  : 'Sign in to dashboard'}
              </span>

              {isSubmitting ? (
                <span className="button-spinner" />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>
          </form>

          <div className="login-security">
            <ShieldCheck size={17} />
            Protected administrator access
          </div>
        </div>
      </motion.section>
    </main>
  )
}
