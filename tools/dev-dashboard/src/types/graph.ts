export interface GraphNode {
  id: string
  label: string
  type: NodeType
  filePath?: string
  lineNumber?: number
  exports?: string[]
  imports?: string[]
  complexity?: number
  size?: number
  metadata?: Record<string, any>
}

export type NodeType =
  | 'directory'
  | 'package'
  | 'module'
  | 'file'
  | 'class'
  | 'protocol'
  | 'function'
  | 'method'
  | 'enum'
  | 'dataclass'
  | 'config'
  | 'test'
  | 'script'
  | 'asset'
  | 'documentation'

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: EdgeType
  weight?: number
  metadata?: Record<string, any>
}

export type EdgeType =
  | 'imports'
  | 'contains'
  | 'inherits'
  | 'implements'
  | 'calls'
  | 'references'
  | 'uses'
  | 'owns'
  | 'depends_on'
  | 'configuration'
  | 'test_of'
  | 'module_boundary'
  | 'protocol_implementation'
  | 'architecture_layer'

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: GraphMetadata
}

export interface GraphMetadata {
  totalNodes: number
  totalEdges: number
  nodeTypes: Record<NodeType, number>
  edgeTypes: Record<EdgeType, number>
  lastIndexed: string
  projectName: string
  projectPath: string
  gitBranch?: string
  gitCommit?: string
  linesOfCode: number
  testFiles: number
  configFiles: number
  documentationFiles: number
}

export interface ViewMode {
  id: string
  name: string
  icon: string
  description: string
}

export const VIEW_MODES: ViewMode[] = [
  { id: 'galaxy', name: '3D Galaxy', icon: 'globe', description: 'Immersive 3D galaxy view' },
  { id: 'force', name: 'Force Directed', icon: 'atom', description: 'Force-directed graph layout' },
  { id: 'hierarchy', name: 'Hierarchy', icon: 'git-branch', description: 'Hierarchical tree view' },
  { id: 'layers', name: 'Architecture Layers', icon: 'layers', description: 'Architecture layer view' },
  { id: 'modules', name: 'Module Dependencies', icon: 'package', description: 'Module dependency graph' },
  { id: 'directory', name: 'Directory Tree', icon: 'folder-tree', description: 'File system tree view' },
  { id: 'imports', name: 'Import Graph', icon: 'arrow-right-left', description: 'Import relationships' },
  { id: 'classes', name: 'Class Diagram', icon: 'square-stack', description: 'Class relationships' },
  { id: 'protocols', name: 'Protocol View', icon: 'code-2', description: 'Protocol implementations' },
  { id: 'analytics', name: 'Analytics', icon: 'bar-chart-3', description: 'Repository analytics' },
]

export interface FilterState {
  nodeTypes: Set<NodeType>
  edgeTypes: Set<EdgeType>
  searchQuery: string
  showOnlyConnected: boolean
  maxDepth: number
  colorScheme: ColorScheme
}

export type ColorScheme = 'type' | 'module' | 'layer' | 'directory' | 'complexity' | 'connectivity'

export interface CameraState {
  position: { x: number; y: number; z: number }
  target: { x: number; y: number; z: number }
  zoom: number
}

export interface SelectedNode {
  node: GraphNode | null
  neighbors: GraphNode[]
  edges: GraphEdge[]
}

export const NODE_TYPE_COLORS: Partial<Record<NodeType, string>> = {
  directory: '#64748b',
  package: '#0ea5e9',
  module: '#06b6d4',
  file: '#22d3ee',
  class: '#f59e0b',
  protocol: '#f97316',
  function: '#84cc16',
  method: '#a3e635',
  enum: '#ec4899',
  dataclass: '#d946ef',
  config: '#6366f1',
  test: '#14b8a6',
  script: '#eab308',
  asset: '#64748b',
  documentation: '#64748b',
}

export const MODULE_COLORS: Record<string, string> = {
  argus: '#0ea5e9',
  vision: '#f59e0b',
  graph: '#06b6d4',
  analytics: '#22d3ee',
  simulation: '#14b8a6',
  routing: '#6366f1',
  dashboard: '#8b5cf6',
  cli: '#f97316',
  core: '#ef4444',
  data: '#22c55e',
}

export const LAYER_COLORS: Record<string, string> = {
  core: '#ef4444',
  internal: '#f97316',
  api: '#f59e0b',
  cli: '#eab308',
  data: '#22c55e',
  vision: '#14b8a6',
  graph: '#06b6d4',
  analytics: '#0ea5e9',
  simulation: '#3b82f6',
  routing: '#6366f1',
  dashboard: '#8b5cf6',
}

export const EDGE_TYPE_COLORS: Partial<Record<EdgeType, string>> = {
  imports: '#22d3ee',
  contains: '#64748b',
  inherits: '#f59e0b',
  implements: '#f97316',
  calls: '#84cc16',
  references: '#a3e635',
  uses: '#06b6d4',
  owns: '#6366f1',
  depends_on: '#ec4899',
  configuration: '#8b5cf6',
  test_of: '#14b8a6',
  module_boundary: '#0ea5e9',
  protocol_implementation: '#d946ef',
  architecture_layer: '#ef4444',
}
