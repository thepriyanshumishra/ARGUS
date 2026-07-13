import React, { useRef, useEffect, useState } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useDashboardStore } from '../store'
import { OrbitControls } from '@react-three/drei'

export function GraphControls() {
  const { viewMode } = useDashboardStore()
  const { camera } = useThree()
  const controlsRef = useRef<any>(null)

  useFrame(() => {
    if (controlsRef.current) {
      controlsRef.current.enableRotate = true
      controlsRef.current.enableZoom = true
      controlsRef.current.enablePan = true
      controlsRef.current.enableDamping = true
      controlsRef.current.dampingFactor = 0.05
      controlsRef.current.rotateSpeed = 0.5
      controlsRef.current.zoomSpeed = 1.2
      controlsRef.current.panSpeed = 0.8
      controlsRef.current.minDistance = 10
      controlsRef.current.maxDistance = 1000
      controlsRef.current.minPolarAngle = 0
      controlsRef.current.maxPolarAngle = Math.PI
    }
  })

  const targetPositions: Record<string, THREE.Vector3> = {
    galaxy: new THREE.Vector3(0, 0, 200),
    force: new THREE.Vector3(0, 0, 150),
    hierarchy: new THREE.Vector3(0, 200, 200),
    layers: new THREE.Vector3(0, 0, 180),
    modules: new THREE.Vector3(0, 0, 180),
    tree: new THREE.Vector3(0, 150, 150),
    imports: new THREE.Vector3(0, 0, 180),
    classes: new THREE.Vector3(0, 0, 180),
    protocols: new THREE.Vector3(0, 0, 180),
    analytics: new THREE.Vector3(0, 0, 200),
  }

  useEffect(() => {
    if (!camera) return
    const targetPos = targetPositions[viewMode] || new THREE.Vector3(0, 0, 200)
    const startPos = camera.position.clone()
    const startTime = Date.now()
    const duration = 1500

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      camera.position.lerpVectors(startPos, targetPos, eased)
      camera.lookAt(0, 0, 0)
      if (progress < 1) requestAnimationFrame(animate)
    }
    animate()
  }, [viewMode])

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enableRotate={true}
      enableZoom={true}
      enablePan={true}
      enableDamping={true}
      dampingFactor={0.05}
      rotateSpeed={0.5}
      zoomSpeed={1.2}
      panSpeed={0.8}
      minDistance={10}
      maxDistance={1000}
      minPolarAngle={0}
      maxPolarAngle={Math.PI}
    />
  )
}
