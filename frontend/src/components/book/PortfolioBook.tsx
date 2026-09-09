import { Outlet } from 'react-router-dom'

export function PortfolioBook() {
  return (
    <main className="portfolio-book">
      <div className="book-page">
        <Outlet />
      </div>
    </main>
  )
}
