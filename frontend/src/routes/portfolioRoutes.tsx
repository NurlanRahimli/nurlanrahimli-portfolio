import type { ComponentType } from 'react'
import { AboutPage } from '../pages/about/AboutPage'
import { ContactPage } from '../pages/contact/ContactPage'
import { ProjectDetailsPage } from '../pages/projects/ProjectDetailsPage'
import { ProjectsPage } from '../pages/projects/ProjectsPage'
import { ResumePage } from '../pages/resume/ResumePage'

export type PortfolioRoute = {
  path: string
  label: string
  index: number
  component: ComponentType
}

export const portfolioRoutes: PortfolioRoute[] = [
  {
    path: '/about',
    label: 'About',
    index: 0,
    component: AboutPage,
  },
  {
    path: '/resume',
    label: 'Resume',
    index: 1,
    component: ResumePage,
  },
  {
    path: '/projects',
    label: 'Projects',
    index: 2,
    component: ProjectsPage,
  },
  {
    path: '/projects/:slug',
    label: 'Project Details',
    index: 2,
    component: ProjectDetailsPage,
  },
  {
    path: '/contact',
    label: 'Contact',
    index: 3,
    component: ContactPage,
  },
]

export function getPortfolioRouteIndex(pathname: string) {
  if (pathname.startsWith('/projects/')) {
    return 2
  }

  return portfolioRoutes.findIndex((route) => route.path === pathname)
}
