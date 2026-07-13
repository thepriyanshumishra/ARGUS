import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useDashboardStore } from '../store'

interface CodebaseMemoryData {
  nodes: any[]
  edges: any[]
  metadata: any
  stats: any
}

interface CodebaseMemoryContextType {
  data: CodebaseMemoryData | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  isConnected: boolean
  lastIndexed: string | null
}

const CodebaseMemoryContext = createContext<CodebaseMemoryContextType | null>(null)

const MCP_URL = import.meta.env.VITE_MCP_URL || 'http://localhost:9749'

export function CodebaseMemoryProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<CodebaseMemoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastIndexed, setLastIndexed] = useState<string | null>(null)
  
  const { setCodebaseMemoryAvailable, setLastIndexed: setStoreLastIndexed, setRepositoryStats } = useDashboardStore()

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Check MCP status
      const statusResponse = await fetch(`${MCP_URL}/api/status`).catch(() => null)
      if (statusResponse?.ok) {
        const statusData = await statusResponse.json()
        setIsConnected(true)
        setLastIndexed(statusData.lastIndexed || null)
        setStoreLastIndexed(statusData.lastIndexed || null)
      } else {
        setIsConnected(false)
      }

      // Fetch graph data
      const graphResponse = await fetch(`${MCP_URL}/api/graph?project=ARGUS&limit=5000`).catch(() => null)
      if (graphResponse?.ok) {
        const graphData = await graphResponse.json()
        setData(graphData)
        // Update store
        const store = useDashboardStore
        store.getState().setGraphData(graphData)
        store.getState().setCodebaseMemoryAvailable(true)
        store.getState().setLastIndexed(graphData.metadata?.lastIndexed || null)
        store.getState().setRepositoryStats(graphData.metadata)
      }
    } catch (err) {
      setError('Failed to connect to Codebase Memory MCP')
      setIsConnected(false)
    } finally {
      setLoading(false)
    }
  }

  const refetch = async () => {
    await fetchData()
  }

  // Initial fetch
  useEffect(() => {
    fetchData()
    
    // Set up polling for auto-refresh
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <CodebaseMemoryContext.Provider value={{
      data,
      loading,
      error,
      refetch,
      isConnected,
      lastIndexed
    }}>
      {children}
    </CodebaseMemoryContext.Provider>
  )
}

export function useCodebaseMemory() {
  const context = useContext(CodebaseMemoryContext)
  if (!context) {
    throw new Error('useCodebaseMemory must be used within a CodebaseMemoryProvider')
  }
  return context
}