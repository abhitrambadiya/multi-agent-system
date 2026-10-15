import React, { useState } from 'react';
import { useAgentStore } from '../../store/useAgentStore';
import { useCameraStore } from '../../store/useCameraStore';
import { useSimulationStore } from '../../store/useSimulationStore';
import { INITIAL_TASKS } from '../../constants/initialAgents';
import { AgentId } from '../../types/agent';

export const AgentInspector: React.FC = () => {
  const [pickOpen, setPickOpen] = useState(false);

  const selectedAgentId = useAgentStore(state => state.selectedAgentId);
  const selectAgent = useAgentStore(state => state.selectAgent);
  const agents = useAgentStore(state => state.agents);
  const assignTask = useAgentStore(state => state.assignTask);

  const followAgentId = useCameraStore(state => state.followAgentId);
  const setFollow = useCameraStore(state => state.setFollow);
  const getFormattedTime = useSimulationStore(state => state.getFormattedTime);

  const agent = agents[selectedAgentId];
  if (!agent) return null;

  const isFollowing = followAgentId === agent.id;

  const handleAssign = (taskTitle: string) => {
    assignTask(agent.id, taskTitle, getFormattedTime());
    setPickOpen(false);
  };

  const handleToggleFollow = () => {
    setFollow(agent.id);
  };

  const agentIds: AgentId[] = ['atlas', 'nova', 'echo', 'sage', 'pixel'];

  return (
    <aside
      id="insp"
      className="w-[312px] h-full flex-none bg-[#171A20]/95 backdrop-blur-lg border-l border-[#262b35]/80 overflow-y-auto select-none transition-all duration-300 shadow-2xl"
    >
      <div className="p-4 flex flex-col gap-4">
        {/* Quick Agent Selection Bar */}
        <div className="flex items-center justify-between pb-3 border-b border-[#262b35]">
          <span className="text-[11px] font-medium uppercase tracking-wider text-[#8b93a3]">
            Roster
          </span>
          <div className="flex items-center gap-1.5">
            {agentIds.map(id => {
              const a = agents[id];
              const isSel = a.id === selectedAgentId;
              return (
                <button
                  key={id}
                  onClick={() => selectAgent(id)}
                  title={`${a.name} (${a.role})`}
                  className={`w-6 h-6 rounded-md text-[11px] font-semibold transition-all flex items-center justify-center ${
                    isSel
                      ? 'ring-2 ring-[#8b7cff] scale-105 text-[#0D0F12]'
                      : 'opacity-70 hover:opacity-100 text-[#0D0F12]'
                  }`}
                  style={{ backgroundColor: a.color }}
                >
                  {a.name[0]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Header: Avatar, Name, Role */}
        <div className="flex items-center gap-2.5">
          <div
            className="w-[34px] h-[34px] rounded-[9px] flex items-center justify-center font-semibold text-[#0D0F12] shadow-md flex-none"
            style={{ backgroundColor: agent.color }}
          >
            {agent.name[0]}
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-semibold text-[#e6e8ee] leading-tight truncate">
              {agent.name}
            </h2>
            <small className="text-xs text-[#8b93a3] truncate block">
              {agent.role}
            </small>
          </div>
        </div>

        {/* Live Status indicator */}
        <div className="flex items-center gap-2 text-[13px] text-[#e6e8ee] bg-[#1e222a]/60 px-2.5 py-1.5 rounded-lg border border-[#262b35]">
          <span
            className="w-1.5 h-1.5 rounded-full flex-none animate-pulse"
            style={{ backgroundColor: agent.color }}
          />
          <span id="is" className="font-medium text-xs">
            {agent.statusText}
          </span>
          <em className="ml-auto not-italic text-[#4cc38a] text-[11px] font-medium tracking-wide">
            Live
          </em>
        </div>

        {/* Current Task & Progress Bar */}
        <div className="flex flex-col gap-1.5">
          <h3 className="text-[11px] font-medium text-[#8b93a3] tracking-wide uppercase">
            Current task
          </h3>
          <div
            id="it2"
            className="text-[13px] text-[#e6e8ee] font-medium leading-relaxed bg-[#1e222a] p-2.5 rounded-lg border border-[#262b35]"
          >
            {agent.task}
          </div>
          <div className="h-1 bg-[#262b35] rounded-full overflow-hidden mt-1">
            <div
              id="ipg"
              className="h-full bg-[#8b7cff] transition-all duration-300 ease-linear rounded-full"
              style={{ width: `${Math.min(100, Math.max(0, agent.progress))}%` }}
            />
          </div>
          <div className="flex justify-between items-center text-[10px] text-[#8b93a3] font-mono px-0.5">
            <span>Progress</span>
            <span>{Math.round(agent.progress)}%</span>
          </div>
        </div>

        {/* Action Buttons: Assign Task & Follow Agent */}
        <div className="flex gap-2 relative">
          <button
            id="as"
            onClick={() => setPickOpen(prev => !prev)}
            className={`flex-1 h-8 rounded-md text-xs font-medium transition-all ${
              pickOpen
                ? 'bg-[#8b7cff] text-[#0D0F12] shadow-sm'
                : 'bg-[#8b7cff] text-[#0D0F12] hover:brightness-110'
            }`}
          >
            Assign task
          </button>
          <button
            id="fb"
            onClick={handleToggleFollow}
            className={`flex-1 h-8 rounded-md text-xs font-medium border transition-colors ${
              isFollowing
                ? 'bg-[#1e222a] border-[#3a4150] text-[#e6e8ee]'
                : 'border-[#262b35] text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee]'
            }`}
          >
            {isFollowing ? 'Following' : 'Follow agent'}
          </button>
        </div>

        {/* Task Selection Popover */}
        {pickOpen && (
          <div
            id="pick"
            className="flex flex-col gap-1 p-1.5 rounded-lg bg-[#0D0F12] border border-[#262b35] shadow-xl animate-fade-in"
          >
            <div className="text-[10px] text-[#8b93a3] uppercase font-semibold px-2 py-1">
              Select task to assign:
            </div>
            {INITIAL_TASKS.map(taskOption => (
              <button
                key={taskOption}
                onClick={() => handleAssign(taskOption)}
                className="w-full text-left px-2.5 py-1.5 rounded text-xs text-[#8b93a3] hover:bg-[#1e222a] hover:text-[#e6e8ee] transition-colors truncate"
              >
                {taskOption}
              </button>
            ))}
          </div>
        )}

        {/* Upcoming Queue */}
        {agent.queue.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <h3 className="text-[11px] font-medium text-[#8b93a3] tracking-wide uppercase">
              Queued ({agent.queue.length})
            </h3>
            <div className="flex flex-col gap-1">
              {agent.queue.map((qItem, idx) => (
                <div
                  key={idx}
                  className="text-xs text-[#8b93a3] bg-[#1e222a]/40 px-2.5 py-1.5 rounded border border-[#262b35]/60 truncate"
                >
                  <span className="text-[#5f6779] mr-2">#{idx + 1}</span>
                  {qItem}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Activity Timeline */}
        <div className="flex flex-col gap-1.5">
          <h3 className="text-[11px] font-medium text-[#8b93a3] tracking-wide uppercase">
            Activity
          </h3>
          <ul className="relative pl-4 m-0 list-none flex flex-col gap-1 text-xs before:absolute before:left-[3px] before:top-2 before:bottom-2 before:w-[1px] before:bg-[#262b35]">
            {agent.log.slice(0, 5).map((logItem, index) => (
              <li
                key={index}
                className={`relative py-1 flex gap-2.5 items-baseline before:absolute before:-left-4 before:top-2.5 before:w-[7px] before:h-[7px] before:rounded-full before:border ${
                  index === 0
                    ? 'text-[#e6e8ee] before:bg-[#8b7cff] before:border-[#8b7cff]'
                    : 'text-[#8b93a3] before:bg-[#171A20] before:border-[#3a4150]'
                }`}
              >
                <time className="text-[#5f6779] font-mono text-[11px] flex-none">
                  {logItem[0]}
                </time>
                <span className="leading-snug">{logItem[1]}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Recent Achievements */}
        <div className="flex flex-col gap-1.5">
          <h3 className="text-[11px] font-medium text-[#8b93a3] tracking-wide uppercase">
            Recent achievements
          </h3>
          <div className="flex flex-col gap-2 text-xs text-[#8b93a3]">
            {agent.achievements.slice(0, 3).map((achievement, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <i className="w-1.5 h-1.5 bg-[#8b7cff] rotate-45 flex-none" />
                <span className="truncate">{achievement}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
};
