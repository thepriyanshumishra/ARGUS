import React, { useMemo, useState } from 'react'
import {
  FileCode, Layers, Zap, GitBranch, Package, Search, Filter, Settings, ExternalLink,
  ChevronDown, ChevronUp, BarChart3, PieChart, TrendingUp, Target, X,
  Zap as ZapIcon, RotateCcw, Download, Settings as SettingsIcon,
  Sun, Moon, Monitor, SlidersHorizontal, Network, Folder, FileText, Terminal, Image, BookOpen, Globe
} from 'lucide-react'
import { cn } from '../utils/cn'
import { useDashboardStore } from '../store'

export interface AnalyticsPanelProps {
  open?: boolean
  onClose?: () => void
}

export function AnalyticsPanel({ open = true, onClose }: AnalyticsPanelProps) {
  const { graphData, filteredNodes, filteredEdges } = useDashboardStore()
  const [activeTab, setActiveTab] = useState<'overview' | 'nodes' | 'edges'>('overview')

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'nodes', label: 'Nodes', icon: Zap },
    { id: 'edges', label: 'Edges', icon: GitBranch },
  ]

  const stats = useMemo(() => {
    if (!graphData) return null
    const nodes = filteredNodes || graphData.nodes || []
    const edges = filteredEdges || graphData.edges || []

    const nodeTypes: Record<string, number> = {}
    nodes.forEach((n: any) => { nodeTypes[n.type] = (nodeTypes[n.type] || 0) + 1 })

    const edgeTypes: Record<string, number> = {}
    edges.forEach((e: any) => { edgeTypes[e.type] = (edgeTypes[e.type] || 0) + 1 })

    const connections = new Map<string, number>()
    edges.forEach((e: any) => {
      connections.set(e.source, (connections.get(e.source) || 0) + 1)
      connections.set(e.target, (connections.get(e.target) || 0) + 1)
    })

    const topConnected = Array.from(connections.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([id, count]) => {
        const node = graphData.nodes?.find((n: any) => n.id === id)
        return { id, label: node?.label || id, count, type: node?.type }
      })

    return {
      totalNodes: nodes.length,
      totalEdges: edges.length,
      nodeTypes,
      edgeTypes,
      topConnected,
      density: nodes.length > 1 ? (2 * edges.length) / (nodes.length * (nodes.length - 1)) : 0,
      avgDegree: nodes.length > 0 ? (2 * edges.length) / nodes.length : 0,
    }
  }, [graphData, filteredNodes, filteredEdges])

  return (
    <aside
      className={cn(
        'flex flex-col bg-dark-950/95 backdrop-blur-xl border-l border-dark-700/50 transition-all duration-300',
        open ? 'w-96 min-w-[384px]' : 'w-0 min-w-0 overflow-hidden'
      )}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-4 border-b border-dark-700/50 bg-dark-950/80 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary-400" />
            <span className="font-semibold text-dark-100">Analytics</span>
            <span className="px-2 py-0.5 text-xs bg-primary-500/20 text-primary-400 rounded">
              {filteredNodes.length} nodes
            </span>
          </div>
          <button onClick={() => { useDashboardStore.getState().setAnalyticsOpen?.(false); onClose?.() }} className="p-1.5 rounded-lg hover:bg-dark-700/50 transition-colors">
            <X className="w-4 h-4 text-dark-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-3 py-2 border-b border-dark-700/50 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-all whitespace-nowrap',
                activeTab === tab.id ? 'bg-primary-500/15 text-primary-400 border border-primary-500/30' : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700/50'
              )}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {activeTab === 'overview' && stats && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <MetricCard label="Total Nodes" value={stats.totalNodes} icon={Zap} />
                <MetricCard label="Total Edges" value={stats.totalEdges} icon={GitBranch} />
                <MetricCard label="Avg Degree" value={stats.avgDegree?.toFixed(1) || '0'} icon={Target} />
                <MetricCard label="Density" value={(stats.density * 100).toFixed(2) + '%'} icon={TrendingUp} />
              </div>

              <div className="glass-strong rounded-xl p-4">
                <h4 className="font-semibold text-dark-100 mb-3">Node Types</h4>
                <div className="space-y-2">
                  {Object.entries(stats.nodeTypes).map(([type, count]) => (
                    <div key={type} className="flex items-center gap-3">
                      <span className="text-sm text-dark-300 capitalize flex-1">{type}</span>
                      <span className="text-sm font-mono text-dark-100">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-strong rounded-xl p-4">
                <h4 className="font-semibold text-dark-100 mb-3">Edge Types</h4>
                <div className="space-y-2">
                  {Object.entries(stats.edgeTypes).map(([type, count]) => (
                    <div key={type} className="flex items-center gap-3">
                      <span className="text-sm text-dark-300 capitalize flex-1">{type.replace(/_/g, ' ')}</span>
                      <span className="text-sm font-mono text-dark-100">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-strong rounded-xl p-4">
                <h4 className="font-semibold text-dark-100 mb-3 flex items-center gap-2">
                  <Target className="w-5 h-5 text-amber-400" />
                  Most Connected
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {stats.topConnected.map((item, i) => (
                    <div key={item.id} className="flex items-center gap-3 p-2 rounded-lg bg-dark-800/50 hover:bg-dark-700/50 transition-colors">
                      <span className="w-6 text-center font-mono text-amber-400 font-bold">{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="font-medium text-dark-100 truncate">{item.label}</span>
                          <span className="px-1.5 py-0.5 text-xs rounded bg-dark-700 text-dark-400">{item.type}</span>
                        </div>
                      </div>
                      <span className="px-2 py-0.5 text-xs font-bold bg-primary-500/20 text-primary-400 rounded">{item.count} conn</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {activeTab === 'nodes' && (
            <div className="glass-strong rounded-xl overflow-hidden">
              <div className="p-4 border-b border-dark-700/50"><h4 className="font-semibold text-dark-100">Nodes ({filteredNodes.length})</h4></div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700/50 text-left text-xs text-dark-400 uppercase tracking-wider">
                      <th className="p-3 font-semibold">Name</th>
                      <th className="p-3 font-semibold">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredNodes.slice(0, 100).map((node: any) => (
                      <tr key={node.id} className="border-b border-dark-700/30 hover:bg-dark-700/50">
                        <td className="p-3 font-medium text-dark-100 truncate max-w-[200px]">{node.label}</td>
                        <td className="p-3"><span className="px-2 py-0.5 text-xs rounded bg-dark-700 text-dark-300 capitalize">{node.type}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'edges' && (
            <div className="glass-strong rounded-xl overflow-hidden">
              <div className="p-4 border-b border-dark-700/50"><h4 className="font-semibold text-dark-100">Edges ({filteredEdges.length})</h4></div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-dark-700/50 text-left text-xs text-dark-400 uppercase tracking-wider">
                      <th className="p-3 font-semibold">Source</th>
                      <th className="p-3 font-semibold">Target</th>
                      <th className="p-3 font-semibold">Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEdges.slice(0, 100).map((edge: any) => (
                      <tr key={edge.id} className="border-b border-dark-700/30 hover:bg-dark-700/50">
                        <td className="p-3 text-dark-300 truncate max-w-[150px]">{edge.source}</td>
                        <td className="p-3 text-dark-300 truncate max-w-[150px]">{edge.target}</td>
                        <td className="p-3"><span className="px-2 py-0.5 text-xs rounded bg-dark-700 text-dark-300 capitalize">{edge.type.replace(/_/g, ' ')}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}

function MetricCard({ label, value, icon: Icon }: { label: string; value: string | number; icon: any }) {
  return (
    <div className="glass-strong rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-dark-400 uppercase tracking-wider">{label}</span>
        <div className="w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-primary-400" />
        </div>
      </div>
      <div className="text-2xl font-bold font-mono text-dark-100">{value}</div>
    </div>
  )
}

export default AnalyticsPanel
