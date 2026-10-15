export type AgentId = 'atlas' | 'nova' | 'echo' | 'sage' | 'pixel' | 'ledger' | 'rowan' | 'mira';

export type AgentAnimation = 'type' | 'walk' | 'idle' | 'coffee';

export type AgentState =
  | 'IDLE'
  | 'WALKING'
  | 'WORKING'
  | 'BREAK'
  | 'MEETING'
  | 'TASK_COMPLETE';

export interface Agent {
  id: AgentId;
  name: string;
  role: string;
  color: string;
  x: number;
  y: number;
  targetX?: number;
  targetY?: number;
  animation: AgentAnimation;
  seated?: boolean;
  facingUp?: boolean;
  flipped?: boolean;
  statusText: string;
  state: AgentState;
  task: string;
  queue: string[];
  progress: number; // 0 to 100
  achievements: string[];
  log: [string, string][]; // [timestamp, message]
  outfit: [string, string, string]; // [top, pants, hair]
  accessoryType: 'glasses' | 'flower' | 'scarf' | 'tie' | 'headphones';
  hasMug?: boolean;
  isBusy?: boolean;
  coffeeCycle?: number;
  workstation: { x: number; y: number };
}

export interface TaskDefinition {
  id: string;
  title: string;
  description?: string;
  category?: string;
}

export interface Waypoint {
  x: number;
  y: number;
  name?: string;
}
