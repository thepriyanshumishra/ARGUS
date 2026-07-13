import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../store/useAppStore'
import { ShieldAlert, Cpu, Network, ArrowRight } from 'lucide-react'
import LaserFlow from '../LaserFlow'

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
    <div className="w-full flex flex-col gap-24 py-16 relative">
      {/* Background Volumetric Laser Effect */}
      <div className="absolute inset-0 -top-20 h-[650px] w-full pointer-events-none z-0 overflow-hidden opacity-50">
        <LaserFlow
          color="#06b6d4"
          fogIntensity={0.6}
          wispIntensity={4}
          flowSpeed={0.25}
          horizontalBeamOffset={0.0}
          verticalBeamOffset={-0.2}
          verticalSizing={2.5}
          horizontalSizing={1.5}
        />
        {/* Dark vignette to blend with canvas background */}
        <div className="absolute inset-0 bg-gradient-to-t from-stone-canvas via-transparent to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-stone-canvas via-transparent to-stone-canvas" />
      </div>

      {/* Hero Section */}
      <div className="flex flex-col items-center text-center gap-8 max-w-4xl mx-auto z-10 relative">
        <div className="bg-sky-wash border border-stone-border/40 text-cyan-signal text-[11px] font-mono px-4 py-1.5 rounded-full uppercase tracking-[0.2em] shadow-sm backdrop-blur-md">
          Decision Support System v0.3.0
        </div>
        <h1 className="text-[56px] md:text-[68px] leading-[1.05] tracking-tight font-roobert font-normal text-ink-black max-w-[20ch]">
          Automated Road Extraction & Criticality Analysis
        </h1>
        <p className="text-[16px] leading-relaxed text-warm-gray font-inter max-w-[55ch] opacity-90">
          ARGUS leverages SpaceNet 5 deep neural networks and topology search engines to extract high-resolution centerline graphs from satellite imagery. Simulate disasters, optimize rescue routes, and identify vulnerable bottlenecks instantly.
        </p>
        <button
          onClick={handleGetStarted}
          className="bg-cyan-signal hover:bg-cyan-edge text-stone-canvas hover:text-white px-8 py-4 rounded-full font-inter font-semibold text-[14px] flex items-center gap-2.5 transition-all active:scale-[0.98] shadow-lg hover:shadow-cyan-signal/20 cursor-pointer focus:outline-none mt-4"
        >
          Access Command Console
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Bento Showcase Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 z-10 relative">
        {/* Card 1: AI Extractor */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[240px] hover:border-cyan-signal/30 hover:shadow-md transition-all duration-300 group">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal transition-colors group-hover:bg-cyan-signal/15">
            <Cpu className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2 mt-6">
            <h3 className="text-[16px] font-inter font-semibold text-ink-black">
              SpaceNet 5 Inference
            </h3>
            <p className="text-[13px] text-warm-gray font-inter leading-relaxed">
              Native 256x256 crop tiling, binned speed classification, and customized ResNet-34 U-Nets tuned for urban densities.
            </p>
          </div>
        </div>

        {/* Card 2: Topology Generator */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[240px] hover:border-cyan-signal/30 hover:shadow-md transition-all duration-300 group">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal transition-colors group-hover:bg-cyan-signal/15">
            <Network className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2 mt-6">
            <h3 className="text-[16px] font-inter font-semibold text-ink-black">
              Vector Centerlines
            </h3>
            <p className="text-[13px] text-warm-gray font-inter leading-relaxed">
              Thinning algorithms convert pixel probability masks into NetworkX mathematical structures with exact spatial coordinates.
            </p>
          </div>
        </div>

        {/* Card 3: Disaster Simulations */}
        <div className="bg-pure-white border border-stone-border rounded-xl p-8 flex flex-col justify-between min-h-[240px] hover:border-cyan-signal/30 hover:shadow-md transition-all duration-300 group">
          <div className="w-10 h-10 rounded-lg bg-stone-canvas flex items-center justify-center border border-stone-border/40 text-cyan-signal transition-colors group-hover:bg-cyan-signal/15">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-2 mt-6">
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
      <div className="border-t border-stone-border/40 pt-8 flex items-center justify-between text-[11px] font-mono text-warm-gray uppercase tracking-wider z-10 relative">
        <span>© 2026 ARGUS Intelligence</span>
        <div className="flex gap-6">
          <span>Security Certified</span>
          <span>GPU Accelerated</span>
        </div>
      </div>
    </div>
  )
}
