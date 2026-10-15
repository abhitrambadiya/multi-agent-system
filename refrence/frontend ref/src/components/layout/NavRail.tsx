import React from 'react';
import { useUIStore, NavTab } from '../../store/useUIStore';
import {
  Building2,
  Users,
  CheckSquare,
  TrendingUp,
  Calendar,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';

export const NavRail: React.FC = () => {
  const railExpanded = useUIStore(state => state.railExpanded);
  const toggleRail = useUIStore(state => state.toggleRail);
  const activeNavTab = useUIStore(state => state.activeNavTab);
  const setActiveNavTab = useUIStore(state => state.setActiveNavTab);

  const navItems: { id: NavTab; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'office', label: 'Office', icon: Building2 },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'tasks', label: 'Tasks', icon: CheckSquare },
    { id: 'markets', label: 'Markets', icon: TrendingUp },
    { id: 'meetings', label: 'Meetings', icon: Calendar },
  ];

  return (
    <nav
      id="rail"
      className={`h-full bg-[#171A20]/90 backdrop-blur-md border-r border-[#262b35]/80 py-2.5 px-2 flex flex-col gap-1 overflow-hidden select-none transition-all duration-300 z-30 flex-none shadow-2xl ${
        railExpanded ? 'w-44' : 'w-[52px]'
      }`}
    >
      {/* Brand logo */}
      <div className="h-7 flex items-center gap-2.5 pl-1 mb-2.5 font-semibold text-xs tracking-tight whitespace-nowrap text-[#e6e8ee]">
        <div className="w-[18px] h-[18px] rounded-[5px] bg-[#8b7cff] flex-none shadow-sm flex items-center justify-center font-black text-[9px] text-[#0D0F12]">
          HQ
        </div>
        {railExpanded && (
          <span className="font-semibold text-[13px] animate-fade-in truncate">
            Agent HQ
          </span>
        )}
      </div>

      {/* Nav Buttons */}
      {navItems.map(item => {
        const Icon = item.icon;
        const isActive = activeNavTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveNavTab(item.id)}
            title={item.label}
            className={`flex items-center gap-2.5 h-8 px-2 rounded-md whitespace-nowrap text-xs transition-colors cursor-pointer ${
              isActive
                ? 'bg-[#1e222a] text-[#e6e8ee] font-medium'
                : 'text-[#8b93a3] hover:bg-[#1e222a]/70 hover:text-[#e6e8ee]'
            }`}
          >
            <Icon className="w-[18px] h-[18px] flex-none" />
            {railExpanded && <span className="truncate">{item.label}</span>}
          </button>
        );
      })}

      <div className="flex-1" />

      {/* Collapse / Expand rail toggle */}
      <button
        id="rt"
        onClick={toggleRail}
        title={railExpanded ? 'Collapse navigation' : 'Expand navigation'}
        className="flex items-center gap-2.5 h-8 px-2 rounded-md whitespace-nowrap text-xs text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee] transition-colors cursor-pointer"
      >
        {railExpanded ? (
          <>
            <ChevronLeft className="w-[18px] h-[18px] flex-none" />
            <span className="truncate">Collapse</span>
          </>
        ) : (
          <ChevronRight className="w-[18px] h-[18px] flex-none" />
        )}
      </button>
    </nav>
  );
};
