import { create } from 'zustand'

export type ConnectionStatus = 'disconnected' | 'connected' | 'checking'

export interface GraphNode {
  x: number
  y: number
}

export interface GraphEdge {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  imgWidth: number
  imgHeight: number
  nodeCount: number
  edgeCount: number
}

interface AppState {
  // Authentication
  isAuthenticated: boolean
  authToken: string | null
  setIsAuthenticated: (auth: boolean) => void
  setAuthToken: (token: string | null) => void
  logout: () => void

  // Backend connection
  connectionStatus: ConnectionStatus
  setConnectionStatus: (status: ConnectionStatus) => void
  checkBackendHealth: () => Promise<void>

  // Ingestion data
  selectedImage: File | null
  imageName: string | null
  imageSize: string | null
  imageUrl: string | null  // object URL or static path for the selected image
  setSelectedImage: (image: File | null) => void
  setImageUrlDirectly: (url: string, name: string, size: string) => void

  // Extraction results
  extractionProgress: number
  isExtracting: boolean
  graphData: GraphData | null
  maskB64: string | null
  skeletonB64: string | null
  extractionError: string | null
  setExtractionProgress: (progress: number) => void
  setIsExtracting: (isExtracting: boolean) => void
  setGraphData: (data: GraphData | null) => void
  setMaskB64: (mask: string | null) => void
  setSkeletonB64: (skel: string | null) => void
  setExtractionError: (error: string | null) => void

  // Reset store
  resetStore: () => void
}

const API_BASE_URL = typeof window !== 'undefined'
  ? (window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
      ? 'http://localhost:8000'
      : window.location.origin)
  : 'http://localhost:8000';

export const useAppStore = create<AppState>((set, get) => ({
  // Authentication initial state read from localStorage
  isAuthenticated: !!localStorage.getItem('argus_token'),
  authToken: localStorage.getItem('argus_token'),
  setIsAuthenticated: (auth) => set({ isAuthenticated: auth }),
  setAuthToken: (token) => {
    if (token) {
      localStorage.setItem('argus_token', token)
    } else {
      localStorage.removeItem('argus_token')
    }
    set({ authToken: token, isAuthenticated: !!token })
  },
  logout: () => {
    localStorage.removeItem('argus_token')
    get().resetStore()
    set({ authToken: null, isAuthenticated: false })
  },

  connectionStatus: 'checking',
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  checkBackendHealth: async () => {
    set({ connectionStatus: 'checking' })
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (response.ok) {
        set({ connectionStatus: 'connected' })
      } else {
        set({ connectionStatus: 'disconnected' })
      }
    } catch {
      set({ connectionStatus: 'disconnected' })
    }
  },

  selectedImage: null,
  imageName: null,
  imageSize: null,
  imageUrl: null,
  setSelectedImage: (image) => {
    // Revoke previous object URL to avoid memory leak
    const prevUrl = get().imageUrl
    if (prevUrl && prevUrl.startsWith('blob:')) {
      URL.revokeObjectURL(prevUrl)
    }
    if (!image) {
      set({ selectedImage: null, imageName: null, imageSize: null, imageUrl: null })
      return
    }
    const sizeInMB = (image.size / (1024 * 1024)).toFixed(2) + ' MB'
    const url = URL.createObjectURL(image)
    set({ selectedImage: image, imageName: image.name, imageSize: sizeInMB, imageUrl: url })
  },
  setImageUrlDirectly: (url, name, size) => {
    const prevUrl = get().imageUrl
    if (prevUrl && prevUrl.startsWith('blob:')) {
      URL.revokeObjectURL(prevUrl)
    }
    set({ selectedImage: null, imageUrl: url, imageName: name, imageSize: size })
  },

  extractionProgress: 0,
  isExtracting: false,
  graphData: null,
  maskB64: null,
  skeletonB64: null,
  extractionError: null,
  setExtractionProgress: (progress) => set({ extractionProgress: progress }),
  setIsExtracting: (isExtracting) => set({ isExtracting }),
  setGraphData: (data) => set({ graphData: data }),
  setMaskB64: (mask) => set({ maskB64: mask }),
  setSkeletonB64: (skel) => set({ skeletonB64: skel }),
  setExtractionError: (error) => set({ extractionError: error }),

  resetStore: () => {
    const prevUrl = get().imageUrl
    if (prevUrl && prevUrl.startsWith('blob:')) {
      URL.revokeObjectURL(prevUrl)
    }
    set({
      selectedImage: null,
      imageName: null,
      imageSize: null,
      imageUrl: null,
      extractionProgress: 0,
      isExtracting: false,
      graphData: null,
      maskB64: null,
      skeletonB64: null,
      extractionError: null,
    })
  },
}))
