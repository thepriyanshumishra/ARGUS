import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { ShieldAlert, Cpu, Network, ArrowRight } from 'lucide-react'

export const HomeStep: React.FC = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAppStore()

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard')
    } else {
      navigate('/login')
    }
  }

  return (
    <div className="w-full flex flex-col gap-20 py-8 animate-fadeIn">
      {/* Hero Section */}
      <div className="flex flex-col items-center text-center gap-6 max-w-3xl mx-auto">
        <div className="bg-sky-wash border border-stone-border/60 text-cyan-signal text-[11px] font-mono px-3 py-1 rounded-full uppercase tracking-wider">
          Decision Support System v0.3.0
        </div>
        <h1 className="text-[52px] leading-[1.1] tracking-tight font-roobert font-normal text-ink-black">
          Automated Road Extraction & Criticality Analysis
        </h1>
        <p className="text-[16px] leading-relaxed text-warm-gray font-inter max-w-[55ch]">
          ARGUS leverages SpaceNet 5 deep neural networks and topology search engines to extract high-resolution centerline graphs from satellite imagery. Simulate disasters, optimize rescue routes, and identify vulnerable bottlenecks instantly.
        </p>
        <button
          onClick={handleGetStarted}
          className="bg-cyan-signal hover:bg-cyan-edge text-pure-white px-8 py-4 rounded-full font-inter font-semibold text-[14px] flex items-center gap-2 transition-all active:scale-[0.98] shadow-subtle cursor-pointer focus:outline-none mt-4"
        >
          Access Command Console
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Bento Showcase Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {/* Card 1: AI Extractor */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[220px] hover:shadow-subtle transition-all duration-300">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal">
            <Cpu className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[16px] font-inter font-semibold text-ink-black">
              SpaceNet 5 Inference
            </h3>
            <p className="text-[13px] text-warm-gray font-inter leading-relaxed">
              Native 256x256 crop tiling, binned speed classification, and customized ResNet-34 U-Nets tuned for urban densities.
            </p>
          </div>
        </div>

        {/* Card 2: Topology Generator */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[220px] hover:shadow-subtle transition-all duration-300">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal">
            <Network className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[16px] font-inter font-semibold text-ink-black">
              Vector Centerlines
            </h3>
            <p className="text-[13px] text-warm-gray font-inter leading-relaxed">
              Thinning algorithms convert pixel probability masks into NetworkX mathematical structures with exact spatial coordinates.
            </p>
          </div>
        </div>

        {/* Card 3: Disaster Simulations */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[220px] hover:shadow-subtle transition-all duration-300">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2">
            <h3 className="text-[16px] font-inter font-semibold text-ink-black">
              Resilience Simulation
            </h3>
            <p className="text-[13px] text-warm-gray font-inter leading-relaxed">
              Block coordinates, trigger flood lasso selections, and calculate alternative routing paths in real-time.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-stone-border pt-8 flex items-center justify-between text-[11px] font-mono text-warm-gray uppercase tracking-wider">
        <span>© 2026 ARGUS Intelligence</span>
        <div className="flex gap-4">
          <span>Security Certified</span>
          <span>GPU Accelerated</span>
        </div>
      </div>
    </div>
  )
}
