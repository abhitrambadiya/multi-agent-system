import React from 'react';
import { NavRail } from './NavRail';
import { TopBar } from './TopBar';
import { OfficeViewport } from '../office/OfficeViewport';
import { AgentInspector } from '../inspector/AgentInspector';
import { NavModals } from '../modals/NavModals';
import { useUIStore } from '../../store/useUIStore';
import { useSimulationLoop } from '../../simulation/useSimulationLoop';

export const AppShell: React.FC = () => {
  // Start simulation & animation loop
  useSimulationLoop();

  const inspectorOpen = useUIStore(state => state.inspectorOpen);

  return (
    <div id="app" className="relative w-screen h-screen overflow-hidden bg-[#0D0F12]">
      {/* 1. FIXED FULLSCREEN OFFICE VIEWPORT (Covers 100% of the screen) */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden">
        <OfficeViewport />
      </div>

      {/* 2. OVERLAPPING FLOATING TOP STATUS BAR */}
      <div className="absolute top-0 left-0 right-0 z-30 pointer-events-none">
        <div className="pointer-events-auto">
          <TopBar />
        </div>
      </div>

      {/* 3. OVERLAPPING FLOATING LEFT NAVIGATION RAIL */}
      <div className="absolute top-11 bottom-0 left-0 z-30 pointer-events-none flex">
        <div className="pointer-events-auto h-full">
          <NavRail />
        </div>
      </div>

      {/* 4. OVERLAPPING FLOATING RIGHT AGENT INSPECTOR (Smooth slide in/out) */}
      <div
        className={`absolute top-11 bottom-0 right-0 z-30 pointer-events-none flex transition-transform duration-300 ease-in-out ${
          inspectorOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="pointer-events-auto h-full shadow-2xl">
          <AgentInspector />
        </div>
      </div>

      {/* 5. INTERACTIVE VIEW MODALS */}
      <NavModals />
    </div>
  );
};
