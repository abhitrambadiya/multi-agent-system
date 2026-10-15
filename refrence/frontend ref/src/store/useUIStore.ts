import { create } from 'zustand';

export type NavTab = 'office' | 'agents' | 'tasks' | 'markets' | 'meetings';

interface UIStore {
  railExpanded: boolean;
  inspectorOpen: boolean;
  activeNavTab: NavTab;
  activeModal: NavTab | null;

  toggleRail: () => void;
  toggleInspector: () => void;
  setInspectorOpen: (open: boolean) => void;
  setActiveNavTab: (tab: NavTab) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIStore>((set, get) => ({
  railExpanded: false,
  inspectorOpen: true,
  activeNavTab: 'office',
  activeModal: null,

  toggleRail: () => set(state => ({ railExpanded: !state.railExpanded })),

  toggleInspector: () => set(state => ({ inspectorOpen: !state.inspectorOpen })),

  setInspectorOpen: (open: boolean) => set({ inspectorOpen: open }),

  setActiveNavTab: (tab: NavTab) => {
    if (tab === 'office') {
      set({ activeNavTab: 'office', activeModal: null });
    } else {
      set({ activeNavTab: tab, activeModal: tab });
    }
  },

  closeModal: () => set({ activeNavTab: 'office', activeModal: null }),
}));
