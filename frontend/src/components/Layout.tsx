import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Navbar } from './Navbar'
import { Sparkles, Globe, FileText, Shield } from 'lucide-react'
import TargetCursor from './TargetCursor'

interface LayoutProps {
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const isHome = pathname === '/'

  return (
    <div className="min-h-screen bg-stone-canvas flex flex-col font-inter selection:bg-sky-wash relative overflow-hidden">
      <TargetCursor
        cursorColor="#06b6d4"
        cursorColorOnTarget="#10b981"
        targetSelector=".cursor-target, button, a, select, input, [role='button']"
      />
      {/* Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <main className={`flex-1 w-full mx-auto px-8 transition-all duration-300 flex flex-col ${
        isHome
          ? 'max-w-[1400px] py-16 gap-20'
          : 'max-w-[1200px] py-12 gap-12'
      }`}>
        {children}
      </main>

      {/* Conditional Footer: Full Bento/Editorial for Home page OR Minimal for Steps */}
      {isHome ? (
        <footer className="w-full bg-stone-canvas border-t border-stone-border mt-auto pt-16 pb-12 select-none">
          <div className="max-w-[1400px] mx-auto px-8 grid grid-cols-1 md:grid-cols-12 gap-10">
            {/* Logo and Wordmark Column */}
            <div className="md:col-span-5 flex flex-col gap-4">
              <div
                className="flex items-center gap-2.5 cursor-pointer group w-fit"
                onClick={() => navigate('/')}
              >
                <div className="w-7 h-7 rounded bg-pure-white border border-stone-border flex items-center justify-center text-ink-black transition-colors duration-150 group-hover:bg-cyan-signal/20 group-hover:text-cyan-signal">
                  <Sparkles className="w-4 h-4" />
                </div>
                <span className="font-roobert font-semibold text-[15px] text-ink-black tracking-tight">
                  ARGUS
                </span>
              </div>
              <p className="text-[12px] leading-relaxed text-warm-gray font-inter max-w-[34ch]">
                Developing topological resilience networks from spatial satellite imagery to empower urban planners and disaster response coordination.
              </p>
              <span className="text-[11px] text-ash-gray font-mono uppercase tracking-wider mt-4">
                Bharatiya Antariksh Hackathon 2026
              </span>
            </div>

            {/* Quick Navigation Links */}
            <div className="md:col-span-3 flex flex-col gap-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-black font-semibold">Workspace</span>
              <ul className="flex flex-col gap-2 text-[12px] font-inter text-warm-gray">
                <li>
                  <button onClick={() => navigate('/dashboard')} className="hover:text-ink-black transition-colors duration-150 cursor-pointer">
                    1. Raster Ingestion
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/dashboard')} className="hover:text-ink-black transition-colors duration-150 cursor-pointer">
                    2. Graph Extraction
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/dashboard')} className="hover:text-ink-black transition-colors duration-150 cursor-pointer">
                    3. Network Simulation
                  </button>
                </li>
              </ul>
            </div>

            {/* Research and Docs */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-black font-semibold">Resources</span>
              <ul className="flex flex-col gap-2 text-[12px] font-inter text-warm-gray">
                <li className="flex items-center gap-1.5 hover:text-ink-black transition-colors duration-150 cursor-pointer">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Documentation</span>
                </li>
                <li className="flex items-center gap-1.5 hover:text-ink-black transition-colors duration-150 cursor-pointer">
                  <Shield className="w-3.5 h-3.5" />
                  <span>Architecture</span>
                </li>
                <li className="flex items-center gap-1.5 hover:text-ink-black transition-colors duration-150 cursor-pointer">
                  <Globe className="w-3.5 h-3.5" />
                  <span>GitHub Repository</span>
                </li>
              </ul>
            </div>

            {/* Ecosystem Links */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <span className="text-[10px] font-mono uppercase tracking-wider text-ink-black font-semibold">Sponsors</span>
              <ul className="flex flex-col gap-2 text-[12px] font-inter text-warm-gray">
                <li className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5" />
                  <span>ISRO / Space Apps</span>
                </li>
                <li>
                  <span>Government of India</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="max-w-[1400px] mx-auto px-8 border-t border-stone-border mt-12 pt-8 flex items-center justify-between text-[11px] text-ash-gray font-inter">
            <span>© {new Date().getFullYear()} ARGUS. All rights reserved. Open-source under MIT.</span>
            <span>Platform v1.0.0-beta</span>
          </div>
        </footer>
      ) : (
        <footer className="w-full max-w-[1200px] mx-auto px-8 py-8 border-t border-stone-border flex items-center justify-between text-[11px] text-ash-gray font-inter select-none">
          <span>© {new Date().getFullYear()} ARGUS. Adaptive Resilience Graph for Urban Systems.</span>
          <span>Bharatiya Antariksh Hackathon 2026</span>
        </footer>
      )}
    </div>
  )
}
