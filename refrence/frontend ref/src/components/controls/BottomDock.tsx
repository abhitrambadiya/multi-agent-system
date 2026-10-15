import React from 'react';
import { useCameraStore } from '../../store/useCameraStore';
import { useSimulationStore } from '../../store/useSimulationStore';
import { LocateFixed } from 'lucide-react';

export const BottomDock: React.FC = () => {
  const zoomPercent = useCameraStore(state => state.zoomPercent);
  const zoom = useCameraStore(state => state.zoom);
  const resetCamera = useCameraStore(state => state.resetCamera);

  const speed = useSimulationStore(state => state.speed);
  const setSpeed = useSimulationStore(state => state.setSpeed);
  const showPaths = useSimulationStore(state => state.showPaths);
  const togglePaths = useSimulationStore(state => state.togglePaths);
  const showLabels = useSimulationStore(state => state.showLabels);
  const toggleLabels = useSimulationStore(state => state.toggleLabels);

  const speedOptions = [
    { label: 'Pause', val: 0 },
    { label: '0.5×', val: 0.5 },
    { label: '1×', val: 1 },
    { label: '2×', val: 2 },
  ];

  return (
    <div
      id="dock"
      className="absolute left-1/2 bottom-3.5 -translate-x-1/2 z-20 flex items-center gap-1 bg-[#171A20]/90 backdrop-blur-md border border-[#262b35] rounded-[9px] p-1 text-[13px] shadow-2xl max-w-[calc(100%-16px)] overflow-x-auto select-none"
    >
      {/* Zoom Out */}
      <button
        id="zo"
        onClick={() => zoom(0.8)}
        className="h-6 min-w-[26px] px-2 rounded-md border-0 bg-transparent text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee] transition-colors flex items-center justify-center font-medium"
        title="Zoom out"
      >
        −
      </button>

      {/* Zoom Level Label */}
      <span id="zl" className="min-w-[42px] text-center text-xs text-[#8b93a3] font-mono">
        {zoomPercent}%
      </span>

      {/* Zoom In */}
      <button
        id="zi"
        onClick={() => zoom(1.25)}
        className="h-6 min-w-[26px] px-2 rounded-md border-0 bg-transparent text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee] transition-colors flex items-center justify-center font-medium"
        title="Zoom in"
      >
        +
      </button>

      {/* Reset Camera */}
      <button
        id="zr"
        onClick={resetCamera}
        className="h-6 min-w-[26px] px-2 rounded-md border-0 bg-transparent text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee] transition-colors flex items-center justify-center"
        title="Reset camera (100% view)"
      >
        <LocateFixed className="w-3.5 h-3.5" />
      </button>

      <div className="w-[1px] h-4 bg-[#262b35] mx-1" />

      {/* Speed Controls */}
      {speedOptions.map(opt => (
        <button
          key={opt.val}
          onClick={() => setSpeed(opt.val)}
          className={`h-6 px-2.5 rounded-md text-xs font-medium transition-colors ${
            speed === opt.val
              ? 'bg-[#1e222a] text-[#e6e8ee] border border-[#3a4150]'
              : 'text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee]'
          }`}
        >
          {opt.label}
        </button>
      ))}

      <div className="w-[1px] h-4 bg-[#262b35] mx-1" />

      {/* Overlay Toggles */}
      <button
        id="tpa"
        onClick={togglePaths}
        className={`h-6 px-2.5 rounded-md text-xs font-medium transition-colors ${
          showPaths
            ? 'bg-[#1e222a] text-[#e6e8ee] border border-[#3a4150]'
            : 'text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee]'
        }`}
      >
        Paths
      </button>

      <button
        id="tlb"
        onClick={toggleLabels}
        className={`h-6 px-2.5 rounded-md text-xs font-medium transition-colors ${
          showLabels
            ? 'bg-[#1e222a] text-[#e6e8ee] border border-[#3a4150]'
            : 'text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee]'
        }`}
      >
        Labels
      </button>
    </div>
  );
};
