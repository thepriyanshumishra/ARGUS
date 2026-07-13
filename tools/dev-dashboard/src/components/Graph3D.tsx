import React, { useMemo, useRef, useEffect, useState } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useDashboardStore } from '../store'
import { NODE_TYPE_COLORS, MODULE_COLORS, LAYER_COLORS, EDGE_TYPE_COLORS } from '../types/graph'
import { cn } from '../utils/cn'

interface GraphNodesProps {
  nodes: any[]
  colorScheme: string
  selectedNodeId: string | null
  hoveredNodeId: string | null
  pinnedNodes: string[]
  onNodeClick: (id: string | null) => void
  onNodeHover: (id: string | null) => void
}

export function GraphNodes({ 
  nodes, 
  colorScheme, 
  selectedNodeId, 
  hoveredNodeId,
  pinnedNodes,
  onNodeClick,
  onNodeHover
}: GraphNodesProps) {
  const pointsRef = useRef<THREE.Points | null>(null)
  const geometryRef = useRef<THREE.BufferGeometry | null>(null)
  const materialRef = useRef<THREE.PointsMaterial | null>(null)
  const { camera } = useThree()

  // Initialize geometry and material
  useEffect(() => {
    if (!nodes || nodes.length === 0) return

    const geometry = new THREE.BufferGeometry()
    const count = nodes.length
    
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    const nodeIds = new Float32Array(count)
    const alphas = new Float32Array(count)
    
    nodes.forEach((node, i) => {
      const pos = node.position || { x: 0, y: 0, z: 0 }
      positions[i * 3] = pos.x
      positions[i * 3 + 1] = pos.y
      positions[i * 3 + 2] = pos.z
      
      let color = new THREE.Color(0x888888)
      if (colorScheme === 'type') {
        color.set(NODE_TYPE_COLORS[node.type] || '#888888')
      } else if (colorScheme === 'module') {
        color.set(MODULE_COLORS[node.module] || '#888888')
      } else if (colorScheme === 'layer') {
        color.set(LAYER_COLORS[node.layer] || '#888888')
      }
      
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
      
      const connections = (node.inDegree || 0) + (node.outDegree || 0)
      sizes[i] = Math.max(3, Math.min(12, 3 + connections * 0.8))
      
      nodeIds[i] = i
      alphas[i] = 1.0
    })
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    geometry.setAttribute('nodeId', new THREE.BufferAttribute(nodeIds, 1))
    geometry.setAttribute('alpha', new THREE.BufferAttribute(alphas, 1))
    
    geometryRef.current = geometry
    
    const material = new THREE.PointsMaterial({
      size: 1,
      vertexColors: true,
      transparent: true,
      opacity: 1,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
    
    materialRef.current = material
    
    const points = new THREE.Points(geometry, material)
    pointsRef.current = points
    
    return () => {
      geometry.dispose()
      material.dispose()
    }
  }, [nodes.length])

  // Update positions when nodes change
  useEffect(() => {
    if (!nodes || nodes.length === 0 || !geometryRef.current) return
    
    const geometry = geometryRef.current
    const positions = geometry.getAttribute('position').array as Float32Array
    const colors = geometry.getAttribute('color').array as Float32Array
    const sizes = geometry.getAttribute('size').array as Float32Array
    const alphas = geometry.getAttribute('alpha').array as Float32Array
    
    nodes.forEach((node, i) => {
      const pos = node.position || { x: 0, y: 0, z: 0 }
      positions[i * 3] = pos.x
      positions[i * 3 + 1] = pos.y
      positions[i * 3 + 2] = pos.z
      
      let color = new THREE.Color(0x888888)
      if (colorScheme === 'type') {
        color.set(NODE_TYPE_COLORS[node.type] || '#888888')
      } else if (colorScheme === 'module') {
        color.set(MODULE_COLORS[node.module] || '#888888')
      } else if (colorScheme === 'layer') {
        color.set(LAYER_COLORS[node.layer] || '#888888')
      }
      
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
      
      const connections = (node.inDegree || 0) + (node.outDegree || 0)
      sizes[i] = Math.max(3, Math.min(12, 3 + connections * 0.8))
      
      // Highlight selected/hovered/pinned
      const isSelected = node.id === selectedNodeId
      const isHovered = node.id === hoveredNodeId
      const isPinned = pinnedNodes.includes(node.id)
      
      if (isSelected) {
        alphas[i] = 1.0
        sizes[i] = Math.max(sizes[i], 14)
      } else if (isHovered) {
        alphas[i] = 1.0
        sizes[i] = Math.max(sizes[i], 10)
      } else if (isPinned) {
        alphas[i] = 1.0
        sizes[i] = Math.max(sizes[i], 8)
      } else {
        alphas[i] = 0.85
      }
    })
    
    geometry.getAttribute('position').needsUpdate = true
    geometry.getAttribute('color').needsUpdate = true
    geometry.getAttribute('size').needsUpdate = true
    geometry.getAttribute('alpha').needsUpdate = true
  }, [nodes, colorScheme, selectedNodeId, hoveredNodeId, pinnedNodes])

  // Subtle animation
  useFrame(() => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += 0.00008
    }
  })

  if (!nodes || nodes.length === 0) return null

  return (
    <points ref={pointsRef} />
  )
}

interface GraphEdgesProps {
  nodes: any[]
  edges: any[]
  selectedNodeId: string | null
  hoveredNodeId: string | null
}

export function GraphEdges({ nodes, edges, selectedNodeId, hoveredNodeId }: GraphEdgesProps) {
  const lineRef = useRef<THREE.LineSegments | null>(null)
  const geometryRef = useRef<THREE.BufferGeometry | null>(null)
  const materialRef = useRef<THREE.LineBasicMaterial | null>(null)

  const nodeMap = useMemo(() => {
    const map = new Map()
    nodes.forEach((node, i) => {
      map.set(node.id, { index: i, position: node.position || { x: 0, y: 0, z: 0 } })
    })
    return map
  }, [nodes])

  useEffect(() => {
    if (!edges || edges.length === 0) return

    // We need to rebuild geometry when edges or node positions change
    const rebuildGeometry = () => {
      if (!geometryRef.current) return
      
      const geometry = geometryRef.current
      const positions = geometry.getAttribute('position').array as Float32Array
      const colors = geometry.getAttribute('color').array as Float32Array
      
      edges.forEach((edge, i) => {
        const source = nodeMap.get(edge.source)
        const target = nodeMap.get(edge.target)
        
        if (!source || !target) return
        
        const srcPos = source.position
        const tgtPos = target.position
        
        // Source to target
        positions[i * 6] = srcPos.x
        positions[i * 6 + 1] = srcPos.y
        positions[i * 6 + 2] = srcPos.z
        positions[i * 6 + 3] = tgtPos.x
        positions[i * 6 + 4] = tgtPos.y
        positions[i * 6 + 5] = tgtPos.z
        
        // Color based on edge type
        const edgeColor = EDGE_TYPE_COLORS[edge.type] || '#444444'
        const color = new THREE.Color(edgeColor)
        
        // Highlight edges connected to selected/hovered node
        const isHighlighted = edge.source === selectedNodeId || edge.target === selectedNodeId ||
                              edge.source === hoveredNodeId || edge.target === hoveredNodeId
        
        const alpha = isHighlighted ? 0.8 : 0.15
        
        colors[i * 6] = color.r * alpha
        colors[i * 6 + 1] = color.g * alpha
        colors[i * 6 + 2] = color.b * alpha
        colors[i * 6 + 3] = color.r * alpha
        colors[i * 6 + 4] = color.g * alpha
        colors[i * 6 + 5] = color.b * alpha
      })
      
      geometry.getAttribute('position').needsUpdate = true
      geometry.getAttribute('color').needsUpdate = true
    }

    // Initial build
    if (!geometryRef.current) {
      const geometry = new THREE.BufferGeometry()
      const count = edges.length
      const positions = new Float32Array(count * 6)
      const colors = new Float32Array(count * 6)
      
      edges.forEach((edge, i) => {
        const source = nodeMap.get(edge.source)
        const target = nodeMap.get(edge.target)
        
        if (!source || !target) return
        
        const srcPos = source.position
        const tgtPos = target.position
        
        positions[i * 6] = srcPos.x
        positions[i * 6 + 1] = srcPos.y
        positions[i * 6 + 2] = srcPos.z
        positions[i * 6 + 3] = tgtPos.x
        positions[i * 6 + 4] = tgtPos.y
        positions[i * 6 + 5] = tgtPos.z
        
        const edgeColor = EDGE_TYPE_COLORS[edge.type] || '#444444'
        const color = new THREE.Color(edgeColor)
        const alpha = 0.15
        
        colors[i * 6] = color.r * alpha
        colors[i * 6 + 1] = color.g * alpha
        colors[i * 6 + 2] = color.b * alpha
        colors[i * 6 + 3] = color.r * alpha
        colors[i * 6 + 4] = color.g * alpha
        colors[i * 6 + 5] = color.b * alpha
      })
      
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
      
      geometryRef.current = geometry
      
      const material = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 1,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        linewidth: 1,
      })
      
      materialRef.current = material
      
      const lines = new THREE.LineSegments(geometry, material)
      lineRef.current = lines
      
      return () => {
        geometry.dispose()
        material.dispose()
      }
    }
    
    rebuildGeometry()
    
    // Update on selection/hover changes
    const interval = setInterval(rebuildGeometry, 100)
    return () => clearInterval(interval)
  }, [edges, nodes, selectedNodeId, hoveredNodeId])

  // Rebuild when node positions change
  useFrame(() => {
    if (geometryRef.current && materialRef.current) {
      // Positions are updated via the effect above
    }
  })

  if (!edges || edges.length === 0) return null

  return (
    <lineSegments ref={lineRef} />
  )
}

export function GraphBackground() {
  return (
    <>
      <Stars count={1500} />
      <CentralGlow />
    </>
  )
}

function Stars({ count = 1500 }: { count: number }) {
  const geometryRef = useRef<THREE.BufferGeometry | null>(null)
  const materialRef = useRef<THREE.PointsMaterial | null>(null)
  const pointsRef = useRef<THREE.Points | null>(null)

  useEffect(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)

    for (let i = 0; i < count; i++) {
      const radius = 400 + Math.random() * 400
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = radius * Math.cos(phi)
      
      const hue = 0.55 + Math.random() * 0.15 // Blue-cyan range
      const color = new THREE.Color().setHSL(hue, 0.4, 0.5 + Math.random() * 0.3)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
      
      sizes[i] = Math.random() * 0.6 + 0.3
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    geometryRef.current = geometry

    const material = new THREE.PointsMaterial({
      size: 1,
      vertexColors: true,
      transparent: true,
      opacity: 0.5,
      sizeAttenuation: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    })
    materialRef.current = material

    const points = new THREE.Points(geometry, material)
    pointsRef.current = points

    return () => {
      geometry.dispose()
      material.dispose()
    }
  }, [])

  useFrame(() => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y += 0.000015
      pointsRef.current.rotation.x += 0.000005
    }
  })

  return <points ref={pointsRef} />
}

function CentralGlow() {
  const materialRef = useRef<THREE.MeshBasicMaterial | null>(null)
  const meshRef = useRef<THREE.Mesh | null>(null)

  useEffect(() => {
    const geometry = new THREE.SphereGeometry(60, 32, 32)
    const material = new THREE.MeshBasicMaterial({
      color: 0x0ea5e9,
      transparent: true,
      opacity: 0.04,
      side: THREE.BackSide,
      depthWrite: false,
    })
    materialRef.current = material

    const mesh = new THREE.Mesh(geometry, material)
    meshRef.current = mesh

    return () => {
      geometry.dispose()
      material.dispose()
    }
  }, [])

  useFrame(({ clock }) => {
    if (meshRef.current) {
      const scale = 1 + Math.sin(clock.getElapsedTime() * 0.4) * 0.08
      meshRef.current.scale.setScalar(scale)
    }
  })

  return <mesh ref={meshRef} />
}

export function GraphControls() {
  const { controls, camera } = useThree()

  useEffect(() => {
    if (controls) {
      controls.enableDamping = true
      controls.dampingFactor = 0.05
      controls.enablePan = true
      controls.enableZoom = true
      controls.enableRotate = true
      controls.autoRotate = true
      controls.autoRotateSpeed = 0.15
      controls.minDistance = 20
      controls.maxDistance = 600
      controls.minPolarAngle = 0
      controls.maxPolarAngle = Math.PI
    }
  }, [controls])

  return null
}

export function GraphRaycaster() {
  const { camera, scene, gl } = useThree()
  const { filteredNodes, setSelectedNode, setHoveredNode, pinnedNodes } = useDashboardStore()
  const raycasterRef = useRef(new THREE.Raycaster())
  const mouseRef = useRef(new THREE.Vector2())

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const rect = gl.domElement.getBoundingClientRect()
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

      raycasterRef.current.setFromCamera(mouseRef.current, camera)
      
      // Find intersecting nodes
      const nodeObjects = scene.children.filter(child => 
        child.isPoints && child.geometry?.attributes?.nodeId
      )
      
      const intersects = raycasterRef.current.intersectObjects(nodeObjects)
      
      if (intersects.length > 0) {
        const intersect = intersects[0]
        const nodeIdAttr = intersect.object.geometry.attributes.nodeId
        const nodeIndex = nodeIdAttr.getX(intersect.index)
        const node = filteredNodes[nodeIndex]
        if (node) {
          setSelectedNode(node.id)
        }
      } else {
        setSelectedNode(null)
      }
    }

    const handleMove = (event: MouseEvent) => {
      const rect = gl.domElement.getBoundingClientRect()
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

      raycasterRef.current.setFromCamera(mouseRef.current, camera)
      
      const nodeObjects = scene.children.filter(child => 
        child.isPoints && child.geometry?.attributes?.nodeId
      )
      
      const intersects = raycasterRef.current.intersectObjects(nodeObjects)
      
      if (intersects.length > 0) {
        const intersect = intersects[0]
        const nodeIdAttr = intersect.object.geometry.attributes.nodeId
        const nodeIndex = nodeIdAttr.getX(intersect.index)
        const node = filteredNodes[nodeIndex]
        if (node) {
          setHoveredNode(node.id)
          gl.domElement.style.cursor = 'pointer'
        }
      } else {
        setHoveredNode(null)
        gl.domElement.style.cursor = 'grab'
      }
    }

    gl.domElement.addEventListener('click', handleClick)
    gl.domElement.addEventListener('mousemove', handleMove)
    gl.domElement.addEventListener('mouseleave', () => {
      setHoveredNode(null)
      gl.domElement.style.cursor = 'grab'
    })

    return () => {
      gl.domElement.removeEventListener('click', handleClick)
      gl.domElement.removeEventListener('mousemove', handleMove)
    }
  }, [camera, scene, gl, filteredNodes, setSelectedNode, setHoveredNode])

  return null
}

export default function Graph3D() {
  return null // Helper components only
}