import React, { useRef, useEffect, useCallback } from 'react';
import { useCameraStore } from '../../store/useCameraStore';
import { useSimulationStore } from '../../store/useSimulationStore';
import { useAgentStore } from '../../store/useAgentStore';
import { OfficeDefs } from './OfficeDefs';
import { OfficeRooms } from './OfficeRooms';
import { AgentRenderer } from '../agent/AgentRenderer';
import { BottomDock } from '../controls/BottomDock';
import { Toast } from '../controls/Toast';

export const OfficeViewportComponent: React.FC = () => {
  const stageRef = useRef<HTMLElement>(null);
  const isPointerDownRef = useRef(false);
  const dragPosRef = useRef<{ x: number; y: number } | null>(null);

  const showPaths = useSimulationStore(state => state.showPaths);
  const showLabels = useSimulationStore(state => state.showLabels);
  const agents = useAgentStore(state => state.agents);

  // Wheel zoom handler
  useEffect(() => {
    const stageEl = stageRef.current;
    if (!stageEl) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      useCameraStore.getState().zoom(e.deltaY < 0 ? 1.1 : 0.91);
    };

    stageEl.addEventListener('wheel', handleWheel, { passive: false });
    return () => stageEl.removeEventListener('wheel', handleWheel);
  }, []);

  // Pointer panning handlers
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    const target = e.target as HTMLElement;
    if (target.closest('.agent')) return;

    isPointerDownRef.current = true;
    dragPosRef.current = { x: e.clientX, y: e.clientY };

    const svg = document.getElementById('world');
    if (svg) svg.style.cursor = 'grabbing';
  }, []);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!isPointerDownRef.current || !dragPosRef.current) return;

    const stageEl = stageRef.current;
    const rect = stageEl ? stageEl.getBoundingClientRect() : { width: window.innerWidth, height: window.innerHeight };
    const fitFactor = Math.min(rect.width / 1200, rect.height / 760);

    const deltaX = e.clientX - dragPosRef.current.x;
    const deltaY = e.clientY - dragPosRef.current.y;

    useCameraStore.getState().pan(deltaX, deltaY, fitFactor);
    dragPosRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handlePointerUp = useCallback(() => {
    isPointerDownRef.current = false;
    dragPosRef.current = null;

    const svg = document.getElementById('world');
    if (svg) svg.style.cursor = 'grab';
  }, []);

  const stageClasses = [
    'relative',
    'w-full',
    'h-full',
    'overflow-hidden',
    'bg-[#0D0F12]',
    'select-none',
    'touch-none',
    showPaths ? 'showp' : '',
    !showLabels ? 'nolbl' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <main
      id="stage"
      ref={stageRef}
      className={stageClasses}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <svg
        id="world"
        role="img"
        aria-label="Top-down view of the Agent HQ office"
        viewBox="0 0 1200 760"
        className="w-full h-full block cursor-grab"
      >
        <OfficeDefs />
        <OfficeRooms />

        {/* 5 Office Agents */}
        <g id="agents-layer">
          {Object.values(agents).map(agent => (
            <AgentRenderer key={agent.id} agent={agent} />
          ))}
        </g>
      </svg>

      {/* Floating UI Overlays inside Stage */}
      <Toast />
      <BottomDock />
    </main>
  );
};

export const OfficeViewport = React.memo(OfficeViewportComponent);
