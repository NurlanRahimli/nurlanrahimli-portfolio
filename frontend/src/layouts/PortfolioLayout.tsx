import { AnimatedBackground } from '../components/background/AnimatedBackground'
import { PortfolioBook } from '../components/book/PortfolioBook'
import { SideNavigation } from '../components/navigation/SideNavigation'
import { ProfileCard } from '../components/profile/ProfileCard'

export function PortfolioLayout() {
  return (
    <div className="portfolio-shell">
      <AnimatedBackground />

      <div className="portfolio-interface">
        <SideNavigation />
        <ProfileCard />
        <PortfolioBook />
      </div>
    </div>
  )
}
