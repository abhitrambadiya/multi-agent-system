import {create} from 'zustand';
import {Agent,AgentId} from '../types/agent';
import {INITIAL_AGENTS} from '../constants/initialAgents';
const ids: Record<string,AgentId>={manager:'sage',sales:'nova',research:'atlas',inventory:'pixel',email:'echo',finance:'ledger',procurement:'rowan',marketing:'mira'};
interface AgentStore {agents:Record<string,Agent>;selectedAgentId:AgentId;completedAgentId:AgentId|null;selectAgent:(id:AgentId)=>void;sync:(events:any[])=>void}
export const useAgentStore=create<AgentStore>(set=>({agents:INITIAL_AGENTS,selectedAgentId:'sage',completedAgentId:null,selectAgent:id=>set({selectedAgentId:id}),sync:events=>{
 const agents=Object.fromEntries(Object.entries(INITIAL_AGENTS).map(([id,a])=>[id,{...a,log:[] as [string,string][],state:'IDLE' as Agent['state'],animation:'idle' as Agent['animation'],statusText:'Ready',task:'Awaiting assignment',progress:0}]));
 for(const e of events){const id=ids[e.agent];if(!id)continue;const a=agents[id];if(e.type==='task_started'){a.task=e.payload.title;a.statusText='Working';a.state='WORKING';a.animation='type';a.progress=0;}
 if(e.type==='task_completed'){a.statusText='Complete';a.state='TASK_COMPLETE';a.animation='idle';a.progress=100;}
 if(e.type==='task_failed'){a.statusText='Failed';a.state='IDLE';a.animation='idle';}
 a.log.unshift([new Date(e.created*1000).toLocaleTimeString(),e.payload.title||e.payload.message||e.type.replace(/_/g,' ')]);}
 set({agents});}}));
