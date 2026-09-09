import { Navigate, Route, Routes } from 'react-router-dom'
import { PortfolioLayout } from './layouts/PortfolioLayout'
import { portfolioRoutes } from './routes/portfolioRoutes'

function App() {
  return (
    <Routes>
      <Route element={<PortfolioLayout />}>
        <Route index element={<Navigate to="/about" replace />} />

        {portfolioRoutes.map((route) => {
          const Page = route.component

          return (
            <Route
              key={route.path}
              path={route.path}
              element={<Page />}
            />
          )
        })}

        <Route path="*" element={<Navigate to="/about" replace />} />
      </Route>
    </Routes>
  )
}

export default App
