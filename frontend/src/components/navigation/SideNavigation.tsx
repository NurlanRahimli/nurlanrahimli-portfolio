import {
  BriefcaseBusiness,
  FileText,
  Menu,
  Moon,
  Sun,
  UserRound,
  Mail,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

const navigationItems = [
  {
    to: '/about',
    label: 'About',
    icon: UserRound,
  },
  {
    to: '/resume',
    label: 'Resume',
    icon: FileText,
  },
  {
    to: '/projects',
    label: 'Projects',
    icon: BriefcaseBusiness,
  },
  {
    to: '/contact',
    label: 'Contact',
    icon: Mail,
  },
]

export function SideNavigation() {
  const [darkMode, setDarkMode] = useState(true)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40)
    }

    handleScroll()
    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  useEffect(() => {
    document.documentElement.dataset.portfolioTheme =
      darkMode ? 'dark' : 'light'
  }, [darkMode])

  return (
    <header className={`futurism-header${isScrolled ? " is-scrolled" : ""}`}>
      <div className="futurism-header-outline" />

      <div className="futurism-utility">
        <button
          className="futurism-utility-button futurism-menu-button"
          type="button"
          aria-label="Menu"
        >
          <Menu size={30} strokeWidth={1.5} />
        </button>

        <button
          className="futurism-utility-button"
          type="button"
          aria-label="Toggle theme"
          onClick={() => setDarkMode((current) => !current)}
        >
          {darkMode ? (
            <Sun size={28} strokeWidth={1.45} />
          ) : (
            <Moon size={28} strokeWidth={1.45} />
          )}
        </button>

        <button
          className="futurism-utility-button futurism-status-button"
          type="button"
          aria-label="Projects"
        >
          <BriefcaseBusiness size={27} strokeWidth={1.45} />
          <span className="futurism-status-badge">4</span>
        </button>
      </div>

      <nav className="futurism-menu" aria-label="Portfolio navigation">
        {navigationItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `futurism-menu-item${isActive ? ' is-active' : ''}`
            }
          >
            <Icon size={27} strokeWidth={1.45} />

            <span className="futurism-menu-label">
              {label}
            </span>
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
