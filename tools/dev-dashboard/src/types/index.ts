export interface GraphNode {
  id: string
  name: string
  qualifiedName: string
  type: NodeType
  label: string
  filePath: string
  module: string
  directory: string
  layer: ArchitectureLayer
  size: number
  complexity: number
  inDegree: number
  outDegree: number
  isExported: boolean
  isTest: boolean
  isEntryPoint: boolean
  docstring?: string
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

export type ArchitectureLayer =
  | 'core'
  | 'internal'
  | 'api'
  | 'cli'
  | 'data'
  | 'vision'
  | 'graph'
  | 'analytics'
  | 'simulation'
  | 'routing'
  | 'dashboard'
  | 'test'
  | 'validation'
  | 'config'
  | 'docs'
  | 'external'

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

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: EdgeType
  weight: number
  metadata?: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata: GraphMetadata
}

export interface GraphMetadata {
  projectName: string
  projectPath: string
  totalNodes: number
  totalEdges: number
  nodeTypeCounts: Record<string, number>
  edgeTypeCounts: Record<string, number>
  linesOfCode: number
  testFiles: number
  configFiles: number
  documentationFiles: number
  lastIndexed: string
  languages: string[]
  packages: string[]
}

export interface RepositoryStats {
  totalFiles: number
  pythonFiles: number
  classes: number
  functions: number
  protocols: number
  modules: number
  directories: number
  linesOfCode: number
  comments: number
  testFiles: number
  configs: number
  assets: number
  docs: number
  currentBranch: string
  latestCommit: string
  repoSize: number
  nodeCount: number
  edgeCount: number
  graphDensity: number
  avgDegree: number
  largestComponent: number
  mostConnectedFiles: string[]
  mostImportedModules: string[]
  largestFiles: string[]
  largestModules: string[]
}

export interface ViewMode {
  id: string
  name: string
  description: string
  icon: string
}

export const VIEW_MODES: ViewMode[] = [
  { id: 'galaxy', name: '3D Galaxy', description: '3D galaxy view with rotation', icon: 'globe' },
  { id: 'force', name: 'Force Directed', description: 'Force-directed graph layout', icon: 'network' },
  { id: 'hierarchy', name: 'Hierarchical', description: 'Hierarchical tree layout', icon: 'git-branch' },
  { id: 'layers', name: 'Architecture Layers', description: 'Architecture layer view', icon: 'layers' },
  { id: 'modules', name: 'Module Dependencies', description: 'Module dependency graph', icon: 'package' },
  { id: 'tree', name: 'Directory Tree', description: 'Directory tree view', icon: 'folder-tree' },
  { id: 'imports', name: 'Import Graph', description: 'Import relationships', icon: 'arrow-down-left' },
  { id: 'classes', name: 'Class Diagram', description: 'Class relationships', icon: 'square-stack' },
  { id: 'protocols', name: 'Protocol Relationships', description: 'Protocol implementations', icon: 'git-merge' },
  { id: 'analytics', name: 'Analytics Dashboard', description: 'Repository analytics', icon: 'bar-chart' },
]

export const NODE_TYPE_COLORS: Record<string, string> = {
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

export const EDGE_TYPE_COLORS: Record<string, string> = {
  imports: '#0ea5e9',
  contains: '#64748b',
  inherits: '#f59e0b',
  implements: '#f97316',
  calls: '#84cc16',
  references: '#a3e635',
  uses: '#ec4899',
  owns: '#d946ef',
  depends_on: '#6366f1',
  configuration: '#14b8a6',
  test_of: '#eab308',
  module_boundary: '#64748b',
  protocol_implementation: '#f59e0b',
  architecture_layer: '#6366f1',
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
  test: '#64748b',
  validation: '#64748b',
  config: '#64748b',
  docs: '#64748b',
  external: '#94a3b8',
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
  tests: '#64748b',
  validation: '#64748b',
}
