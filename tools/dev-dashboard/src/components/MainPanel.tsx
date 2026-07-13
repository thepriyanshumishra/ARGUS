import React, { useRef, useEffect, useState, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { GraphNodes, GraphEdges, GraphBackground, GraphControls, GraphRaycaster } from './Graph3D'
import { LoadingGraph, EmptyState } from './Legend'
import { useDashboardStore } from '../store'
import { cn } from '../utils/cn'

export function MainPanel() {
  const {
    viewMode,
    setViewMode,
    filteredNodes,
    filteredEdges,
    colorScheme,
    loading,
    setSelectedNode,
    setHoveredNode,
    pinnedNodes,
  } = useDashboardStore()

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [canvasReady, setCanvasReady] = useState(false)

  useEffect(() => {
    const observer = new ResizeObserver(() => {})
    if (containerRef.current) observer.observe(containerRef.current)
    return () => observer.disconnect()
  }, [])

  return (
    <main className="flex-1 relative overflow-hidden bg-dark-950">
      {(loading || !canvasReady) && <LoadingGraph />}

      {canvasReady && !loading && filteredNodes.length === 0 && (
        <div className="absolute inset-0 z-40 flex items-center justify-center">
          <EmptyState />
        </div>
      )}

      <div ref={containerRef} className="absolute inset-0">
        <Canvas
          ref={canvasRef}
          camera={{ position: [0, 0, 220], fov: 50 }}
          gl={{
            antialias: true,
            alpha: true,
            powerPreference: 'high-performance',
            preserveDrawingBuffer: true
          }}
          onCreated={({ gl }) => {
            gl.setClearColor(0x0f172a, 1)
            setCanvasReady(true)
          }}
          onPointerMissed={() => setSelectedNode(null)}
        >
          <color attach="background" args={['#0f172a']} />
          <fog attach="fog" args={['#0f172a', 0.00015, 80, 600]} />
          <Suspense fallback={null}>
            <GraphBackground />
            {filteredNodes.length > 0 && (
              <>
                <GraphEdges
                  nodes={filteredNodes}
                  edges={filteredEdges}
                  selectedNodeId={useDashboardStore.getState().selectedNodeId}
                  hoveredNodeId={useDashboardStore.getState().hoveredNodeId}
                />
                <GraphNodes
                  nodes={filteredNodes}
                  colorScheme={colorScheme}
                  selectedNodeId={useDashboardStore.getState().selectedNodeId}
                  hoveredNodeId={useDashboardStore.getState().hoveredNodeId}
                  pinnedNodes={pinnedNodes}
                  onNodeClick={setSelectedNode}
                  onNodeHover={setHoveredNode}
                />
              </>
            )}
          </Suspense>
          <GraphControls />
          <GraphRaycaster />
        </Canvas>
      </div>

      {canvasReady && (
        <div className="absolute inset-0 pointer-events-none">
          {/* Top-left: Legend & Stats */}
          <div className="absolute top-4 left-4 pointer-events-auto">
            <div className="glass-strong rounded-xl p-3 min-w-[220px] shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-dark-100 text-sm">Legend</h4>
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary-500/20 text-primary-400 border border-primary-500/30">
                  {colorScheme}
                </span>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-dark-300">
                  <div className="w-3 h-3 rounded-full bg-primary-500 shadow-[0_0_8px_rgba(14,165,233,0.6)]" />
                  <span>Selected Node</span>
                </div>
                <div className="flex items-center gap-2 text-dark-300">
                  <div className="w-3 h-3 rounded-full bg-amber-400/50 ring-2 ring-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.4)]" />
                  <span>Pinned</span>
                </div>
                <div className="flex items-center gap-2 text-dark-300">
                  <div className="w-3 h-3 rounded-full bg-emerald-400/50 ring-2 ring-emerald-400" />
                  <span>Hovered</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-dark-700/50 space-y-1.5">
                <div className="flex items-center justify-between text-xs text-dark-400">
                  <span>Nodes</span>
                  <span className="text-dark-100 font-mono font-medium">{filteredNodes.length}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-dark-400">
                  <span>Edges</span>
                  <span className="text-dark-100 font-mono font-medium">{filteredEdges?.length || 0}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-dark-400">
                  <span>Avg Degree</span>
                  <span className="text-dark-100 font-mono font-medium">
                    {filteredNodes.length > 0 ? ((filteredEdges?.length || 0) * 2 / filteredNodes.length).toFixed(1) : '0'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Top-right: View Modes */}
          <div className="absolute top-4 right-4 pointer-events-auto">
            <div className="glass-strong rounded-xl p-2 shadow-xl">
              <div className="grid grid-cols-2 gap-1">
                {(['galaxy', 'force', 'hierarchy', 'layers'] as const).map(mode => (
                  <button
                    key={mode}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                      viewMode === mode
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30 shadow-[0_0_12px_rgba(14,165,233,0.2)]'
                        : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700/50'
                    )}
                    onClick={() => setViewMode(mode)}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Color Scheme Selector */}
            <div className="glass-strong rounded-xl p-2 shadow-xl mt-2 min-w-[160px]">
              <div className="text-xs font-medium text-dark-400 mb-1 uppercase tracking-wide">Color By</div>
              <div className="grid grid-cols-2 gap-1">
                {(['type', 'module', 'layer'] as const).map(scheme => (
                  <button
                    key={scheme}
                    className={cn(
                      'px-2 py-1 rounded-lg text-xs font-medium transition-all',
                      colorScheme === scheme
                        ? 'bg-primary-500/20 text-primary-400 border border-primary-500/30'
                        : 'text-dark-400 hover:text-dark-100 hover:bg-dark-700/50'
                    )}
                    onClick={() => useDashboardStore.getState().setColorScheme(scheme)}
                  >
                    {scheme.charAt(0).toUpperCase() + scheme.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom-center: Connection Stats Bar */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 pointer-events-auto">
            <div className="glass-strong rounded-xl px-6 py-3 flex items-center gap-8 shadow-xl border border-dark-600/30">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-400 font-mono">{filteredNodes.length}</div>
                <div className="text-xs text-dark-400 uppercase tracking-wide">Nodes</div>
              </div>
              <div className="w-px h-8 bg-dark-700" />
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-400 font-mono">{filteredEdges?.length || 0}</div>
                <div className="text-xs text-dark-400 uppercase tracking-wide">Edges</div>
              </div>
              <div className="w-px h-8 bg-dark-700" />
              <div className="text-center">
                <div className="text-2xl font-bold text-amber-400 font-mono">
                  {filteredNodes.length > 0 ? ((filteredEdges?.length || 0) * 2 / filteredNodes.length).toFixed(1) : '0'}
                </div>
                <div className="text-xs text-dark-400 uppercase tracking-wide">Avg Deg</div>
              </div>
              <div className="w-px h-8 bg-dark-700" />
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-400 font-mono">
                  {pinnedNodes.length}
                </div>
                <div className="text-xs text-dark-400 uppercase tracking-wide">Pinned</div>
              </div>
            </div>
          </div>

          {/* Bottom-left: Node Detail Panel */}
          {useDashboardStore.getState().selectedNodeId && (
            <div className="absolute bottom-4 left-4 pointer-events-auto">
              <NodeDetailPanel
                node={filteredNodes.find(n => n.id === useDashboardStore.getState().selectedNodeId)}
                onClose={() => setSelectedNode(null)}
                onPin={() => {
                  const id = useDashboardStore.getState().selectedNodeId
                  if (id) useDashboardStore.getState().togglePinNode(id)
                }}
                isPinned={pinnedNodes.includes(useDashboardStore.getState().selectedNodeId || '')}
              />
            </div>
          )}
        </div>
      )}
    </main>
  )
}

function NodeDetailPanel({ node, onClose, onPin, isPinned }: {
  node: any;
  onClose: () => void;
  onPin: () => void;
  isPinned: boolean;
}) {
  if (!node) return null

  const color = node.type && NODE_TYPE_COLORS[node.type] || '#888888'

  return (
    <div className="glass-strong rounded-xl p-4 min-w-[280px] max-w-[360px] shadow-xl border border-dark-600/30 animate-in slide-in-from-bottom-4 duration-300">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
            <div className="w-5 h-5 rounded" style={{ backgroundColor: color }} />
          </div>
          <div>
            <h4 className="font-semibold text-dark-100 truncate max-w-[200px]">{node.name || node.id}</h4>
            <div className="flex items-center gap-2 text-xs text-dark-400">
              <span className="px-2 py-0.5 rounded-full bg-dark-700/50 border border-dark-600">{node.type}</span>
              {node.module && <span className="px-2 py-0.5 rounded-full bg-dark-700/50 border border-dark-600">{node.module}</span>}
            </div>
          </div>
        </div>
        <button onClick={onClose} className="text-dark-400 hover:text-dark-100 p-1 rounded-lg hover:bg-dark-700/50 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {node.file && (
        <div className="mb-3 p-2 rounded-lg bg-dark-800/50 border border-dark-700/50">
          <div className="text-xs text-dark-400 mb-1">File</div>
          <div className="text-xs font-mono text-dark-200 truncate">{node.file}</div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="p-2 rounded-lg bg-dark-800/50 border border-dark-700/50">
          <div className="text-xs text-dark-400">In Degree</div>
          <div className="font-mono font-medium text-dark-100">{node.inDegree || 0}</div>
        </div>
        <div className="p-2 rounded-lg bg-dark-800/50 border border-dark-700/50">
          <div className="text-xs text-dark-400">Out Degree</div>
          <div className="font-mono font-medium text-dark-100">{node.outDegree || 0}</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onPin}
          className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            isPinned
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
              : 'bg-dark-700/50 text-dark-300 hover:bg-dark-600/50 border border-dark-600/50'
          }`}
        >
          {isPinned ? 'Unpin' : 'Pin Node'}
        </button>
        <button
          onClick={onClose}
          className="px-3 py-2 rounded-lg text-sm font-medium bg-dark-700/50 text-dark-300 hover:bg-dark-600/50 border border-dark-600/50 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  )
}

// Import color constants for NodeDetailPanel
import { NODE_TYPE_COLORS } from '../types/graph'

export default MainPanel
