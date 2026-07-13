import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../../store/useAppStore";
import { MapPin, UploadCloud, Database, Clock, LogOut, ArrowRight, FileImage } from "lucide-react";

// Demo pre-fitted cities
const PRE_FITTED_CITIES = [
  {
    id: "mumbai",
    name: "Mumbai Suburbs",
    state: "Maharashtra",
    size: "12.4 MB",
    resolution: "0.6m GSD (SpaceNet 5)",
    image: "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=600&auto=format&fit=crop&q=60",
    localPath: "/validation/vision/samples/sample_sat.png",
  },
  {
    id: "delhi",
    name: "Delhi Cantonment",
    state: "NCR",
    size: "18.1 MB",
    resolution: "0.5m GSD (Multi-band)",
    image: "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=600&auto=format&fit=crop&q=60",
    localPath: "/validation/vision/samples/sample_sat.png",
  },
  {
    id: "bangalore",
    name: "Bangalore Tech Corridor",
    state: "Karnataka",
    size: "15.6 MB",
    resolution: "0.6m GSD (SpaceNet 5)",
    image: "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=600&auto=format&fit=crop&q=60",
    localPath: "/validation/vision/samples/sample_sat.png",
  },
];

// Mock history records
const MOCK_HISTORY = [
  { id: 1, name: "Mumbai_Suburbs_Zone3.png", date: "July 14, 2026", nodes: 127, edges: 182 },
  { id: 2, name: "Dar_Es_Salaam_Raw.tif", date: "July 13, 2026", nodes: 55, edges: 47 },
];

export const DashboardStep: React.FC = () => {
  const navigate = useNavigate();
  const { setSelectedImage, setImageUrlDirectly, logout } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleSelectCity = (city: typeof PRE_FITTED_CITIES[0]) => {
    setImageUrlDirectly(city.localPath, city.name, city.size);
    navigate("/extraction");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedImage(e.target.files[0]);
      navigate("/extraction");
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedImage(e.dataTransfer.files[0]);
      navigate("/extraction");
    }
  };

  return (
    <div className="w-full flex flex-col gap-12 py-4 animate-fadeIn">
      {/* Header Panel */}
      <div className="flex items-center justify-between border-b border-stone-border/40 pb-8">
        <div className="flex flex-col gap-2">
          <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-cyan-signal">
            City Command Center
          </span>
          <h1 className="text-4xl md:text-5xl font-roobert font-medium text-ink-black tracking-tight">
            ARGUS Map Workspace
          </h1>
          <p className="text-[14px] text-warm-gray font-inter max-w-[65ch]">
            Select a pre-configured smart city map or upload custom orthophotos to analyze road centerlines and topological graphs.
          </p>
        </div>
        <button
          onClick={logout}
          className="border border-stone-border hover:bg-stone-muted text-ink-black rounded-full px-5 py-2.5 text-[12px] font-inter font-medium flex items-center gap-2 transition-all cursor-pointer focus:outline-none focus:ring-0 active:scale-[0.98]"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </button>
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-12 gap-8 items-start">
        {/* Left Column: Pre-Fitted Cities (Bento Bento!) */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-cyan-signal" />
            <h2 className="text-[12px] font-mono uppercase tracking-wider text-ink-black font-semibold">
              Pre-Configured City Datasets
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {PRE_FITTED_CITIES.map((city) => (
              <div
                key={city.id}
                onClick={() => handleSelectCity(city)}
                className="group bg-pure-white border border-stone-border rounded-xl overflow-hidden hover:border-cyan-signal/30 hover:shadow-lg transition-all duration-300 cursor-pointer flex flex-col h-[280px]"
              >
                <div className="h-36 w-full overflow-hidden bg-stone-canvas relative">
                  <img
                    src={city.image}
                    alt={city.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-all duration-500 brightness-[0.85] group-hover:brightness-95"
                  />
                  <div className="absolute top-3 left-3 bg-stone-canvas/90 backdrop-blur-md border border-stone-border text-[9px] px-2.5 py-1 rounded font-mono font-medium text-ink-black flex items-center gap-1.5">
                    <MapPin className="w-3 h-3 text-cyan-signal" />
                    {city.state}
                  </div>
                </div>
                <div className="p-5 flex flex-col gap-2 flex-grow justify-between">
                  <div className="flex flex-col gap-1">
                    <h3 className="text-[15px] font-inter font-semibold text-ink-black group-hover:text-cyan-signal transition">
                      {city.name}
                    </h3>
                    <p className="text-[11px] font-mono text-warm-gray uppercase tracking-tight">
                      {city.resolution}
                    </p>
                  </div>
                  <div className="flex items-center justify-between border-t border-stone-border/40 pt-4 mt-2">
                    <span className="text-[11px] font-mono text-warm-gray font-semibold">{city.size}</span>
                    <span className="text-[11px] font-inter font-semibold text-cyan-signal flex items-center gap-1.5 group-hover:translate-x-1.5 transition-transform">
                      Load City <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Custom Upload & History */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-8">
          {/* Custom Upload Card */}
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-cyan-signal" />
              <h2 className="text-[12px] font-mono uppercase tracking-wider text-ink-black font-semibold">
                Analyze Custom Map
              </h2>
            </div>

            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`bg-pure-white border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center gap-5 text-center cursor-pointer transition-all duration-300 ${
                dragActive
                  ? "border-cyan-signal bg-sky-wash/10 scale-[0.99] shadow-inner"
                  : "border-stone-border hover:border-cyan-signal/50 hover:bg-stone-muted/30"
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
              />
              <div className="w-12 h-12 rounded-full bg-stone-canvas flex items-center justify-center border border-stone-border">
                <FileImage className="w-5 h-5 text-warm-gray" />
              </div>
              <div className="flex flex-col gap-1.5">
                <span className="text-[13px] font-inter font-semibold text-ink-black">
                  Upload satellite raster
                </span>
                <span className="text-[11px] font-inter text-warm-gray max-w-[28ch] mx-auto leading-relaxed">
                  Drag & drop PNG, JPG, or GeoTIFF map assets (Max 50MB)
                </span>
              </div>
            </div>
          </div>

          {/* History Card */}
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-signal" />
              <h2 className="text-[12px] font-mono uppercase tracking-wider text-ink-black font-semibold">
                Recent Analyses
              </h2>
            </div>

            <div className="bg-pure-white border border-stone-border rounded-xl divide-y divide-stone-border overflow-hidden">
              {MOCK_HISTORY.map((item) => (
                <div
                  key={item.id}
                  className="p-5 flex items-center justify-between text-[12px] font-inter hover:bg-stone-muted/50 transition-colors"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-semibold text-ink-black truncate max-w-[20ch]">
                      {item.name}
                    </span>
                    <span className="text-[11px] text-warm-gray">{item.date}</span>
                  </div>
                  <div className="flex flex-col items-end gap-1 text-right font-mono text-[10px] text-warm-gray">
                    <span>{item.nodes} Junctions</span>
                    <span>{item.edges} Segments</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
