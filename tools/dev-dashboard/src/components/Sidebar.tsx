import React, { useState } from 'react'
import { useDashboardStore } from '../store'
import { Search, X, ChevronDown, ChevronUp, Filter, SlidersHorizontal, LayoutDashboard, Network, BarChart2, Folder, FileCode, FileText, Terminal, Image, BookOpen } from 'lucide-react'
import { cn } from '../utils/cn'

const NODE_TYPES = [
  { key: 'directory', label: 'Directories', icon: Folder },
  { key: 'package', label: 'Packages', icon: Folder },
  { key: 'module', label: 'Modules', icon: Network },
  { key: 'file', label: 'Files', icon: FileCode },
  { key: 'class', label: 'Classes', icon: LayoutDashboard },
  { key: 'protocol', label: 'Protocols', icon: SlidersHorizontal },
  { key: 'function', label: 'Functions', icon: BarChart2 },
  { key: 'method', label: 'Methods', icon: BarChart2 },
  { key: 'enum', label: 'Enums', icon: SlidersHorizontal },
  { key: 'dataclass', label: 'Data Classes', icon: LayoutDashboard },
  { key: 'config', label: 'Configs', icon: FileText },
  { key: 'test', label: 'Tests', icon: Terminal },
  { key: 'script', label: 'Scripts', icon: Terminal },
  { key: 'asset', label: 'Assets', icon: Image },
  { key: 'documentation', label: 'Docs', icon: BookOpen },
]

const EDGE_TYPES = [
  { key: 'imports', label: 'Imports' },
  { key: 'contains', label: 'Contains' },
  { key: 'inherits', label: 'Inherits' },
  { key: 'implements', label: 'Implements' },
  { key: 'calls', label: 'Calls' },
  { key: 'references', label: 'References' },
  { key: 'uses', label: 'Uses' },
  { key: 'owns', label: 'Owns' },
  { key: 'depends_on', label: 'Depends On' },
  { key: 'configuration', label: 'Configuration' },
  { key: 'test_of', label: 'Test Of' },
  { key: 'module_boundary', label: 'Module Boundary' },
  { key: 'protocol_implementation', label: 'Protocol Impl' },
  { key: 'architecture_layer', label: 'Architecture Layer' },
]

const MODULES = ['argus', 'vision', 'graph', 'analytics', 'simulation', 'routing', 'dashboard', 'cli']
const LAYERS = ['core', 'api', 'data', 'dashboard', 'infra']

export interface SidebarProps {
  open?: boolean
  onClose?: () => void
}

export function Sidebar({ open = true, onClose }: SidebarProps) {
  const {
    searchQuery,
    setSearchQuery,
    sidebarOpen,
    toggleSidebar,
    graphData,
    filteredNodes,
    filteredEdges,
    nodeTypeFilters,
    edgeTypeFilters,
    moduleFilters,
    layerFilters,
    setNodeTypeFilter,
    setEdgeTypeFilter,
    setModuleFilter,
    setLayerFilter,
    clearFilters,
    setSearchQuery: setSearch,
  } = useDashboardStore()

  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    types: true,
    edges: true,
    modules: true,
    layers: true,
  })

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const getTypeCount = (type: string) => graphData?.nodes?.filter((n: any) => n.type === type).length || 0
  const getEdgeCount = (type: string) => graphData?.edges?.filter((e: any) => e.type === type).length || 0
  const getModuleCount = (mod: string) => graphData?.nodes?.filter((n: any) => n.module === mod).length || 0
  const getLayerCount = (layer: string) => graphData?.nodes?.filter((n: any) => n.layer === layer).length || 0

  const activeTypeFilters = Object.values(nodeTypeFilters).filter(Boolean).length
  const activeEdgeFilters = Object.values(edgeTypeFilters).filter(Boolean).length
  const activeModuleFilters = Object.values(moduleFilters).filter(Boolean).length
  const activeLayerFilters = Object.values(layerFilters).filter(Boolean).length

  return (
    <aside
      className={cn(
        'flex flex-col bg-dark-950/95 backdrop-blur-xl border-r border-dark-700/50 transition-all duration-300',
        open ? 'w-72 min-w-[288px]' : 'w-0 min-w-0 overflow-hidden'
      )}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between h-14 px-4 border-b border-dark-700/50 bg-dark-950/80 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500 flex items-center justify-center">
              <Filter className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-dark-100 text-sm">Filters</span>
            <span className="px-2 py-0.5 text-xs bg-primary-500/20 text-primary-400 rounded">
              {filteredNodes.length} nodes
            </span>
          </div>
          <button onClick={onClose || toggleSidebar} className="p-1.5 rounded-lg hover:bg-dark-700/50 transition-colors" aria-label="Close sidebar">
            <X className="w-4 h-4 text-dark-400" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-dark-700/50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-500" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 pl-10 text-sm bg-dark-800 border border-dark-600 rounded-lg text-dark-100 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="px-4 py-2 border-b border-dark-700/50 flex gap-2">
          <button
            onClick={clearFilters}
            className="flex-1 py-2 px-3 text-xs font-medium rounded-lg bg-dark-800 border border-dark-600 text-dark-300 hover:bg-dark-700 hover:text-dark-100 transition-colors flex items-center justify-center gap-1"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Reset
          </button>
          <button
            onClick={() => {
              // Select all node types
              NODE_TYPES.forEach(t => setNodeTypeFilter(t.key, true))
              EDGE_TYPES.forEach(t => setEdgeTypeFilter(t.key, true))
              MODULES.forEach(m => setModuleFilter(m, true))
              LAYERS.forEach(l => setLayerFilter(l, true))
            }}
            className="flex-1 py-2 px-3 text-xs font-medium rounded-lg bg-primary-500/10 border border-primary-500/30 text-primary-400 hover:bg-primary-500/20 transition-colors flex items-center justify-center gap-1"
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            All
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Node Types */}
          <FilterSection
            title="Node Types"
            icon={<LayoutDashboard className="w-3.5 h-3.5" />}
            expanded={expandedSections.types}
            onToggle={() => toggleSection('types')}
            count={`${activeTypeFilters} / ${NODE_TYPES.length} active`}
            badge={filteredNodes.length > 0 ? filteredNodes.length : undefined}
          >
            <div className="space-y-1">
              {NODE_TYPES.map(({ key, label, icon: Icon }) => {
                const count = getTypeCount(key)
                const isActive = !!nodeTypeFilters[key]
                return (
                  <label key={key} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => setNodeTypeFilter(key, !isActive)}
                      className="w-4 h-4 rounded border-dark-600 text-primary-500 focus:ring-primary-500 focus:ring-2 bg-dark-800"
                    />
                    <Icon className="w-3.5 h-3.5 text-dark-400 group-hover:text-dark-200 transition-colors" />
                    <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors flex-1 truncate">{label}</span>
                    <span className={`text-xs font-mono ${count > 0 ? 'text-dark-400' : 'text-dark-600'}`}>{count}</span>
                  </label>
                )
              })}
            </div>
          </FilterSection>

          {/* Edge Types */}
          <FilterSection
            title="Edge Types"
            icon={<Network className="w-3.5 h-3.5" />}
            expanded={expandedSections.edges}
            onToggle={() => toggleSection('edges')}
            count={`${activeEdgeFilters} / ${EDGE_TYPES.length} active`}
          >
            <div className="space-y-1">
              {EDGE_TYPES.map(({ key, label }) => {
                const count = getEdgeCount(key)
                const isActive = !!edgeTypeFilters[key]
                return (
                  <label key={key} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => setEdgeTypeFilter(key, !isActive)}
                      className="w-4 h-4 rounded border-dark-600 text-primary-500 focus:ring-primary-500 focus:ring-2 bg-dark-800"
                    />
                    <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors flex-1 truncate">{label}</span>
                    <span className={`text-xs font-mono ${count > 0 ? 'text-dark-400' : 'text-dark-600'}`}>{count}</span>
                  </label>
                )
              })}
            </div>
          </FilterSection>

          {/* Modules */}
          <FilterSection
            title="Modules"
            icon={<Network className="w-3.5 h-3.5" />}
            expanded={expandedSections.modules}
            onToggle={() => toggleSection('modules')}
            count={`${activeModuleFilters} / ${MODULES.length} active`}
          >
            <div className="space-y-1">
              {MODULES.map(mod => {
                const count = getModuleCount(mod)
                const isActive = !!moduleFilters[mod]
                return (
                  <label key={mod} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => setModuleFilter(mod, !isActive)}
                      className="w-4 h-4 rounded border-dark-600 text-primary-500 focus:ring-primary-500 focus:ring-2 bg-dark-800"
                    />
                    <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors capitalize flex-1 truncate">{mod}</span>
                    <span className={`text-xs font-mono ${count > 0 ? 'text-dark-400' : 'text-dark-600'}`}>{count}</span>
                  </label>
                )
              })}
            </div>
          </FilterSection>

          {/* Layers */}
          <FilterSection
            title="Architecture Layers"
            icon={<SlidersHorizontal className="w-3.5 h-3.5" />}
            expanded={expandedSections.layers}
            onToggle={() => toggleSection('layers')}
            count={`${activeLayerFilters} / ${LAYERS.length} active`}
          >
            <div className="space-y-1">
              {LAYERS.map(layer => {
                const count = getLayerCount(layer)
                const isActive = !!layerFilters[layer]
                return (
                  <label key={layer} className="flex items-center gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={isActive}
                      onChange={() => setLayerFilter(layer, !isActive)}
                      className="w-4 h-4 rounded border-dark-600 text-primary-500 focus:ring-primary-500 focus:ring-2 bg-dark-800"
                    />
                    <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors capitalize flex-1 truncate">{layer}</span>
                    <span className={`text-xs font-mono ${count > 0 ? 'text-dark-400' : 'text-dark-600'}`}>{count}</span>
                  </label>
                )
              })}
            </div>
          </FilterSection>
        </div>
      </div>
    </aside>
  )
}

interface FilterSectionProps {
  title: string
  icon: React.ReactNode
  expanded: boolean
  onToggle: () => void
  count: string
  badge?: number
  children: React.ReactNode
}

function FilterSection({ title, icon, expanded, onToggle, count, badge, children }: FilterSectionProps) {
  return (
    <div className="bg-dark-900/50 rounded-xl border border-dark-700/50 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-dark-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-dark-800 text-primary-400">{icon}</div>
          <div>
            <div className="text-xs font-semibold text-dark-300 uppercase tracking-wider">{title}</div>
            <div className="text-xs text-dark-500">{count}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {badge !== undefined && (
            <span className="px-2 py-0.5 text-xs bg-primary-500/20 text-primary-400 rounded font-mono">{badge}</span>
          )}
          <ChevronDown className={cn('w-4 h-4 text-dark-400 transition-transform', expanded && 'rotate-180')} />
        </div>
      </button>
      {expanded && (
        <div className="px-3 pb-3 border-t border-dark-700/50 animate-in fade-in slide-in-from-top-2 duration-200">
          {children}
        </div>
      )}
    </div>
  )
}

export default Sidebar
