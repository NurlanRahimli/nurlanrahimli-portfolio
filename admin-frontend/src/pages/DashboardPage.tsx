import { motion } from 'framer-motion'
import {
  ArrowUpRight,
  FolderKanban,
  LogOut,
  ShieldCheck,
} from 'lucide-react'

import { useAuth } from '../context/authContext'

export function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <main className="dashboard-page">
      <motion.div
        className="dashboard-shell"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <header className="dashboard-header">
          <div className="dashboard-brand">
            <div className="brand-mark brand-mark--small">
              NR
            </div>

            <div>
              <span>Portfolio administration</span>
              <strong>Nurlan Rahimli</strong>
            </div>
          </div>

          <button
            className="logout-button"
            type="button"
            onClick={logout}
          >
            <LogOut size={18} />
            Log out
          </button>
        </header>

        <section className="dashboard-welcome">
          <span className="login-eyebrow">
            <ShieldCheck size={17} />
            Authenticated
          </span>

          <h1>Welcome to your dashboard.</h1>

          <p>
            Authentication is connected successfully. The full
            portfolio management dashboard will be built next.
          </p>

          <div className="dashboard-user">
            <div>
              <span>Signed in as</span>
              <strong>{user?.email}</strong>
            </div>

            <div>
              <span>Account</span>
              <strong>Super admin</strong>
            </div>
          </div>

          <div className="dashboard-placeholder">
            <FolderKanban size={26} />

            <div>
              <strong>Management modules coming next</strong>
              <span>
                Projects, media, resume, profile and contact.
              </span>
            </div>

            <ArrowUpRight size={22} />
          </div>
        </section>
      </motion.div>
    </main>
  )
}
