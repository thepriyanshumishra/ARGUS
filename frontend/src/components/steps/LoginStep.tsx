import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { Shield, Key, AlertCircle, Loader2 } from 'lucide-react'

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
      const response = await fetch('http://localhost:8000/api/login', {
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
      setError(err.message || 'Server error. Please verify the Colab backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center w-full px-4">
      <div className="bg-pure-white border border-stone-border rounded-2xl p-8 shadow-lg max-w-md w-full flex flex-col gap-6 animate-fadeIn">
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="w-12 h-12 bg-sky-wash text-cyan-signal rounded-xl flex items-center justify-center border border-stone-border/50">
            <Shield className="w-6 h-6" />
          </div>
          <h1 className="text-display leading-tight text-ink-black font-roobert font-normal mt-2">
            ARGUS Security Gate
          </h1>
          <p className="text-[13px] font-inter text-warm-gray max-w-[30ch]">
            Enter your credentials to access the satellite decision-support system.
          </p>
        </div>

        {error && (
          <div className="flex items-start gap-2.5 text-[12px] font-inter text-red-600 bg-red-50 border border-red-200 rounded-lg p-3 animate-fadeIn">
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
              className="w-full bg-stone-canvas border border-stone-border rounded-lg px-3 py-2 text-[13px] font-inter text-ink-black focus:outline-none focus:border-cyan-signal transition-all"
              placeholder="e.g. admin"
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
                className="w-full bg-stone-canvas border border-stone-border rounded-lg pl-9 pr-3 py-2 text-[13px] font-inter text-ink-black focus:outline-none focus:border-cyan-signal transition-all"
                placeholder="••••••••"
              />
              <Key className="absolute left-3 top-2.5 w-4 h-4 text-warm-gray" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-cyan-signal hover:bg-cyan-edge text-pure-white text-[13px] font-inter font-semibold py-3 rounded-full flex items-center justify-center gap-2 transition-all active:scale-[0.98] shadow-subtle cursor-pointer focus:outline-none mt-2 disabled:bg-warm-gray"
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
