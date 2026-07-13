import React from 'react'
import { Layout } from 'lucide-react'
import { useDashboardStore } from '../store'

export function Header() {
  const { sidebarOpen, setSidebarOpen } = useDashboardStore()
  return (
    <header className="h-14 bg-dark-900/80 backdrop-blur-xl border-b border-dark-700/50 flex items-center justify-between px-4 sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 rounded-lg hover:bg-dark-800 transition-colors text-dark-400 hover:text-dark-100" aria-label="Toggle Sidebar">
          <Layout className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <span className="text-sm font-bold text-white">A</span>
          </div>
          <span className="text-xl font-bold gradient-text">ARGUS Dev Dashboard</span>
        </div>
      </div>
    </header>
  )
}

export default Header
