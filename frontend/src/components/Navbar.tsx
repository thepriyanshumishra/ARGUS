import React, { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAppStore } from '../store/useAppStore'
import { Sparkles, AlertCircle, RefreshCw } from 'lucide-react'

const STEPS = [
  { path: '/dashboard', label: '1. Dashboard' },
  { path: '/extraction', label: '2. Extraction' },
  { path: '/workspace', label: '3. Workspace' },
]

export const Navbar: React.FC = () => {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { connectionStatus, checkBackendHealth, logout, isAuthenticated } = useAppStore()

  const isWorkflow = ['/dashboard', '/extraction', '/workspace'].includes(pathname)

  useEffect(() => {
    checkBackendHealth()
    const interval = setInterval(checkBackendHealth, 10000)
    return () => clearInterval(interval)
  }, [checkBackendHealth])

  const handleReset = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="sticky top-0 z-50 bg-stone-canvas/80 backdrop-blur-md border-b border-stone-border px-12 h-20 flex items-center justify-between select-none">
      {/* Left: Brand Logo Wordmark */}
      <div
        className="flex items-center gap-2.5 cursor-pointer group"
        onClick={() => navigate('/')}
      >
        <div className="w-7 h-7 rounded bg-pure-white border border-stone-border flex items-center justify-center text-ink-black transition-all duration-150 group-hover:bg-cyan-signal/20 group-hover:text-cyan-signal group-hover:border-cyan-signal/40">
          <Sparkles className="w-4 h-4" strokeWidth={2.5} />
        </div>
        <span className="font-roobert font-semibold text-[16px] text-ink-black tracking-tight">
          ARGUS
        </span>
      </div>

      {/* Center: Tabs group - only on active workflow steps */}
      {isWorkflow && isAuthenticated ? (
        <div className="bg-pure-white border border-stone-border rounded-full p-1 flex items-center gap-1 shadow-sm">
          {STEPS.map((step) => {
            const isActive = pathname === step.path
            return (
              <button
                key={step.path}
                onClick={() => navigate(step.path)}
                className={`px-5 py-2 rounded-full text-[13px] font-inter font-medium leading-none transition-all duration-150 focus:outline-none focus:ring-0 select-none ${
                  isActive
                    ? 'bg-stone-canvas text-cyan-signal border border-stone-border shadow-inner'
                    : 'text-warm-gray hover:text-ink-black bg-transparent'
                }`}
              >
                {step.label}
              </button>
            )
          })}
        </div>
      ) : (
        <div className="hidden md:flex items-center gap-2 text-[12px] font-inter text-warm-gray">
          <div className="w-1.5 h-1.5 rounded-full bg-cyan-signal/60" />
          <span>Bharatiya Antariksh Hackathon 2026 // Platform</span>
        </div>
      )}

      {/* Right: API Status & Reset */}
      <div className="flex items-center gap-5">
        {/* Connection status indicator */}
        <div className="flex items-center">
          {connectionStatus === 'connected' && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 text-[11px] font-mono font-medium">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>API Live</span>
            </div>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 text-[11px] font-mono font-medium animate-pulse">
              <AlertCircle className="w-3.5 h-3.5" />
              <span>Offline</span>
            </div>
          )}
          {connectionStatus === 'checking' && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-stone-canvas border border-stone-border text-ash-gray text-[11px] font-mono font-medium">
              <RefreshCw className="w-3 h-3 animate-spin" />
              <span>Checking</span>
            </div>
          )}
        </div>

        {isAuthenticated && (
          <button
            onClick={handleReset}
            className="h-9 px-4 border border-stone-border rounded-full text-[13px] font-inter font-medium text-ink-black hover:bg-stone-muted hover:border-warm-gray active:scale-[0.98] transition-all duration-150 focus:outline-none focus:ring-0 cursor-pointer"
          >
            Reset Session
          </button>
        )}
      </div>
    </nav>
  )
}
