import React from 'react';
import { useAgentStore } from '../../store/useAgentStore';
import { useSimulationStore } from '../../store/useSimulationStore';
import { useUIStore } from '../../store/useUIStore';
import { PanelRightClose, PanelRightOpen } from 'lucide-react';

export const TopBar: React.FC = () => {
  const agents = useAgentStore(state => state.agents);
  const getFormattedTime = useSimulationStore(state => state.getFormattedTime);
  const inspectorOpen = useUIStore(state => state.inspectorOpen);
  const toggleInspector = useUIStore(state => state.toggleInspector);

  // Active agents count: non-break and non-idle
  const activeCount = Object.values(agents).filter(
    a => a.statusText !== 'Coffee break' && a.statusText !== 'Idle'
  ).length;

  const formattedTime = getFormattedTime();

  return (
    <header
      id="top"
      className="h-11 bg-[#171A20]/85 backdrop-blur-md border-b border-[#262b35]/80 flex items-center gap-2 px-3 select-none flex-none z-20 text-[13px] shadow-sm"
    >
      {/* Breadcrumbs */}
      <span className="text-[#8b93a3]">
        Agent HQ / <b className="text-[#e6e8ee] font-medium">Main office</b>
      </span>

      <div className="flex-1" />

      {/* Active agents badge */}
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-[#262b35] text-xs text-[#8b93a3] bg-[#171A20]/90">
        <span className="w-1.5 h-1.5 rounded-full bg-[#4cc38a] animate-pulse" />
        <span className="font-mono">
          <b id="act" className="text-[#e6e8ee] font-semibold mr-1">
            {activeCount}
          </b>
          active
        </span>
      </div>

      {/* Clock badge */}
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-[#262b35] text-xs text-[#8b93a3] bg-[#171A20]/90">
        <span>Day 3</span>
        <b id="clk" className="text-[#e6e8ee] font-mono font-medium">
          {formattedTime}
        </b>
      </div>

      {/* Inspector toggle button */}
      <button
        id="it"
        onClick={toggleInspector}
        title={inspectorOpen ? 'Hide inspector' : 'Show inspector'}
        className={`h-7 w-7 rounded-md border flex items-center justify-center transition-colors cursor-pointer ${
          inspectorOpen
            ? 'bg-[#1e222a] border-[#3a4150] text-[#e6e8ee]'
            : 'border-[#262b35] text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee]'
        }`}
      >
        {inspectorOpen ? (
          <PanelRightClose className="w-3.5 h-3.5" />
        ) : (
          <PanelRightOpen className="w-3.5 h-3.5" />
        )}
      </button>
    </header>
  );
};
