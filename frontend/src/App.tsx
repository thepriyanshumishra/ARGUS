import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomeStep } from './components/steps/HomeStep'
import { LoginStep } from './components/steps/LoginStep'
import { DashboardStep } from './components/steps/DashboardStep'
import { ExtractionStep } from './components/steps/ExtractionStep'
import { WorkspaceStep } from './components/steps/WorkspaceStep'
import { useAppStore } from './store/useAppStore'
import './App.css'

/** Guard: requires user authentication */
const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAppStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

/** Guard: requires a satellite image to be selected/uploaded */
const RequireImage: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { imageUrl } = useAppStore()
  if (!imageUrl) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

/** Guard: requires graph extraction to be complete */
const RequireGraph: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { graphData, imageUrl } = useAppStore()
  if (!imageUrl) return <Navigate to="/dashboard" replace />
  if (!graphData) return <Navigate to="/extraction" replace />
  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        {/* Public Landing */}
        <Route path="/" element={<HomeStep />} />

        {/* Security Login */}
        <Route path="/login" element={<LoginStep />} />

        {/* Protected Dashboard */}
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <DashboardStep />
            </RequireAuth>
          }
        />

        {/* Protected Stepper Extraction */}
        <Route
          path="/extraction"
          element={
            <RequireAuth>
              <RequireImage>
                <ExtractionStep />
              </RequireImage>
            </RequireAuth>
          }
        />

        {/* Protected Workspace Simulation */}
        <Route
          path="/workspace"
          element={
            <RequireAuth>
              <RequireGraph>
                <WorkspaceStep />
              </RequireGraph>
            </RequireAuth>
          }
        />

        {/* Fallback: redirect unknown paths to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
