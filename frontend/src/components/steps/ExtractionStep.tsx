import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../../store/useAppStore";
import {
  Grid,
  Layers,
  Activity,
  Network,
  ArrowRight,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

const getApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    return window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
      ? "http://localhost:8000"
      : window.location.origin;
  }
  return "http://localhost:8000";
};

export const ExtractionStep: React.FC = () => {
  const navigate = useNavigate();
  const {
    imageUrl,
    selectedImage,
    imageName,
    imageSize,
    graphData,
    maskB64,
    skeletonB64,
    setGraphData,
    setMaskB64,
    setSkeletonB64,
    resetStore,
  } = useAppStore();

  const [activeStep, setActiveStep] = useState<1 | 2 | 3 | 4>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // On mount, start extraction from backend if not already loaded
  useEffect(() => {
    if (graphData && maskB64 && skeletonB64) return; // Already loaded

    const triggerExtraction = async () => {
      setLoading(true);
      setError(null);
      try {
        const formData = new FormData();
        if (selectedImage) {
          formData.append("file", selectedImage);
        } else if (imageUrl) {
          const res = await fetch(imageUrl);
          const blob = await res.blob();
          const file = new File([blob], imageName || "city_map.png", { type: blob.type });
          formData.append("file", file);
        } else {
          throw new Error("No image loaded in workspace.");
        }

        const response = await fetch(`${getApiBaseUrl()}/api/extract-graph?method=classical`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Extraction pipeline failed. Please check server logs.");
        }

        const data = await response.json();
        setGraphData({
          nodes: data.nodes,
          edges: data.edges,
          imgWidth: data.imgWidth,
          imgHeight: data.imgHeight,
          nodeCount: data.nodeCount,
          edgeCount: data.edgeCount,
        });
        setMaskB64(data.maskB64);
        setSkeletonB64(data.skeletonB64);
      } catch (err: any) {
        setError(err.message || "An error occurred during extraction.");
      } finally {
        setLoading(false);
      }
    };

    triggerExtraction();
  }, [selectedImage, imageUrl, graphData, maskB64, skeletonB64, imageName, setGraphData, setMaskB64, setSkeletonB64]);

  const handleNext = () => {
    if (activeStep < 4) {
      setActiveStep((prev) => (prev + 1) as any);
    } else {
      navigate("/workspace");
    }
  };

  const handlePrev = () => {
    if (activeStep > 1) {
      setActiveStep((prev) => (prev - 1) as any);
    }
  };

  const handleCancel = () => {
    resetStore();
    navigate("/dashboard");
  };

  return (
    <div className="w-full flex flex-col gap-12 py-4 animate-fadeIn">
      {/* Page Header */}
      <div className="flex items-center justify-between border-b border-stone-border/40 pb-8">
        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-signal">
            Model Inference Wizard
          </span>
          <h1 className="text-display leading-tight text-ink-black font-roobert font-normal">
            Centerline Extraction Pipeline
          </h1>
          <p className="text-[14px] text-warm-gray font-inter">
            Watch the step-by-step extraction workflow as the raw orthophoto gets tiled, masked, thinned, and vectorized.
          </p>
        </div>

        {/* Top Control Buttons */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleCancel}
            className="border border-stone-border hover:bg-stone-muted text-ink-black rounded-full px-5 py-2.5 text-[12px] font-inter font-medium transition-all cursor-pointer active:scale-[0.98] focus:outline-none"
          >
            Cancel Run
          </button>
        </div>
      </div>

      {/* Pipeline Stepper Visual Header */}
      <div className="grid grid-cols-4 border border-stone-border rounded-xl divide-x divide-stone-border bg-pure-white overflow-hidden shadow-md">
        {[
          { step: 1, icon: Grid, label: "1. Tile Subdivision" },
          { step: 2, icon: Layers, label: "2. Stitched Masking" },
          { step: 3, icon: Activity, label: "3. Skeletonization" },
          { step: 4, icon: Network, label: "4. Vector Topology" },
        ].map((item) => {
          const isCurrent = activeStep === item.step;
          const isDone = activeStep > item.step || (graphData && item.step < 4);
          return (
            <div
              key={item.step}
              className={`p-4 flex flex-col gap-2 transition-all duration-200 ${
                isCurrent ? "bg-sky-wash" : "bg-transparent"
              }`}
            >
              <div className="flex items-center justify-between">
                <item.icon
                  className={`w-4 h-4 ${
                    isCurrent ? "text-cyan-signal" : isDone ? "text-emerald-500" : "text-warm-gray"
                  }`}
                />
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                ) : isCurrent && loading ? (
                  <Loader2 className="w-3.5 h-3.5 text-cyan-signal animate-spin shrink-0" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-stone-border" />
                )}
              </div>
              <span
                className={`text-[12px] font-inter font-medium leading-none ${
                  isCurrent ? "text-ink-black font-semibold" : "text-warm-gray"
                }`}
              >
                {item.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Main Sandbox Interactive Stage */}
      <div className="grid grid-cols-12 gap-8 items-stretch min-h-[500px]">
        {/* Visual Box (Left) */}
        <div className="col-span-12 lg:col-span-8 bg-pure-white border border-stone-border rounded-2xl p-6 shadow-md flex items-center justify-center relative overflow-hidden min-h-[400px]">
          {loading && (
            <div className="absolute inset-0 bg-pure-white/85 backdrop-blur-[3px] z-20 flex flex-col items-center justify-center gap-4">
              <Loader2 className="w-8 h-8 text-cyan-signal animate-spin" />
              <div className="flex flex-col items-center text-center gap-1">
                <span className="text-[13px] font-inter font-semibold text-ink-black">
                  Executing GPU Pipeline...
                </span>
                <span className="text-[11px] font-inter text-warm-gray">
                  Calculating model convolutions and graph intersections
                </span>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 bg-pure-white z-20 flex flex-col items-center justify-center gap-4 text-center px-8">
              <div className="w-12 h-12 rounded-full bg-red-950/20 text-red-400 flex items-center justify-center border border-red-500/30">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-[14px] font-inter font-semibold text-ink-black">Pipeline Interrupted</span>
                <span className="text-[12px] font-inter text-warm-gray max-w-[40ch] leading-relaxed">{error}</span>
              </div>
            </div>
          )}

          {imageUrl ? (
            <div className="relative w-full max-w-[500px] aspect-square rounded-lg border border-stone-border overflow-hidden shadow-lg">
              {/* Step 1: Tiles Subdivision */}
              {activeStep === 1 && (
                <div className="relative w-full h-full">
                  <img src={imageUrl} alt="Subdivided tiles" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 gap-0.5 pointer-events-none">
                    {Array.from({ length: 9 }).map((_, i) => (
                      <div
                        key={i}
                        className="border border-cyan-signal/40 bg-cyan-signal/5 animate-pulse flex items-center justify-center text-[10px] font-mono text-cyan-edge font-bold shadow-[inset_0_0_10px_rgba(6,182,212,0.15)]"
                        style={{ animationDelay: `${i * 150}ms` }}
                      >
                        Tile {i + 1}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 2: Merged Mask */}
              {activeStep === 2 && maskB64 && (
                <div className="relative w-full h-full bg-stone-canvas">
                  <img
                    src={maskB64}
                    alt="Road Probability Mask"
                    className="w-full h-full object-contain filter invert opacity-90 transition-opacity"
                  />
                  <div className="absolute bottom-3 left-3 bg-pure-white border border-stone-border text-[9px] px-2.5 py-1 rounded font-mono font-medium text-ink-black shadow-sm">
                    Classified Channels: Binned Lane Widths
                  </div>
                </div>
              )}

              {/* Step 3: Skeleton Centerlines */}
              {activeStep === 3 && skeletonB64 && (
                <div className="relative w-full h-full">
                  <img src={imageUrl} alt="Base" className="absolute inset-0 w-full h-full object-cover brightness-[0.7]" />
                  <img
                    src={skeletonB64}
                    alt="Centerline Skeleton"
                    className="absolute inset-0 w-full h-full object-contain mix-blend-screen hue-rotate-90 filter saturate-200"
                  />
                </div>
              )}

              {/* Step 4: Vector Topology (SVG overlay) */}
              {activeStep === 4 && graphData && (
                <div className="relative w-full h-full bg-stone-canvas">
                  <img src={imageUrl} alt="Base" className="absolute inset-0 w-full h-full object-cover opacity-30" />

                  <svg
                    viewBox={`0 0 ${graphData.imgWidth} ${graphData.imgHeight}`}
                    className="absolute inset-0 w-full h-full pointer-events-none"
                  >
                    {/* Render edges */}
                    {graphData.edges.map((edge, idx) => (
                      <line
                        key={`edge-${idx}`}
                        x1={edge.x1}
                        y1={edge.y1}
                        x2={edge.x2}
                        y2={edge.y2}
                        stroke="#06b6d4"
                        strokeWidth="4"
                        strokeLinecap="round"
                        opacity="0.8"
                      />
                    ))}
                    {/* Render nodes */}
                    {graphData.nodes.map((node, idx) => (
                      <circle
                        key={`node-${idx}`}
                        cx={node.x}
                        cy={node.y}
                        r="6"
                        fill="#EF4444"
                        stroke="#ffffff"
                        strokeWidth="1.5"
                      />
                    ))}
                  </svg>
                </div>
              )}
            </div>
          ) : (
            <div className="text-[13px] font-inter text-warm-gray">No image selected. Please return to dashboard.</div>
          )}
        </div>

        {/* Sidebar Panel Info (Right) */}
        <div className="col-span-12 lg:col-span-4 flex flex-col justify-between bg-pure-white border border-stone-border rounded-2xl p-6 shadow-md">
          <div className="flex flex-col gap-6">
            <h2 className="text-[12px] font-mono uppercase tracking-wider text-ink-black font-semibold border-b border-stone-border pb-4">
              Extraction Details
            </h2>

            {/* Config metadata list */}
            <div className="flex flex-col gap-4 text-[12px] font-inter text-warm-gray">
              <div className="flex items-center justify-between border-b border-stone-border/40 pb-2">
                <span>Working File:</span>
                <span className="font-semibold text-ink-black truncate max-w-[20ch]">{imageName || "Unknown file"}</span>
              </div>
              <div className="flex items-center justify-between border-b border-stone-border/40 pb-2">
                <span>File Size:</span>
                <span className="font-semibold text-ink-black">{imageSize || "N/A"}</span>
              </div>
              <div className="flex items-center justify-between border-b border-stone-border/40 pb-2">
                <span>Pipeline Method:</span>
                <span className="font-semibold text-ink-black font-mono">SpaceNet 5 U-Net</span>
              </div>
              {graphData && (
                <>
                  <div className="flex items-center justify-between border-b border-stone-border/40 pb-2">
                    <span>Total Nodes (Junctions):</span>
                    <span className="font-semibold text-cyan-signal font-mono">{graphData.nodeCount}</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-stone-border/40 pb-2">
                    <span>Total Edges (Road Lanes):</span>
                    <span className="font-semibold text-emerald-500 font-mono">{graphData.edgeCount}</span>
                  </div>
                </>
              )}
            </div>

            {/* Stepper info cards */}
            <div className="bg-stone-canvas border border-stone-border rounded-xl p-5 flex flex-col gap-2">
              <span className="text-[12px] font-inter font-semibold text-ink-black">
                {activeStep === 1 && "Grid Sub-tiling"}
                {activeStep === 2 && "Semantic Segmentation"}
                {activeStep === 3 && "Line-Thinning Analysis"}
                {activeStep === 4 && "Topological Graph Vectorization"}
              </span>
              <p className="text-[12px] leading-relaxed text-warm-gray font-inter">
                {activeStep === 1 &&
                  "The source satellite image is subdivided into 256x256 pixel sub-tiles. Processing small patches preserves local features and avoids GPU out-of-memory overhead."}
                {activeStep === 2 &&
                  "The SpaceNet 5 model predicts pixel probability maps. Each channel classifies lane speeds and existence boundary channels across all coordinates."}
                {activeStep === 3 &&
                  "A morphological thinning algorithm extracts centerlines. This strips adjacent road lanes down to single-pixel wide continuous lanes."}
                {activeStep === 4 &&
                  "Adjacent pixel coordinates are parsed into intersections (nodes) and lines (edges), yielding a lightweight topological graph ready for routing algorithms."}
              </p>
            </div>
          </div>

          {/* Wizard Controls */}
          <div className="flex items-center justify-between border-t border-stone-border pt-6 mt-8">
            <button
              onClick={handlePrev}
              disabled={activeStep === 1}
              className="border border-stone-border hover:bg-stone-canvas disabled:opacity-40 disabled:hover:bg-transparent text-ink-black rounded-full px-5 py-2.5 text-[12px] font-inter font-semibold flex items-center gap-1.5 transition cursor-pointer active:scale-[0.98] focus:outline-none"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back
            </button>
            <button
              onClick={handleNext}
              disabled={loading || !graphData}
              className="bg-cyan-signal hover:bg-cyan-edge disabled:bg-stone-muted disabled:text-warm-gray text-stone-canvas hover:text-white rounded-full px-6 py-2.5 text-[12px] font-inter font-semibold flex items-center gap-1.5 transition-all active:scale-[0.98] cursor-pointer focus:outline-none"
            >
              {activeStep === 4 ? "Enter Simulation" : "Next"}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
