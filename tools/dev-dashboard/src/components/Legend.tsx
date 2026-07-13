import React from 'react'
import { useDashboardStore } from '../store'
import { Database, Network, Zap, Globe, Sparkles, X, Filter, SlidersHorizontal, LayoutDashboard, BarChart2, Folder, FileCode, FileText, Terminal, Image, BookOpen, ChevronDown, ChevronUp, Globe as GlobeIcon } from 'lucide-react'
import { cn } from '../utils/cn'

export function LoadingGraph() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-dark-950">
      <div className="relative w-48 h-48">
        {[1, 2, 3].map(i => (
          <div key={i} className="absolute inset-0 rounded-full border border-primary-500/20 animate-spin-slow"
            style={{ width: `${120 + i * 30}px`, height: `${120 + i * 30}px`, margin: `-${60 + i * 15}px`, animationDuration: `${15 + i * 5}s` }} />
        ))}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 animate-pulse-slow glow-primary" />
        </div>
      </div>
      <div className="mt-8 text-center">
        <h2 className="text-2xl font-bold gradient-text mb-2">ARGUS Dev Dashboard</h2>
        <p className="text-dark-400 mb-8">Initializing codebase intelligence...</p>
        <div className="w-80 mx-auto space-y-3">
          {steps.map((step, index) => (
            <div key={step.label} className="flex items-center gap-3 p-3 bg-dark-800/50 rounded-lg border border-dark-700/50 animate-in fade-in slide-in-from-left-4 duration-300" style={{ animationDelay: `${index * 100}ms` }}>
              <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center">
                <step.icon className="w-5 h-5 text-primary-400" />
              </div>
              <span className="text-dark-300 text-sm">{step.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const steps = [
  { label: 'Connecting to Codebase Memory...', icon: Database },
  { label: 'Fetching repository graph...', icon: Network },
  { label: 'Indexing nodes and edges...', icon: Zap },
  { label: 'Building 3D visualization...', icon: Globe },
  { label: 'Applying layout algorithms...', icon: Sparkles },
]

export function EmptyState({ message = 'No graph data available', actionLabel = 'Refresh', onAction }: { message?: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8 bg-dark-950/50 rounded-xl border border-dark-700/50">
      <div className="relative w-32 h-32 mb-6">
        <div className="absolute inset-0 rounded-full border-2 border-primary-500/20 animate-spin-slow" />
        <div className="relative w-full h-full flex items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <Globe className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>
      <h3 className="text-xl font-semibold text-dark-100 mb-2">No Graph Data</h3>
      <p className="text-dark-400 text-center max-w-xs mb-6">{message}</p>
      {onAction && (
        <button onClick={onAction} className="px-6 py-3 bg-gradient-to-r from-primary-500 to-primary-700 text-white rounded-lg font-medium hover:from-primary-600 hover:to-primary-800 transition-all glow-primary">
          {actionLabel}
        </button>
      )}
    </div>
  )
}

export function GraphLegend({ colorScheme = 'type' }: { colorScheme?: string }) {
  const schemes: Record<string, { label: string; color: string }[]> = {
    type: [
      { label: 'Class', color: '#f59e0b' }, { label: 'Protocol', color: '#f97316' },
      { label: 'Function', color: '#84cc16' }, { label: 'Method', color: '#a3e635' },
      { label: 'Enum', color: '#ec4899' }, { label: 'File', color: '#22d3ee' },
    ],
    module: [
      { label: 'argus', color: '#0ea5e9' }, { label: 'vision', color: '#f59e0b' },
      { label: 'graph', color: '#06b6d4' }, { label: 'analytics', color: '#8b5cf6' },
      { label: 'simulation', color: '#f97316' }, { label: 'routing', color: '#22c55e' },
      { label: 'dashboard', color: '#ec4899' }, { label: 'cli', color: '#a3e635' },
    ],
    layer: [
      { label: 'Core', color: '#ef4444' }, { label: 'API', color: '#f59e0b' },
      { label: 'Data', color: '#22c55e' }, { label: 'Dashboard', color: '#8b5cf6' },
      { label: 'Infra', color: '#06b6d4' },
    ],
  }

  const items = schemes[colorScheme] || schemes.type

  return (
    <div className="glass-strong rounded-xl p-4 w-64">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-dark-300">Legend</h4>
        <span className="text-xs text-dark-500 capitalize">{colorScheme}</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map((item, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
            <span className="text-xs text-dark-300 truncate">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Legend() {
  return <GraphLegend colorScheme={useDashboardStore.getState().colorScheme} />
}
