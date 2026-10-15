import {Agent, AgentId} from '../types/agent';

function agent(id:AgentId,name:string,role:string,color:string,x:number,y:number,outfit:Agent['outfit'],accessoryType:Agent['accessoryType']):Agent {
 return {id,name,role,color,x,y,workstation:{x,y},outfit,accessoryType,
   animation:'idle',state:'IDLE',statusText:'Ready',task:'Awaiting assignment',
   queue:[],progress:0,achievements:[],log:[],isBusy:false,seated:true};
}

// Appearance is adapted from the reference. Work state is supplied only by backend events.
export const INITIAL_AGENTS:Record<AgentId,Agent>={
 atlas:agent('atlas','Atlas','Research','#6ea8ff',125,141,['#34476f','#1d2433','#3a2a22'],'glasses'),
 nova:agent('nova','Nova','Sales','#4cc38a',655,171,['#2f7d6b','#1e2a33','#c4527a'],'flower'),
 echo:agent('echo','Echo','Email','#e5a64f',330,141,['#c9843b','#2a2630','#e8c06a'],'scarf'),
 sage:agent('sage','Sage','Manager','#a995ff',1015,181,['#4a3f86','#25222f','#cfcfd6'],'tie'),
 pixel:agent('pixel','Pixel','Inventory','#ef7f93',475,141,['#a8445a','#242833','#2d3a66'],'headphones'),
 ledger:agent('ledger','Ledger','Finance','#67c9be',300,270,['#346f65','#1d2433','#bda17f'],'tie'),
 rowan:agent('rowan','Rowan','Procurement','#dca575',475,270,['#8d684b','#292333','#463b2c'],'glasses'),
 mira:agent('mira','Mira','Marketing','#b99fea',785,275,['#6d558c','#25222f','#b48560'],'flower'),
};
