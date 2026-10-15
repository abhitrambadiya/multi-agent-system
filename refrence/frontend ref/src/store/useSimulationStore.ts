import { create } from 'zustand';

export interface ToastItem {
  id: string;
  message: string;
}

interface SimulationStore {
  simMinutes: number; // in minutes from midnight (642 = 10:42)
  speed: number; // 0, 0.5, 1, 2
  showPaths: boolean;
  showLabels: boolean;
  toasts: ToastItem[];

  setSpeed: (speed: number) => void;
  togglePaths: () => void;
  toggleLabels: () => void;
  advanceMinutes: (delta: number) => void;
  addToast: (message: string) => void;
  removeToast: (id: string) => void;
  getFormattedTime: () => string;
}

export const useSimulationStore = create<SimulationStore>((set, get) => ({
  simMinutes: 642, // 10:42
  speed: 1,
  showPaths: false,
  showLabels: true,
  toasts: [],

  setSpeed: (speed: number) => set({ speed }),

  togglePaths: () => set(state => ({ showPaths: !state.showPaths })),

  toggleLabels: () => set(state => ({ showLabels: !state.showLabels })),

  advanceMinutes: (delta: number) =>
    set(state => ({
      simMinutes: (state.simMinutes + delta) % (24 * 60),
    })),

  addToast: (message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    set(state => ({
      toasts: [...state.toasts, { id, message }],
    }));
    setTimeout(() => {
      get().removeToast(id);
    }, 2800);
  },

  removeToast: (id: string) => {
    set(state => ({
      toasts: state.toasts.filter(t => t.id !== id),
    }));
  },

  getFormattedTime: () => {
    const m = get().simMinutes;
    const hours = Math.floor((m / 60) % 24);
    const mins = Math.floor(m % 60);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
  },
}));
