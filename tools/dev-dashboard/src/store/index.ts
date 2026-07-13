import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light' | 'system'

interface DashboardState {
  // UI State
  viewMode: 'galaxy' | 'force' | 'hierarchy' | 'layers' | 'modules' | 'tree' | 'imports' | 'classes' | 'protocols' | 'analytics'
  sidebarOpen: boolean
  analyticsOpen: boolean
  sidebarWidth: number
  analyticsWidth: number
  theme: Theme
  
  // Filters
  nodeTypeFilters: Record<string, boolean>
  edgeTypeFilters: Record<string, boolean>
  moduleFilters: Record<string, boolean>
  layerFilters: Record<string, boolean>
  searchQuery: string
  
  // Graph interaction
  selectedNodeId: string | null
  hoveredNodeId: string | null
  pinnedNodes: string[]
  focusedNodeId: string | null
  
  // Color schemes
  colorScheme: 'type' | 'module' | 'layer' | 'directory' | 'architecture'
  
  // Data
  graphData: any
  codebaseMemoryAvailable: boolean
  lastIndexed: string | null
  repositoryStats: any
  
  // Loading state
  loading: boolean
  
  // Filtered data (derived)
  filteredNodes: any[]
  filteredEdges: any[]
  
  // Actions
  setViewMode: (mode: DashboardState['viewMode']) => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  toggleAnalytics: () => void
  setAnalyticsOpen: (open: boolean) => void
  setSidebarWidth: (width: number) => void
  setAnalyticsWidth: (width: number) => void
  setTheme: (theme: Theme) => void
  
  setNodeTypeFilter: (type: string, enabled: boolean) => void
  setEdgeTypeFilter: (type: string, enabled: boolean) => void
  setModuleFilter: (module: string, enabled: boolean) => void
  setLayerFilter: (layer: string, enabled: boolean) => void
  setSearchQuery: (query: string) => void
  clearFilters: () => void
  
  setSelectedNode: (id: string | null) => void
  setHoveredNode: (id: string | null) => void
  togglePinNode: (id: string) => void
  setFocusedNode: (id: string | null) => void
  
  setColorScheme: (scheme: 'type' | 'module' | 'layer' | 'directory' | 'architecture') => void
  
  setGraphData: (data: any) => void
  setCodebaseMemoryAvailable: (available: boolean) => void
  setLastIndexed: (time: string) => void
  setRepositoryStats: (stats: any) => void
  setLoading: (loading: boolean) => void
  
  initialize: () => Promise<void>
  refetchGraph: () => Promise<void>
  setFilteredData: (nodes: any[], edges: any[]) => void
}

const defaultNodeTypes = [
  'directory', 'package', 'module', 'file', 'class', 'protocol', 
  'function', 'method', 'enum', 'dataclass', 'config', 'test', 
  'script', 'asset', 'documentation'
]

const defaultEdgeTypes = [
  'imports', 'contains', 'inherits', 'implements', 'calls', 
  'references', 'uses', 'owns', 'depends_on', 'configuration', 
  'test_of', 'module_boundary', 'protocol_implementation', 'architecture_layer'
]

const defaultNodeTypeFilters = Object.fromEntries(defaultNodeTypes.map(t => [t, true]))
const defaultEdgeTypeFilters = Object.fromEntries(defaultEdgeTypes.map(t => [t, true]))

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set, get) => ({
      // UI State
      viewMode: 'galaxy',
      sidebarOpen: true,
      analyticsOpen: true,
      sidebarWidth: 280,
      analyticsWidth: 360,
      theme: 'dark',
      
      // Filters
      nodeTypeFilters: Object.fromEntries(defaultNodeTypes.map(t => [t, true])),
      edgeTypeFilters: Object.fromEntries(defaultEdgeTypes.map(t => [t, true])),
      moduleFilters: {},
      layerFilters: {},
      searchQuery: '',
      
      // Graph interaction
      selectedNodeId: null,
      hoveredNodeId: null,
      pinnedNodes: [],
      focusedNodeId: null,
      
      // Color schemes
      colorScheme: 'type',
      
      // Data
      graphData: null,
      codebaseMemoryAvailable: false,
      lastIndexed: null,
      repositoryStats: null,
      
      // Loading
      loading: true,
      
      // Filtered data
      filteredNodes: [],
      filteredEdges: [],
      
      // Actions
      setViewMode: (mode) => set({ viewMode: mode }),
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      toggleAnalytics: () => set((state) => ({ analyticsOpen: !state.analyticsOpen })),
      setAnalyticsOpen: (open) => set({ analyticsOpen: open }),
      
      setSidebarWidth: (width) => set({ sidebarWidth: Math.max(200, Math.min(500, width)) }),
      setAnalyticsWidth: (width) => set({ analyticsWidth: Math.max(250, Math.min(500, width)) }),
      setTheme: (theme) => set({ theme }),
      
      setNodeTypeFilter: (type, enabled) => set((state) => ({
        nodeTypeFilters: { ...state.nodeTypeFilters, [type]: enabled }
      })),
      
      setEdgeTypeFilter: (type, enabled) => set((state) => ({
        edgeTypeFilters: { ...state.edgeTypeFilters, [type]: enabled }
      })),
      
      setModuleFilter: (module, enabled) => set((state) => ({
        moduleFilters: { ...state.moduleFilters, [module]: enabled }
      })),
      
      setLayerFilter: (layer, enabled) => set((state) => ({
        layerFilters: { ...state.layerFilters, [layer]: enabled }
      })),
      
      setSearchQuery: (query) => set({ searchQuery: query }),
      
      clearFilters: () => set({
        nodeTypeFilters: Object.fromEntries(defaultNodeTypes.map(t => [t, true])),
        edgeTypeFilters: Object.fromEntries(defaultEdgeTypes.map(t => [t, true])),
        moduleFilters: {},
        layerFilters: {},
        searchQuery: '',
      }),
      
      setSelectedNode: (id) => set({ selectedNodeId: id }),
      setHoveredNode: (id) => set({ hoveredNodeId: id }),
      
      togglePinNode: (id) => set((state) => ({
        pinnedNodes: state.pinnedNodes.includes(id)
          ? state.pinnedNodes.filter(n => n !== id)
          : [...state.pinnedNodes, id]
      })),
      
      setFocusedNode: (id) => set({ focusedNodeId: id }),
      
      setColorScheme: (scheme) => set({ colorScheme: scheme }),
      
      setGraphData: (data) => {
        set({ 
          graphData: data,
          loading: false 
        })
        // Apply filters after data filtering
        const { filteredNodes, filteredEdges } = filterData(data)
        set({ filteredNodes, filteredEdges })
      },
      
      setCodebaseMemoryAvailable: (available) => set({ codebaseMemoryAvailable: available }),
      setLastIndexed: (time) => set({ lastIndexed: time }),
      setRepositoryStats: (stats) => set({ repositoryStats: stats }),
      
      setLoading: (loading) => set({ loading }),
      
      initialize: async () => {
        set({ loading: true })
        try {
          // Try to connect to Codebase Memory MCP
          const response = await fetch('http://localhost:9749/api/status').catch(() => null)
          if (response?.ok) {
            const data = await response.json()
            set({ 
              codebaseMemoryAvailable: true,
              lastIndexed: data.lastIndexed || null,
            })
          } else {
            set({ codebaseMemoryAvailable: false })
          }
          
          // Try to fetch graph data
          const graphResponse = await fetch('http://localhost:9749/api/graph?project=ARGUS&limit=5000').catch(() => null)
          if (graphResponse?.ok) {
            const data = await graphResponse.json()
            set({ graphData: data, loading: false })
            // Apply filtering
            const { filteredNodes, filteredEdges } = filterData(data)
            set({ filteredNodes, filteredEdges })
          } else {
            set({ loading: false })
          }
        } catch (err) {
          set({ loading: false, codebaseMemoryAvailable: false })
        }
      },
      
      refetchGraph: async () => {
        const { graphData } = get()
        if (!graphData) return
        
        try {
          const response = await fetch('http://localhost:9749/api/graph?project=ARGUS&limit=5000').catch(() => null)
          if (response?.ok) {
            const data = await response.json()
            set({ graphData: data })
            const { filteredNodes, filteredEdges } = filterData(data)
            set({ filteredNodes, filteredEdges })
          }
        } catch (err) {
          console.error('Failed to refetch graph:', err)
        }
      },
      
      setFilteredData: (nodes, edges) => set({ filteredNodes: nodes, filteredEdges: edges }),
    }),
    {
      name: 'argus-dev-dashboard',
      partialize: (state) => ({
        viewMode: state.viewMode,
        sidebarOpen: state.sidebarOpen,
        analyticsOpen: state.analyticsOpen,
        sidebarWidth: state.sidebarWidth,
        analyticsWidth: state.analyticsWidth,
        nodeTypeFilters: state.nodeTypeFilters,
        edgeTypeFilters: state.edgeTypeFilters,
        colorScheme: state.colorScheme,
        pinnedNodes: state.pinnedNodes,
      }),
    }
  )
)

function filterData(data: any) {
  if (!data) return { filteredNodes: [], filteredEdges: [] }
  
  const nodes = data.nodes || []
  const edges = data.edges || []
  
  // For now just return all - filtering can be added later
  return { 
    filteredNodes: nodes, 
    filteredEdges: edges 
  }
}