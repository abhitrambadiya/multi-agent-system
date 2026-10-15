import React from 'react';
import { useUIStore } from '../../store/useUIStore';
import { useAgentStore } from '../../store/useAgentStore';
import { useCameraStore } from '../../store/useCameraStore';
import { AgentId } from '../../types/agent';
import { TICKER_ITEMS } from '../../constants/officeData';
import { X, CheckCircle2, Clock, PlayCircle } from 'lucide-react';

export const NavModals: React.FC = () => {
  const activeModal = useUIStore(state => state.activeModal);
  const closeModal = useUIStore(state => state.closeModal);
  const setInspectorOpen = useUIStore(state => state.setInspectorOpen);

  const agents = useAgentStore(state => state.agents);
  const selectAgent = useAgentStore(state => state.selectAgent);

  const setFollow = useCameraStore(state => state.setFollow);
  const setZoom = useCameraStore(state => state.setZoom);

  if (!activeModal || activeModal === 'office') return null;

  const handleSelectAndFocus = (id: AgentId) => {
    selectAgent(id);
    setFollow(id);
    setZoom(1.9);
    setInspectorOpen(true);
    closeModal();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-[#171A20] border border-[#262b35] rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#262b35] bg-[#1e222a]/40">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#8b7cff]" />
            <h2 className="text-sm font-semibold text-[#e6e8ee] capitalize tracking-wide">
              {activeModal} Overview
            </h2>
          </div>
          <button
            onClick={closeModal}
            className="p-1 rounded-md text-[#8b93a3] hover:text-[#e6e8ee] hover:bg-[#1e222a] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs text-[#8b93a3]">
          {/* 1. AGENTS VIEW */}
          {activeModal === 'agents' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.values(agents).map(agent => (
                <div
                  key={agent.id}
                  className="p-3 rounded-lg bg-[#1e222a]/50 border border-[#262b35] hover:border-[#3a4150] transition-colors flex flex-col justify-between gap-2.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-7 h-7 rounded-md flex items-center justify-center font-bold text-[#0D0F12]"
                        style={{ backgroundColor: agent.color }}
                      >
                        {agent.name[0]}
                      </div>
                      <div>
                        <div className="font-semibold text-[#e6e8ee]">{agent.name}</div>
                        <div className="text-[11px] text-[#8b93a3]">{agent.role}</div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#262b35] text-[#e6e8ee] font-medium">
                      {agent.statusText}
                    </span>
                  </div>

                  <div className="bg-[#0D0F12] p-2 rounded border border-[#262b35]/60">
                    <span className="text-[10px] text-[#5f6779] uppercase block font-semibold mb-0.5">
                      Active Task:
                    </span>
                    <p className="text-xs text-[#e6e8ee] truncate">{agent.task}</p>
                    <div className="w-full bg-[#262b35] h-1 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className="bg-[#8b7cff] h-full"
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelectAndFocus(agent.id)}
                    className="w-full py-1.5 rounded bg-[#262b35] hover:bg-[#8b7cff] hover:text-[#0D0F12] text-[#e6e8ee] font-medium transition-colors flex items-center justify-center gap-1.5"
                  >
                    <PlayCircle className="w-3.5 h-3.5" />
                    <span>Track Agent</span>
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 2. TASKS VIEW */}
          {activeModal === 'tasks' && (
            <div className="space-y-4">
              <div className="text-xs text-[#8b93a3]">
                Live queue across all active agents in the Agent HQ simulation:
              </div>
              <div className="space-y-2">
                {Object.values(agents).map(agent => (
                  <div
                    key={agent.id}
                    className="p-3 rounded-lg bg-[#1e222a]/40 border border-[#262b35] flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span
                        className="w-2.5 h-2.5 rounded-full flex-none"
                        style={{ backgroundColor: agent.color }}
                      />
                      <div className="min-w-0">
                        <div className="font-semibold text-[#e6e8ee] truncate">
                          {agent.task}
                        </div>
                        <div className="text-[11px] text-[#8b93a3]">
                          Assigned to {agent.name} • {Math.round(agent.progress)}% complete
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleSelectAndFocus(agent.id)}
                      className="px-2.5 py-1 rounded bg-[#262b35] hover:bg-[#1e222a] text-[#e6e8ee] text-xs font-medium flex-none transition-colors"
                    >
                      Inspect
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. MARKETS VIEW */}
          {activeModal === 'markets' && (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-[#0D0F12] border border-[#262b35] font-mono">
                <div className="flex items-center justify-between border-b border-[#262b35] pb-2 mb-2 text-[#8b93a3]">
                  <span>Ticker Watchlist</span>
                  <span>Nova AI Risk Feed</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {TICKER_ITEMS.map((item, i) => (
                    <div
                      key={i}
                      className="p-2 rounded bg-[#171A20] border border-[#262b35] flex justify-between items-center"
                    >
                      <span className="text-[#e6e8ee] font-semibold">
                        {item.symbol.split(' ')[0]}
                      </span>
                      <span style={{ color: item.color }} className="font-semibold">
                        {item.symbol.split(' ')[1]}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-[#1e222a]/40 border border-[#262b35] text-xs">
                <span className="font-semibold text-[#e6e8ee] block mb-1">
                  Analyst Intelligence Note:
                </span>
                Tracking liquidity spreads across mega-cap tech components. Low volatility
                regime maintained throughout current session. Automated alerts configured
                for &gt; 3% deviations.
              </div>
            </div>
          )}

          {/* 4. MEETINGS VIEW */}
          {activeModal === 'meetings' && (
            <div className="space-y-3">
              <div className="text-xs text-[#8b93a3]">
                Scheduled collaborative synchronization in the Meeting Room:
              </div>
              {[
                {
                  time: '11:00 AM',
                  title: 'Daily Synthesis & Drafting Sync',
                  room: 'Meeting Room',
                  lead: 'Echo (Writing Agent)',
                  status: 'In Progress / Walking',
                },
                {
                  time: '14:00 PM',
                  title: 'Market Spread Risk Review',
                  room: 'Meeting Room',
                  lead: 'Nova (Market Analyst)',
                  status: 'Upcoming',
                },
                {
                  time: '16:30 PM',
                  title: 'Engineering Deployment Gate',
                  room: 'Trading Desk Lounge',
                  lead: 'Pixel & Sage',
                  status: 'Scheduled',
                },
              ].map((m, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-[#1e222a]/50 border border-[#262b35] flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3.5 h-3.5 text-[#8b7cff]" />
                      <span className="font-mono text-[#e6e8ee] font-semibold">{m.time}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#262b35] text-[#8b93a3]">
                        {m.room}
                      </span>
                    </div>
                    <div className="font-semibold text-sm text-[#e6e8ee]">{m.title}</div>
                    <div className="text-[11px] text-[#8b93a3]">Lead: {m.lead}</div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#262b35] text-[#4cc38a] font-medium flex-none">
                    {m.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-[#262b35] bg-[#1e222a]/40 flex justify-end">
          <button
            onClick={closeModal}
            className="px-4 py-1.5 rounded-md bg-[#262b35] hover:bg-[#3a4150] text-[#e6e8ee] font-medium text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
