import React from 'react';
import { useSimulationStore } from '../../store/useSimulationStore';

export const Toast: React.FC = () => {
  const toasts = useSimulationStore(state => state.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-30 pointer-events-none flex flex-col gap-2 items-center">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#171A20] border border-[#262b35] text-sm text-[#e6e8ee] shadow-xl animate-fade-in transition-all"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#4cc38a]" />
          <span>{toast.message}</span>
        </div>
      ))}
    </div>
  );
};
