import React from 'react'
import { useDashboardStore } from '../store'
import { Zap, ChevronLeft, Globe, GitBranch, Layers, Package, BarChart3, Network, FolderTree, Sun, Moon, Monitor, LayoutDashboard, Zap as ZapIcon, RotateCcw, Download, Settings, ExternalLink } from 'lucide-react'
import { cn } from '../utils/cn'

export function Toolbar() {
  const {
    viewMode,
    setViewMode,
    colorScheme,
    setColorScheme,
    codebaseMemoryAvailable,
    loading,
    toggleSidebar,
    sidebarOpen,
    theme,
    setTheme,
    refetchGraph,
  } = useDashboardStore()

  return (
    <header className="h-14 border-b border-dark-700/50 bg-dark-950/80 backdrop-blur-xl sticky top-0 z-40 flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <button onClick={toggleSidebar} className="p-2 rounded-lg hover:bg-dark-700/50 transition-colors" aria-label="Toggle sidebar">
          <ChevronLeft className="w-5 h-5 text-dark-300" />
        </button>

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center shadow-[0_0_12px_rgba(14,165,233,0.4)]">
            <ZapIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-semibold text-dark-100 text-sm">ARGUS Dev Dashboard</h1>
            <div className="flex items-center gap-1.5 text-xs">
              <span className={cn(
                'px-1.5 py-0.5 rounded text-[10px] font-medium',
                codebaseMemoryAvailable ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
              )}>
                {codebaseMemoryAvailable ? 'Connected' : 'Offline'}
              </span>
              {loading && (
                <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary-500/20 text-primary-400 animate-pulse">
                  Loading...
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Color Scheme Selector */}
        <div className="hidden sm:flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-dark-800/50 border border-dark-600/50">
          <span className="text-xs text-dark-400">Color</span>
          <select
            value={colorScheme}
            onChange={(e) => setColorScheme(e.target.value as any)}
            className="bg-dark-900 border border-dark-600 rounded-lg px-2 py-1 text-sm text-dark-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent cursor-pointer"
          >
            <option value="type">By Type</option>
            <option value="module">By Module</option>
            <option value="layer">By Layer</option>
            <option value="directory">By Directory</option>
            <option value="architecture">Architecture</option>
          </select>
        </div>

        {/* View Mode Selector */}
        <div className="flex items-center gap-1 px-1.5 py-1.5 rounded-lg bg-dark-800/50 border border-dark-600/50">
          {(['galaxy', 'force', 'hierarchy', 'layers'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={cn(
                'p-2 rounded-lg text-dark-400 hover:text-dark-100 hover:bg-dark-700/50 transition-all',
                viewMode === mode && 'text-primary-400 bg-primary-500/20 shadow-[0_0_8px_rgba(14,165,233,0.2)]'
              )}
              title={mode.charAt(0).toUpperCase() + mode.slice(1)}
            >
              {mode === 'galaxy' && <Globe className="w-5 h-5" />}
              {mode === 'force' && <ZapIcon className="w-5 h-5" />}
              {mode === 'hierarchy' && <GitBranch className="w-5 h-5" />}
              {mode === 'layers' && <Layers className="w-5 h-5" />}
            </button>
          ))}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          className="p-2 rounded-lg hover:bg-dark-700/50 transition-colors"
          aria-label="Toggle theme"
          title="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5 text-dark-300" /> : <Moon className="w-5 h-5 text-dark-300" />}
        </button>

        {/* Refresh Button */}
        <button
          onClick={refetchGraph}
          disabled={loading}
          className={cn(
            'p-2 rounded-lg hover:bg-dark-700/50 transition-colors flex items-center gap-1.5',
            loading && 'opacity-50 cursor-not-allowed'
          )}
          aria-label="Refresh graph"
          title="Refresh"
        >
          <RotateCcw className={cn('w-5 h-5 text-dark-300', loading && 'animate-spin')} />
        </button>

        {/* Export Button */}
        <button
          className="p-2 rounded-lg hover:bg-dark-700/50 transition-colors"
          aria-label="Export"
          title="Export"
        >
          <Download className="w-5 h-5 text-dark-300" />
        </button>

        {/* Settings Button */}
        <button
          className="p-2 rounded-lg hover:bg-dark-700/50 transition-colors"
          aria-label="Settings"
          title="Settings"
        >
          <Settings className="w-5 h-5 text-dark-300" />
        </button>
      </div>
    </header>
  )
}

export default Toolbar
