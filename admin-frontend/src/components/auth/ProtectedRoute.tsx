import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../../context/authContext'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <main className="auth-loading" aria-live="polite">
        <div className="auth-loading__mark">NR</div>
        <div className="auth-loading__spinner" />
        <p>Restoring your session...</p>
      </main>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
