import {
  BriefcaseBusiness,
  FolderKanban,
  Mail,
  UserRound,
} from 'lucide-react'
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
    icon: BriefcaseBusiness,
  },
  {
    to: '/projects',
    label: 'Projects',
    icon: FolderKanban,
  },
  {
    to: '/contact',
    label: 'Contact',
    icon: Mail,
  },
]

export function SideNavigation() {
  return (
    <nav className="side-navigation" aria-label="Portfolio navigation">
      {navigationItems.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `navigation-item${isActive ? ' navigation-item-active' : ''}`
          }
        >
          <Icon size={20} strokeWidth={1.8} />

          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
