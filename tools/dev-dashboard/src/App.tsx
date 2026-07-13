import { useEffect } from 'react'
import { Sidebar, MainPanel, AnalyticsPanel, Toolbar } from './components'
import { useDashboardStore } from './store'
import './App.css'

function App() {
  const initialize = useDashboardStore(state => state.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <div className="min-h-screen bg-dark-950 flex flex-col">
      <Toolbar />
      <div className="flex-1 flex">
        <Sidebar />
        <MainPanel />
        <AnalyticsPanel />
      </div>
    </div>
  )
}

export default App