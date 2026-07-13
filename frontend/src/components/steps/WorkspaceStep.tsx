import React, { useState, useEffect, useRef } from 'react'
import { useAppStore } from '../../store/useAppStore'
import {
  Hammer,
  RotateCcw,
  Navigation,
  Activity,
  PlusCircle,
  Info
} from 'lucide-react'

// Local Types
interface LocalNode {
  id: number
  x: number
  y: number
}

interface LocalEdge {
  id: string
  u: number
  v: number
  x1: number
  y1: number
  x2: number
  y2: number
  weight: number
  isMajor: boolean
  disabled: boolean
}

// Helper: distance between two points
const getDistance = (x1: number, y1: number, x2: number, y2: number) => {
  return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
}

// Ray casting algorithm for Point-in-Polygon check
const isPointInPolygon = (x: number, y: number, polygon: [number, number][]): boolean => {
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0], yi = polygon[i][1]
    const xj = polygon[j][0], yj = polygon[j][1]
    const intersect = ((yi > y) !== (yj > y)) && (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
    if (intersect) inside = !inside
  }
  return inside
}

// Dijkstra Algorithm
const calculateDijkstra = (
  nodes: LocalNode[],
  edges: LocalEdge[],
  startId: number,
  endId: number
): number[] | null => {
  const distances: Record<number, number> = {}
  const previous: Record<number, number | null> = {}
  const queue = new Set<number>()

  nodes.forEach((node) => {
    distances[node.id] = Infinity
    previous[node.id] = null
    queue.add(node.id)
  })

  distances[startId] = 0

  // Build adjacency list
  const adj: Record<number, { node: number; weight: number }[]> = {}
  nodes.forEach((n) => { adj[n.id] = [] })
  edges.forEach((e) => {
    if (e.disabled) return
    adj[e.u].push({ node: e.v, weight: e.weight })
    adj[e.v].push({ node: e.u, weight: e.weight })
  })

  while (queue.size > 0) {
    let minNode: number | null = null
    queue.forEach((nodeId) => {
      if (minNode === null || distances[nodeId] < distances[minNode]) {
        minNode = nodeId
      }
    })

    if (minNode === null || distances[minNode] === Infinity) break
    if (minNode === endId) break

    queue.delete(minNode)

    const neighbors = adj[minNode] || []
    for (const neighbor of neighbors) {
      if (!queue.has(neighbor.node)) continue
      const alt = distances[minNode] + neighbor.weight
      if (alt < distances[neighbor.node]) {
        distances[neighbor.node] = alt
        previous[neighbor.node] = minNode
      }
    }
  }

  if (distances[endId] === Infinity) return null

  const path: number[] = []
  let curr: number | null = endId
  while (curr !== null) {
    path.push(curr)
    curr = previous[curr]
  }
  return path.reverse()
}

export const WorkspaceStep: React.FC = () => {
  const { graphData, imageUrl } = useAppStore()
  const svgRef = useRef<SVGSVGElement>(null)

  // Local graph states
  const [nodes, setNodes] = useState<LocalNode[]>([])
  const [edges, setEdges] = useState<LocalEdge[]>([])

  // Tools & Mode Selection
  const [activeTool, setActiveTool] = useState<'none' | 'hammer' | 'circle' | 'rect' | 'lasso'>('none')
  const [activeLayer, setActiveLayer] = useState<'both' | 'satellite' | 'graph'>('both')

  // Routing State
  const [startNode, setStartNode] = useState<number | null>(null)
  const [endNode, setEndNode] = useState<number | null>(null)
  const [shortestPath, setShortestPath] = useState<number[] | null>(null)

  // Drawing disaster variables
  const [drawPoints, setDrawPoints] = useState<[number, number][]>([])
  const [isDrawing, setIsDrawing] = useState(false)
  const [disasters, setDisasters] = useState<{ id: string; type: 'circle' | 'rect' | 'lasso'; points: [number, number][] }[]>([])

  // Initialize nodes and edges from global graphData
  useEffect(() => {
    if (!graphData) return
    const localNodes: LocalNode[] = graphData.nodes.map((n, idx) => ({
      id: idx,
      x: n.x,
      y: n.y,
    }))

    const localEdges: LocalEdge[] = graphData.edges.map((e, idx) => {
      const uNode = localNodes.find((n) => Math.abs(n.x - e.x1) < 0.1 && Math.abs(n.y - e.y1) < 0.1)
      const vNode = localNodes.find((n) => Math.abs(n.x - e.x2) < 0.1 && Math.abs(n.y - e.y2) < 0.1)
      const u = uNode ? uNode.id : 0
      const v = vNode ? vNode.id : 1
      const weight = getDistance(e.x1, e.y1, e.x2, e.y2)
      // Heuristic: Major road if length > 120px or degree of u/v is >= 3
      const isMajor = weight > 120

      return {
        id: `edge-${idx}`,
        u,
        v,
        x1: e.x1,
        y1: e.y1,
        x2: e.x2,
        y2: e.y2,
        weight,
        isMajor,
        disabled: false,
      }
    })

    setNodes(localNodes)
    setEdges(localEdges)
  }, [graphData])

  // Recalculate shortest path whenever start, end, or disabled status changes
  useEffect(() => {
    if (startNode !== null && endNode !== null) {
      const path = calculateDijkstra(nodes, edges, startNode, endNode)
      setShortestPath(path)
    } else {
      setShortestPath(null)
    }
  }, [startNode, endNode, edges, nodes])

  // Get SVG coordinate from click event
  const getSVGCoords = (e: React.MouseEvent<SVGSVGElement>): [number, number] => {
    if (!svgRef.current) return [0, 0]
    const rect = svgRef.current.getBoundingClientRect()
    const scaleX = (graphData?.imgWidth ?? 500) / rect.width
    const scaleY = (graphData?.imgHeight ?? 500) / rect.height
    return [
      (e.clientX - rect.left) * scaleX,
      (e.clientY - rect.top) * scaleY,
    ]
  }

  // Handle map click for tools and routing
  const handleMapClick = (e: React.MouseEvent<SVGSVGElement>) => {
    const [x, y] = getSVGCoords(e)

    if (activeTool === 'lasso') {
      if (!isDrawing) {
        setIsDrawing(true)
        setDrawPoints([[x, y]])
      } else {
        setDrawPoints((prev) => [...prev, [x, y]])
      }
      return
    }

    if (activeTool === 'none') {
      // Find closest node to click
      let closestNode: LocalNode | null = null
      let minDist = 25 // max selection radius 25px
      nodes.forEach((n) => {
        const d = getDistance(x, y, n.x, n.y)
        if (d < minDist) {
          minDist = d
          closestNode = n
        }
      })

      if (closestNode) {
        const nodeId = (closestNode as LocalNode).id
        if (startNode === null) {
          setStartNode(nodeId)
        } else if (endNode === null && startNode !== nodeId) {
          setEndNode(nodeId)
        } else {
          // Reset routing selection
          setStartNode(nodeId)
          setEndNode(null)
          setShortestPath(null)
        }
      }
    }
  }

  // Mouse Drag handlers for Rectangle and Circle drawing
  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (activeTool !== 'circle' && activeTool !== 'rect') return
    const [x, y] = getSVGCoords(e)
    setIsDrawing(true)
    setDrawPoints([[x, y], [x, y]])
  }

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || (activeTool !== 'circle' && activeTool !== 'rect')) return
    const [x, y] = getSVGCoords(e)
    setDrawPoints((prev) => [prev[0], [x, y]])
  }

  const handleMouseUp = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDrawing || (activeTool !== 'circle' && activeTool !== 'rect')) return
    const [x, y] = getSVGCoords(e)
    const start = drawPoints[0] as [number, number]
    setIsDrawing(false)

    // Append to active disaster zones
    const newDisasterId = `disaster-${Date.now()}`
    const newDisasters: { id: string; type: 'circle' | 'rect' | 'lasso'; points: [number, number][] }[] = [
      ...disasters,
      { id: newDisasterId, type: activeTool as 'circle' | 'rect', points: [start, [x, y] as [number, number]] }
    ]
    setDisasters(newDisasters)
    applyDisastersToGraph(newDisasters, edges)
    setDrawPoints([])
  }

  // Double click or button trigger to finalize free-hand Lasso drawing
  const finalizeLasso = () => {
    if (drawPoints.length < 3) {
      setIsDrawing(false)
      setDrawPoints([])
      return
    }
    setIsDrawing(false)
    const newDisasterId = `disaster-${Date.now()}`
    const newDisasters = [...disasters, { id: newDisasterId, type: 'lasso' as const, points: [...drawPoints] }]
    setDisasters(newDisasters)
    applyDisastersToGraph(newDisasters, edges)
    setDrawPoints([])
  }

  // Apply all active disaster zones to disable intersected nodes/edges
  const applyDisastersToGraph = (
    activeZones: typeof disasters,
    currentEdges: LocalEdge[]
  ) => {
    const updatedEdges = currentEdges.map((edge) => {
      let isBlocked = false

      activeZones.forEach((zone) => {
        if (zone.type === 'rect') {
          const [[x1, y1], [x2, y2]] = zone.points
          const minX = Math.min(x1, x2)
          const maxX = Math.max(x1, x2)
          const minY = Math.min(y1, y2)
          const maxY = Math.max(y1, y2)
          // If edge midpoint is inside rectangle, block it
          const midX = (edge.x1 + edge.x2) / 2
          const midY = (edge.y1 + edge.y2) / 2
          if (midX >= minX && midX <= maxX && midY >= minY && midY <= maxY) {
            isBlocked = true
          }
        } else if (zone.type === 'circle') {
          const [[cx, cy], [px, py]] = zone.points
          const radius = getDistance(cx, cy, px, py)
          // If midpoint distance is less than radius, block it
          const midX = (edge.x1 + edge.x2) / 2
          const midY = (edge.y1 + edge.y2) / 2
          if (getDistance(cx, cy, midX, midY) <= radius) {
            isBlocked = true
          }
        } else if (zone.type === 'lasso') {
          const midX = (edge.x1 + edge.x2) / 2
          const midY = (edge.y1 + edge.y2) / 2
          if (isPointInPolygon(midX, midY, zone.points)) {
            isBlocked = true
          }
        }
      })

      return {
        ...edge,
        disabled: isBlocked,
      }
    })

    setEdges(updatedEdges)
  }

  // Toggle single edge blockage via Hammer tool
  const handleEdgeClick = (edgeId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (activeTool !== 'hammer') return

    setEdges((prev) =>
      prev.map((edge) =>
        edge.id === edgeId ? { ...edge, disabled: !edge.disabled } : edge
      )
    )
  }

  // Reset routing path, tool settings, and disaster deactivations
  const handleResetWorkspace = () => {
    setStartNode(null)
    setEndNode(null)
    setShortestPath(null)
    setDisasters([])
    setEdges((prev) => prev.map((e) => ({ ...e, disabled: false })))
    setActiveTool('none')
    setDrawPoints([])
    setIsDrawing(false)
  }

  // Compute analytics
  const totalLanes = edges.length
  const blockedLanes = edges.filter((e) => e.disabled).length
  const activeLanes = totalLanes - blockedLanes
  const majorRoads = edges.filter((e) => e.isMajor).length
  const minorRoads = totalLanes - majorRoads

  return (
    <div className="flex flex-col gap-10 w-full animate-fadeIn">
      {/* Title Header */}
      <div className="flex items-center justify-between border-b border-stone-border pb-6">
        <div className="flex flex-col gap-1.5">
          <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-cyan-edge">
            Stage 04 // Interactive Simulation Room
          </span>
          <h1 className="text-display leading-tight text-ink-black font-roobert font-normal">
            Topological Simulation Workbench
          </h1>
          <p className="text-[14px] text-warm-gray font-inter">
            Test road network resilience by calculating detour routing, blocking lanes manually, or drawing disaster areas.
          </p>
        </div>

        <button
          onClick={handleResetWorkspace}
          className="border border-stone-border hover:bg-stone-canvas text-ink-black rounded-full px-5 py-2.5 text-[12px] font-inter font-medium flex items-center gap-1.5 transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset Sandbox
        </button>
      </div>

      <div className="grid grid-cols-12 gap-8 w-full items-start">
        {/* Left Control Panel */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
          {/* Road Network Analytics */}
          <div className="bg-pure-white border border-stone-border rounded-xl p-6 shadow-subtle flex flex-col gap-5">
            <h2 className="text-[13px] font-mono uppercase tracking-wider text-ink-black flex items-center gap-2 border-b border-stone-border pb-3">
              <Activity className="w-4 h-4 text-cyan-signal" />
              Road Lane Analytics
            </h2>

            <div className="flex flex-col gap-3 text-[12px] font-inter text-warm-gray">
              <div className="flex justify-between border-b border-stone-border/40 pb-2">
                <span>Total Lanes (Edges)</span>
                <span className="font-semibold text-ink-black">{totalLanes}</span>
              </div>
              <div className="flex justify-between border-b border-stone-border/40 pb-2">
                <span>Major Highways (Blue)</span>
                <span className="font-semibold text-cyan-signal">{majorRoads}</span>
              </div>
              <div className="flex justify-between border-b border-stone-border/40 pb-2">
                <span>Minor Local Roads (Gray)</span>
                <span className="font-semibold text-orange-400">{minorRoads}</span>
              </div>
              <div className="flex justify-between border-b border-stone-border/40 pb-2">
                <span>Deactivated Lanes (Blocked)</span>
                <span className="font-semibold text-red-500 font-mono">{blockedLanes}</span>
              </div>
            </div>

            {/* Custom Ratio Visualizer Bar */}
            <div className="flex flex-col gap-1.5 mt-1">
              <span className="text-[11px] font-mono uppercase tracking-wider text-warm-gray">Network Operational Status</span>
              <div className="h-3 w-full bg-red-100 rounded-full overflow-hidden flex">
                <div
                  className="bg-emerald-500 h-full transition-all duration-300"
                  style={{ width: `${(activeLanes / totalLanes) * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-warm-gray mt-0.5">
                <span>{((activeLanes / totalLanes) * 100).toFixed(0)}% Active</span>
                <span>{((blockedLanes / totalLanes) * 100).toFixed(0)}% Disabled</span>
              </div>
            </div>
          </div>

          {/* Interactive Simulation Tools */}
          <div className="bg-pure-white border border-stone-border rounded-xl p-6 shadow-subtle flex flex-col gap-5">
            <h2 className="text-[13px] font-mono uppercase tracking-wider text-ink-black flex items-center gap-2 border-b border-stone-border pb-3">
              <Hammer className="w-4 h-4 text-cyan-signal" />
              Disruption Tool Room
            </h2>

            <div className="flex flex-col gap-3">
              {/* Path Routing mode toggle */}
              <button
                onClick={() => {
                  setActiveTool('none')
                  setDrawPoints([])
                  setIsDrawing(false)
                }}
                className={`w-full text-left p-3 rounded-lg border transition text-[12px] font-inter flex flex-col gap-0.5 cursor-pointer ${
                  activeTool === 'none'
                    ? 'border-cyan-signal bg-sky-wash/10 text-ink-black font-semibold'
                    : 'border-stone-border bg-pure-white hover:bg-stone-canvas/40 text-warm-gray'
                }`}
              >
                <span className="flex items-center gap-1.5 text-ink-black">
                  <Navigation className="w-4 h-4 text-cyan-signal" />
                  Routing Solver
                </span>
                <span className="text-[11px] text-warm-gray font-normal pl-5">
                  Click any two junctions to solve the shortest route detour.
                </span>
              </button>

              {/* Hammer tool */}
              <button
                onClick={() => {
                  setActiveTool('hammer')
                  setDrawPoints([])
                  setIsDrawing(false)
                }}
                className={`w-full text-left p-3 rounded-lg border transition text-[12px] font-inter flex flex-col gap-0.5 cursor-pointer ${
                  activeTool === 'hammer'
                    ? 'border-cyan-signal bg-sky-wash/10 text-ink-black font-semibold'
                    : 'border-stone-border bg-pure-white hover:bg-stone-canvas/40 text-warm-gray'
                }`}
              >
                <span className="flex items-center gap-1.5 text-ink-black">
                  <Hammer className="w-4 h-4 text-cyan-signal" />
                  Deactivate Hammer
                </span>
                <span className="text-[11px] text-warm-gray font-normal pl-5">
                  Click on individual road segments to block them.
                </span>
              </button>

              {/* Disaster Shapes buttons group */}
              <div className="flex flex-col gap-2 border-t border-stone-border/40 pt-4 mt-2">
                <span className="text-[11px] font-mono uppercase tracking-wider text-ink-black">Draw Disaster Shape</span>
                <div className="grid grid-cols-3 gap-2">
                  {(['circle', 'rect', 'lasso'] as const).map((shape) => (
                    <button
                      key={shape}
                      onClick={() => {
                        setActiveTool(shape)
                        setDrawPoints([])
                        setIsDrawing(false)
                      }}
                      className={`py-2 rounded-lg border text-[11px] font-inter capitalize transition cursor-pointer ${
                        activeTool === shape
                          ? 'border-cyan-signal bg-sky-wash/15 text-cyan-edge font-semibold'
                          : 'border-stone-border bg-pure-white hover:bg-stone-canvas/40 text-warm-gray'
                      }`}
                    >
                      {shape}
                    </button>
                  ))}
                </div>

                {activeTool === 'lasso' && isDrawing && (
                  <button
                    onClick={finalizeLasso}
                    className="w-full bg-cyan-signal hover:bg-cyan-edge text-pure-white py-2 rounded-lg text-[11px] font-inter font-semibold mt-2 flex items-center justify-center gap-1.5"
                  >
                    <PlusCircle className="w-4 h-4" />
                    Finalize & Close Lasso
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Interactive Canvas Map */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          <div className="bg-pure-white border border-stone-border rounded-2xl p-4 shadow-xl relative min-h-[500px] flex items-center justify-center overflow-hidden">
            {imageUrl ? (
              <div className="relative w-full max-w-[500px] aspect-square rounded-lg border border-stone-border/80 overflow-hidden shadow-subtle bg-soot">
                {/* 1. Satellite Base layer */}
                {(activeLayer === 'both' || activeLayer === 'satellite') && (
                  <img
                    src={imageUrl}
                    alt="Map base"
                    className={`absolute inset-0 w-full h-full object-cover select-none pointer-events-none ${
                      activeLayer === 'both' ? 'brightness-[0.55]' : 'brightness-100'
                    }`}
                  />
                )}

                {/* 2. Interactive SVG Canvas Overlay */}
                {(activeLayer === 'both' || activeLayer === 'graph') && graphData && (
                  <svg
                    ref={svgRef}
                    viewBox={`0 0 ${graphData.imgWidth} ${graphData.imgHeight}`}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onClick={handleMapClick}
                    className="absolute inset-0 w-full h-full cursor-crosshair select-none"
                  >
                    {/* Render active disaster zones */}
                    {disasters.map((zone) => {
                      if (zone.type === 'rect') {
                        const [[x1, y1], [x2, y2]] = zone.points
                        return (
                          <rect
                            key={zone.id}
                            x={Math.min(x1, x2)}
                            y={Math.min(y1, y2)}
                            width={Math.abs(x2 - x1)}
                            height={Math.abs(y2 - y1)}
                            fill="rgba(239, 68, 68, 0.25)"
                            stroke="#EF4444"
                            strokeWidth="2"
                            strokeDasharray="4 4"
                          />
                        )
                      }
                      if (zone.type === 'circle') {
                        const [[cx, cy], [px, py]] = zone.points
                        const radius = getDistance(cx, cy, px, py)
                        return (
                          <circle
                            key={zone.id}
                            cx={cx}
                            cy={cy}
                            r={radius}
                            fill="rgba(239, 68, 68, 0.25)"
                            stroke="#EF4444"
                            strokeWidth="2"
                            strokeDasharray="4 4"
                          />
                        )
                      }
                      if (zone.type === 'lasso') {
                        const pointsStr = zone.points.map((p) => p.join(',')).join(' ')
                        return (
                          <polygon
                            key={zone.id}
                            points={pointsStr}
                            fill="rgba(239, 68, 68, 0.25)"
                            stroke="#EF4444"
                            strokeWidth="2"
                            strokeDasharray="4 4"
                          />
                        )
                      }
                      return null
                    })}

                    {/* Render temporary drawing shape */}
                    {isDrawing && drawPoints.length > 0 && (
                      <>
                        {activeTool === 'rect' && drawPoints[1] && (
                          <rect
                            x={Math.min(drawPoints[0][0], drawPoints[1][0])}
                            y={Math.min(drawPoints[0][1], drawPoints[1][1])}
                            width={Math.abs(drawPoints[1][0] - drawPoints[0][0])}
                            height={Math.abs(drawPoints[1][1] - drawPoints[0][1])}
                            fill="rgba(14, 165, 233, 0.15)"
                            stroke="#0EA5E9"
                            strokeWidth="1.5"
                          />
                        )}
                        {activeTool === 'circle' && drawPoints[1] && (
                          <circle
                            cx={drawPoints[0][0]}
                            cy={drawPoints[0][1]}
                            r={getDistance(drawPoints[0][0], drawPoints[0][1], drawPoints[1][0], drawPoints[1][1])}
                            fill="rgba(14, 165, 233, 0.15)"
                            stroke="#0EA5E9"
                            strokeWidth="1.5"
                          />
                        )}
                        {activeTool === 'lasso' && (
                          <>
                            {drawPoints.map((p, idx) => (
                              <circle key={`p-${idx}`} cx={p[0]} cy={p[1]} r="4" fill="#0EA5E9" />
                            ))}
                            {drawPoints.length > 1 && (
                              <polyline
                                points={drawPoints.map((p) => p.join(',')).join(' ')}
                                fill="none"
                                stroke="#0EA5E9"
                                strokeWidth="2"
                              />
                            )}
                          </>
                        )}
                      </>
                    )}

                    {/* Render regular edges */}
                    {edges.map((edge) => {
                      const isHighlighted =
                        shortestPath &&
                        shortestPath.some((nodeId, idx) => {
                          if (idx === shortestPath.length - 1) return false
                          const nextId = shortestPath[idx + 1]
                          return (
                            (edge.u === nodeId && edge.v === nextId) ||
                            (edge.u === nextId && edge.v === nodeId)
                          )
                        })

                      return (
                        <line
                          key={edge.id}
                          x1={edge.x1}
                          y1={edge.y1}
                          x2={edge.x2}
                          y2={edge.y2}
                          onClick={(e) => handleEdgeClick(edge.id, e)}
                          className={`cursor-pointer transition-all ${
                            activeTool === 'hammer' ? 'hover:stroke-red-500 hover:stroke-[8px]' : ''
                          }`}
                          stroke={
                            edge.disabled
                              ? '#EF4444' // Blocked: Red
                              : isHighlighted
                              ? '#10B981' // Shortest path: Neon Emerald
                              : edge.isMajor
                              ? '#0EA5E9' // Major highway: Bright blue
                              : '#94A3B8' // Minor road: Gray Slate
                          }
                          strokeWidth={isHighlighted ? '7' : edge.isMajor ? '4' : '2'}
                          strokeDasharray={edge.disabled ? '3 3' : 'none'}
                          strokeLinecap="round"
                          opacity={edge.disabled ? '0.5' : '0.85'}
                        />
                      )
                    })}

                    {/* Render graph nodes */}
                    {nodes.map((node) => {
                      const isStart = startNode === node.id
                      const isEnd = endNode === node.id
                      const inPath = shortestPath && shortestPath.includes(node.id)

                      return (
                        <circle
                          key={`node-${node.id}`}
                          cx={node.x}
                          cy={node.y}
                          r={isStart || isEnd ? '10' : '6'}
                          className="cursor-pointer transition-all duration-150 hover:scale-125"
                          fill={
                            isStart
                              ? '#10B981' // Start: Emerald
                              : isEnd
                              ? '#EC4899' // End: Hot pink
                              : inPath
                              ? '#34D399' // Part of routing path: green
                              : '#ffffff' // Standard node: White
                          }
                          stroke={isStart || isEnd ? '#ffffff' : '#0F172A'}
                          strokeWidth={isStart || isEnd ? '2.5' : '1.5'}
                        />
                      )
                    })}
                  </svg>
                )}
              </div>
            ) : (
              <div className="text-[13px] font-inter text-warm-gray">No image selected. Please return to dashboard.</div>
            )}
          </div>

          {/* Map Layer HUD Controls */}
          <div className="flex items-center justify-between bg-pure-white border border-stone-border rounded-xl p-3 shadow-subtle">
            <div className="flex items-center gap-2 text-[12px] font-inter text-warm-gray">
              <Info className="w-4 h-4 text-cyan-signal" />
              <span>
                {activeTool === 'none' &&
                  (startNode === null
                    ? 'Click any junction (dot) to select routing START point.'
                    : endNode === null
                    ? 'Click another junction (dot) to select routing END point.'
                    : 'Shortest path found! Click any dot to solve a new path.')}
                {activeTool === 'hammer' && 'Click on any road line to block or unblock it.'}
                {(activeTool === 'rect' || activeTool === 'circle') &&
                  'Click and drag on the map to draw the disaster area.'}
                {activeTool === 'lasso' &&
                  'Click multiple points to draw free-hand boundary. Click "Finalize" to block roads inside.'}
              </span>
            </div>

            <div className="bg-stone-canvas border border-stone-border rounded-full p-1 flex gap-1">
              {[
                { id: 'both', label: 'Composite' },
                { id: 'satellite', label: 'Base Satellite' },
                { id: 'graph', label: 'Graph Topology' },
              ].map((layer) => (
                <button
                  key={layer.id}
                  onClick={() => setActiveLayer(layer.id as any)}
                  className={`px-3 py-1 rounded-full text-[11px] font-inter font-medium transition ${
                    activeLayer === layer.id ? 'bg-soot text-pure-white' : 'text-warm-gray hover:text-ink-black'
                  }`}
                >
                  {layer.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
