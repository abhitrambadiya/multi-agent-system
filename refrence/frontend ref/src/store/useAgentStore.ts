import { create } from 'zustand';
import { Agent, AgentId } from '../types/agent';
import { INITIAL_AGENTS, INITIAL_TASKS } from '../constants/initialAgents';

interface AgentStore {
  agents: Record<AgentId, Agent>;
  selectedAgentId: AgentId;
  completedAgentId: AgentId | null;

  selectAgent: (id: AgentId) => void;
  updateAgent: (id: AgentId, updates: Partial<Agent>) => void;
  assignTask: (id: AgentId, task: string, timeStr: string) => void;
  completeTask: (id: AgentId, timeStr: string, onToast?: (msg: string) => void) => void;
  advanceTaskProgress: (id: AgentId, deltaProgress: number, timeStr: string, onToast?: (msg: string) => void) => void;
  addLog: (id: AgentId, timeStr: string, message: string) => void;
  setAgentPosition: (id: AgentId, x: number, y: number, facingUp?: boolean, flipped?: boolean) => void;
  clearCompletedEffect: () => void;
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  agents: INITIAL_AGENTS,
  selectedAgentId: 'nova',
  completedAgentId: null,

  selectAgent: (id: AgentId) => set({ selectedAgentId: id }),

  updateAgent: (id: AgentId, updates: Partial<Agent>) => {
    set(state => {
      const agent = state.agents[id];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [id]: { ...agent, ...updates },
        },
      };
    });
  },

  setAgentPosition: (id: AgentId, x: number, y: number, facingUp?: boolean, flipped?: boolean) => {
    set(state => {
      const agent = state.agents[id];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [id]: {
            ...agent,
            x,
            y,
            ...(facingUp !== undefined ? { facingUp } : {}),
            ...(flipped !== undefined ? { flipped } : {}),
          },
        },
      };
    });
  },

  addLog: (id: AgentId, timeStr: string, message: string) => {
    set(state => {
      const agent = state.agents[id];
      if (!agent) return state;
      return {
        agents: {
          ...state.agents,
          [id]: {
            ...agent,
            log: [[timeStr, message], ...agent.log],
          },
        },
      };
    });
  },

  assignTask: (id: AgentId, task: string, timeStr: string) => {
    set(state => {
      const agent = state.agents[id];
      if (!agent) return state;

      const isPixel = id === 'pixel';
      return {
        agents: {
          ...state.agents,
          [id]: {
            ...agent,
            task,
            progress: 0,
            isBusy: true,
            statusText: isPixel ? 'Working' : agent.statusText,
            animation: isPixel ? 'idle' : agent.animation,
            log: [[timeStr, `Assigned: ${task}`], ...agent.log],
          },
        },
      };
    });
  },

  completeTask: (id: AgentId, timeStr: string, onToast?: (msg: string) => void) => {
    set(state => {
      const agent = state.agents[id];
      if (!agent) return state;

      const nextQueue = [...agent.queue];
      const nextTask = nextQueue.shift() || INITIAL_TASKS[Math.floor(Math.random() * INITIAL_TASKS.length)];
      nextQueue.push(INITIAL_TASKS[Math.floor(Math.random() * INITIAL_TASKS.length)]);

      const isPixel = id === 'pixel';
      const toastMsg = `${agent.name} completed “${agent.task}”`;
      if (onToast) onToast(toastMsg);

      return {
        completedAgentId: id,
        agents: {
          ...state.agents,
          [id]: {
            ...agent,
            progress: 0,
            isBusy: false,
            task: nextTask,
            queue: nextQueue,
            achievements: [`Task completed at ${timeStr}`, ...agent.achievements.slice(0, 4)],
            log: [[timeStr, `Completed: ${agent.task}`], ...agent.log],
            statusText: isPixel ? 'Coffee break' : agent.statusText,
            animation: isPixel ? 'coffee' : agent.animation,
            coffeeCycle: 0,
          },
        },
      };
    });
  },

  clearCompletedEffect: () => set({ completedAgentId: null }),

  advanceTaskProgress: (id: AgentId, deltaProgress: number, timeStr: string, onToast?: (msg: string) => void) => {
    const agent = get().agents[id];
    if (!agent) return;

    const nextProgress = agent.progress + deltaProgress;
    if (nextProgress >= 100) {
      get().completeTask(id, timeStr, onToast);
    } else {
      set(state => ({
        agents: {
          ...state.agents,
          [id]: {
            ...agent,
            progress: nextProgress,
          },
        },
      }));
    }
  },
}));
