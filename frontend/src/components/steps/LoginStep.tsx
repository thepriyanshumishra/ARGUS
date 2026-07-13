import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { Shield, Key, AlertCircle, Loader2 } from 'lucide-react'
import LaserFlow from '../LaserFlow'

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    return window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
      ? 'http://localhost:8000'
      : window.location.origin;
  }
  return 'http://localhost:8000';
};

export const LoginStep: React.FC = () => {
  const navigate = useNavigate()
  const { setAuthToken } = useAppStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await fetch(`${getApiBaseUrl()}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: 'Authentication failed' }))
        throw new Error(errData.detail || 'Invalid username or password')
      }

      const data = await response.json()
      setAuthToken(data.token)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Server connection timed out. Verify your API server is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[85vh] flex items-center justify-center w-full px-4 relative">
      {/* Background Volumetric Laser Effect */}
      <div className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden opacity-40">
        <LaserFlow
          color="#06b6d4"
          fogIntensity={0.5}
          wispIntensity={3}
          flowSpeed={0.2}
          horizontalBeamOffset={-0.1}
          verticalBeamOffset={0.0}
          verticalSizing={2.0}
          horizontalSizing={1.0}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-stone-canvas via-transparent to-stone-canvas" />
      </div>

      <div className="bg-pure-white/40 backdrop-blur-xl border border-stone-border/50 rounded-2xl p-8 shadow-xl max-w-md w-full flex flex-col gap-6 animate-fadeIn z-10 relative">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="w-12 h-12 bg-sky-wash/20 text-cyan-signal rounded-xl flex items-center justify-center border border-stone-border/30">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-display leading-tight text-ink-black font-roobert font-normal mt-3">
            ARGUS Command Portal
          </h1>
          <p className="text-[13px] font-inter text-warm-gray max-w-[30ch]">
            Enter your credentials to access the satellite decision-support system.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 text-[12px] font-inter text-red-400 bg-red-950/20 border border-red-500/30 rounded-lg p-3 animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-ink-black">
              Username
            </label>
            <input
              type="text"
              required
              disabled={loading}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-stone-canvas/50 border border-stone-border rounded-lg px-3 py-2.5 text-[13px] font-inter text-ink-black focus:outline-none focus:border-cyan-signal/50 focus:bg-stone-canvas transition-all"
              placeholder="admin"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-ink-black">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-stone-canvas/50 border border-stone-border rounded-lg pl-9 pr-3 py-2.5 text-[13px] font-inter text-ink-black focus:outline-none focus:border-cyan-signal/50 focus:bg-stone-canvas transition-all"
                placeholder="••••••••"
              />
              <Key className="absolute left-3 top-3 w-4 h-4 text-warm-gray" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-cyan-signal hover:bg-cyan-edge text-stone-canvas hover:text-white text-[13px] font-inter font-semibold py-3.5 rounded-full flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-lg cursor-pointer focus:outline-none mt-2 disabled:bg-stone-muted disabled:text-warm-gray"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Securing connection...
              </>
            ) : (
              'Enter Workspace Portal'
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
