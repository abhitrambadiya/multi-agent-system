import { create } from 'zustand';
import { AgentId } from '../types/agent';

interface CameraStore {
  // Target coordinates for smooth interpolation
  targetX: number;
  targetY: number;
  targetZ: number;

  // Current interpolated coordinates
  camX: number;
  camY: number;
  camZ: number;

  followAgentId: AgentId | null;
  isDragging: boolean;
  zoomPercent: number;

  zoom: (factor: number) => void;
  setZoom: (z: number) => void;
  resetCamera: () => void;
  pan: (deltaX: number, deltaY: number, fitFactor: number) => void;
  setFollow: (agentId: AgentId | null) => void;
  setDragging: (dragging: boolean) => void;
  setTarget: (tx: number, ty: number, tz?: number) => void;
  setInterpolated: (cx: number, cy: number, cz: number) => void;
}

export const useCameraStore = create<CameraStore>((set, get) => ({
  targetX: 600,
  targetY: 380,
  targetZ: 1.0,

  camX: 600,
  camY: 380,
  camZ: 1.0,

  followAgentId: null,
  isDragging: false,
  zoomPercent: 100,

  zoom: (factor: number) => {
    const { targetZ } = get();
    const nextZ = Math.min(3.5, Math.max(0.7, targetZ * factor));
    set({ targetZ: nextZ, zoomPercent: Math.round(nextZ * 100) });
  },

  setZoom: (z: number) => {
    const nextZ = Math.min(3.5, Math.max(0.7, z));
    set({ targetZ: nextZ, zoomPercent: Math.round(nextZ * 100) });
  },

  resetCamera: () => {
    set({
      targetX: 600,
      targetY: 380,
      targetZ: 1.0,
      followAgentId: null,
      zoomPercent: 100,
    });
  },

  pan: (deltaX: number, deltaY: number, fitFactor: number) => {
    const { camZ, targetX, targetY } = get();
    const k = Math.max(0.001, fitFactor * camZ);
    const nx = targetX - deltaX / k;
    const ny = targetY - deltaY / k;
    set({
      targetX: nx,
      targetY: ny,
      followAgentId: null, // Panning detaches follow mode
    });
  },

  setFollow: (agentId: AgentId | null) => {
    const current = get().followAgentId;
    if (current === agentId) {
      // Toggle off
      set({
        followAgentId: null,
        targetX: 600,
        targetY: 380,
        targetZ: 1.0,
        zoomPercent: 100,
      });
    } else {
      // Follow this agent with close-up camera
      set(state => ({
        followAgentId: agentId,
        targetZ: Math.max(state.targetZ, 1.9),
        zoomPercent: Math.round(Math.max(state.targetZ, 1.9) * 100),
      }));
    }
  },

  setDragging: (isDragging: boolean) => set({ isDragging }),

  setTarget: (tx: number, ty: number, tz?: number) => {
    set(state => ({
      targetX: tx,
      targetY: ty,
      ...(tz !== undefined ? { targetZ: tz, zoomPercent: Math.round(tz * 100) } : {}),
    }));
  },

  setInterpolated: (cx: number, cy: number, cz: number) => {
    // Only update store if rounded zoom percent changed
    const nextP = Math.round(cz * 100);
    const currentP = get().zoomPercent;
    if (nextP !== currentP) {
      set({ camX: cx, camY: cy, camZ: cz, zoomPercent: nextP });
    } else {
      set({ camX: cx, camY: cy, camZ: cz });
    }
  },
}));
