import { AnimatedBackground } from '../components/background/AnimatedBackground'
import { PortfolioBook } from '../components/book/PortfolioBook'
import { SideNavigation } from '../components/navigation/SideNavigation'
import { ProfileCard } from '../components/profile/ProfileCard'

export function PortfolioLayout() {
  return (
    <div className="ryancv-app">
      <AnimatedBackground />

      <div className="ryancv-container">
        <SideNavigation />

        <ProfileCard />

        <section className="ryancv-content-panel">
          <PortfolioBook />
        </section>
      </div>
    </div>
  )
}
