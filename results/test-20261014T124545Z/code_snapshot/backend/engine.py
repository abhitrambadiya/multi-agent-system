"""Bounded LangGraph departments, durable decisions, and replayable events."""
import json, re, sqlite3, time
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command
from .db import Store,dumps,uid,digest
from .analytics import Analytics
from .retrieval import Retriever,Embedder,LexicalEmbedder,POLICIES
from .cache import AnswerCache
from .llm import LocalModel
from .contracts import Request

class State(TypedDict,total=False):
    wid:str
    request:dict
    scope:dict
    evidence:list
    findings:dict
    action:dict
    result:dict
    cache_info:dict
    hit:bool

ROLE_NAMES={'manager':'Sage','sales':'Nova','research':'Atlas','inventory':'Pixel','marketing':'Mira','procurement':'Rowan','finance':'Ledger','email':'Echo'}

class Engine:
    def __init__(self,settings,embedder=None):
        self.settings=settings; self.store=Store(settings.db); self.analytics=Analytics(settings.analytics)
        self.embedder=embedder or (Embedder(settings.models) if settings.models.exists() and (settings.models/'modules.json').exists() else LexicalEmbedder())
        self.embedding_mode='MINILM' if isinstance(self.embedder,Embedder) else 'LEXICAL_FALLBACK'
        self.retriever=Retriever(self.store,self.analytics,self.embedder)
        self.cache=AnswerCache(self.store,self.embedder,settings.threshold); self.llm=LocalModel(settings,self.store)
        self.checkpoint_conn=sqlite3.connect(str(settings.db)+'.checkpoints',check_same_thread=False)
        self.checkpointer=SqliteSaver(self.checkpoint_conn)
        graph=StateGraph(State)
        for name in ['manager','sales','inventory','research','marketing','finance','email','synthesis','procurement','approval','finish_purchase']:
            graph.add_node(name,getattr(self,name))
        graph.add_edge(START,'manager')
        graph.add_conditional_edges('manager',lambda s:'cached' if s.get('hit') else s['scope']['kind'],{'cached':END,'investigation':'sales','metrics':'sales','policy':'research','replenishment':'inventory'})
        graph.add_conditional_edges('sales',lambda s:s['scope']['kind'],{'metrics':'synthesis','investigation':'inventory'})
        graph.add_conditional_edges('inventory',lambda s:s['scope']['kind'],{'investigation':'research','replenishment':'procurement'})
        graph.add_conditional_edges('research',lambda s:s['scope']['kind'],{'policy':'synthesis','investigation':'marketing'})
        graph.add_edge('marketing','finance');graph.add_edge('finance','email');graph.add_edge('email','synthesis');graph.add_edge('synthesis',END)
        graph.add_edge('procurement','approval');graph.add_edge('approval','finish_purchase');graph.add_edge('finish_purchase',END)
        self.graph=graph.compile(checkpointer=self.checkpointer)

    def close(self): self.checkpoint_conn.close()
    def event(self,s,agent,kind,payload): self.store.event(s['wid'],agent,kind,payload)
    def task(self,s,role,title,fn):
        self.event(s,role,'task_started',{'title':title})
        try: result=fn()
        except Exception as e:
            self.event(s,role,'task_failed',{'error':str(e)});raise
        self.event(s,role,'task_completed',{'title':title,'output':result})
        return result

    def resolve(self,r):
        q=r['question'].lower();kind=r['kind']
        # Actions always bypass cache, regardless of client-selected kind.
        action=bool(re.search(r'\b(pay|purchase|buy|replenish|replenishment|order supplies|refund|send email|send the email)\b',q))
        if action:
            if re.search(r'\b(refund|send email|send the email)\b',q): raise ValueError('Only simulated chair replenishment is supported. Email drafts never send.')
            kind='replenishment'
        if kind=='auto':
            if any(x in q for x in ['policy','return','eligible','approval','receipt','discount','budget','currency','supplier','forecast','privacy','campaign','cancellation','cache','inventory','evidence','email']): kind='policy'
            elif any(x in q for x in ['why','investigate','low','declin']): kind='investigation'
            elif any(x in q for x in ['sales','compare','revenue','orders']): kind='metrics'
            else: raise ValueError('Choose sales comparison, investigation, policy question, or simulated replenishment.')
        topic='returns'
        aliases={'returns':['return','eligible'],'purchasing':['purchasing','approval','approve','payment'],'delivery':['delivery','receipt','inbound'],'discounts':['discount'],'privacy':['privacy','anonym'],'budget':['budget'],'cache':['cache','reuse'],'campaign':['campaign','conversion'],'quality':['quality','review'],'cancellation':['cancel'],'currency':['currency','brl'],'suppliers':['supplier'],'forecast':['forecast'],'email':['email'],'evidence':['evidence','citation'],'inventory':['inventory','replenishment formula']}
        matched=[k for k,terms in aliases.items() if any(x in q for x in terms)]
        if matched: topic=matched[0]
        elif kind=='policy': raise ValueError('Specify a policy topic, such as returns, budget, delivery or privacy.')
        dates=re.findall(r'\b20\d{2}-\d{2}\b',q)
        if len(dates)==2: r={**r,'period_a':dates[0],'period_b':dates[1]}
        elif dates and kind in {'metrics','investigation'}: raise ValueError('Specify exactly two YYYY-MM comparison periods.')
        # Detect explicit category names in free text, otherwise use visible form scope.
        if kind in {'metrics','investigation'}:
            for cat in self.analytics.categories():
                if cat['category'] in q: r={**r,'category':cat['category']};break
        numbers=re.findall(r'\b\d+(?:\.\d+)?\b',q)
        negation=bool(re.search(r"\b(not|never|without|exclude|except|no)\b|n't",q))
        metric='orders' if re.search(r'\border count|number of orders\b',q) else 'sales'
        # Complex multi-topic queries get exact-only caching; critical literals cannot disappear.
        scope={'kind':kind,'topic':topic if kind=='policy' else None,'category':r['category'] if kind!='policy' else None,'period_a':r['period_a'] if kind in {'metrics','investigation'} else None,'period_b':r['period_b'] if kind in {'metrics','investigation'} else None,'sku':r['sku'] if kind=='replenishment' else None,'numbers':numbers,'negation':negation,'metric':metric,'topics':sorted(matched) if len(matched)>1 else [],'workspace':'local-demo','permissions':'owner-read','output':'summary-v1'}
        # Preserve unrecognized qualifiers so similarity alone cannot erase conditions.
        generic=set('what is are our the a an how long do does can customers customer have to for of in on about explain describe summarize tell me please policy rules rule policyname goods items item product products eligible unused within window days return returns work works sales revenue compare comparison value number orders order count change changed why investigate investigation and suggest propose plan between from versus vs period periods historical delivered category findings business show provide summary overview latest current simulated purchase purchasing approval approve payment delivery receipt inbound discount discounts privacy anonymized budget cache reuse campaign conversion quality review reviews cancel cancellation currency brl supplier suppliers forecast email evidence citation inventory replenishment formula'.split())
        remaining=re.sub(r'20\d{2}-\d{2}', '',q)
        if kind in {'metrics','investigation'}: remaining=remaining.replace(r['category'],'')
        scope['qualifiers']=sorted(set(re.findall(r'\b[a-z]+\b',remaining))-generic)
        if kind=='policy': scope['category']=None
        return scope

    def snapshot(self):
        return {'business':self.store.version(),'dataset':self.analytics.manifest()['archive_sha256'],'model':self.settings.model,'digest':self.llm.model_digest,'mode':self.settings.mode,'prompt':'v2-money-guard','embedding':self.embedding_mode}

    def start(self,request):
        r=request.model_dump() if isinstance(request,Request) else request
        wid=uid();self.store.execute('INSERT INTO workflows(id,request,status,created) VALUES(?,?,?,?)',(wid,dumps(r),'QUEUED',time.time()))
        return wid
    def run(self,wid,arm=None):
        row=self.store.one('SELECT * FROM workflows WHERE id=?',(wid,))
        if not row: raise LookupError('Workflow not found')
        r=json.loads(row['request'])
        if arm: r['cache']=arm
        self.store.execute("UPDATE workflows SET status='RUNNING' WHERE id=?",(wid,))
        try:
            result=self.graph.invoke({'wid':wid,'request':r,'evidence':[],'findings':{}},config={'configurable':{'thread_id':wid},'recursion_limit':20})
            if result.get('__interrupt__'):
                self.store.execute("UPDATE workflows SET status='AWAITING_APPROVAL',result=? WHERE id=?",(dumps({'action':result['action'],'findings':result['findings']}),wid))
            else:
                final=result.get('result',{})
                self.store.execute("UPDATE workflows SET status='COMPLETED',result=? WHERE id=?",(dumps(final),wid))
                self.store.event(wid,'manager','workflow_completed',{'cache':result.get('cache_info',{})})
        except Exception as e:
            self.store.execute("UPDATE workflows SET status='FAILED',error=? WHERE id=?",(str(e)[:1000],wid))
            self.store.event(wid,'manager','workflow_failed',{'error':str(e)[:1000]})
        return self.get(wid)

    def get(self,wid):
        row=self.store.one('SELECT * FROM workflows WHERE id=?',(wid,))
        if not row: raise LookupError('Workflow not found')
        row['request']=json.loads(row['request']);row['result']=json.loads(row['result']) if row['result'] else None
        row['events']=self.store.rows('SELECT * FROM events WHERE workflow_id=? ORDER BY seq',(wid,))
        for e in row['events']: e['payload']=json.loads(e['payload'])
        row['actions']=self.store.rows('SELECT * FROM actions WHERE workflow_id=?',(wid,))
        for a in row['actions']: a['payload']=json.loads(a['payload'])
        row['usage']=self.store.one('SELECT COUNT(*) AS calls,COALESCE(SUM(input_tokens),0) AS input_tokens,COALESCE(SUM(output_tokens),0) AS output_tokens,COALESCE(SUM(duration_ms),0) AS duration_ms FROM invocations WHERE workflow_id=?',(wid,))
        return row

    def manager(self,s):
        scope=self.task(s,'manager','Resolve request and delegate specialists',lambda:self.resolve(s['request']))
        if self.settings.mode=='LOCAL_LLM': self.llm.health()
        hit=None;info={'hit':False,'reason':'financial actions bypass answer reuse'}
        if scope['kind']!='replenishment':
            hit,info=self.cache.lookup(s['request']['question'],scope,self.snapshot(),s['request']['cache'])
        self.event(s,'manager','cache_hit' if hit else 'cache_rejected',info)
        return {'scope':scope,'hit':hit is not None,'cache_info':info,**({'result':{**hit,'cache':info}} if hit else {})}

    def sales(self,s):
        scope=s['scope']; metrics=self.task(s,'sales','Compare historical delivered sales',lambda:self.analytics.compare(scope['category'],scope['period_a'],scope['period_b']))
        ev=self.store.evidence('REAL_PUBLIC',f"metrics/{scope['category']}/{scope['period_a']}/{scope['period_b']}",self.analytics.manifest()['archive_sha256'][:12],dumps(metrics))
        self.event(s,'sales','evidence_found',ev)
        return {'findings':{**s['findings'],'sales':metrics},'evidence':s['evidence']+[ev]}

    def inventory(self,s):
        ops=self.store.operations();stock=ops['inventory'][0]
        inbound=sum(po['quantity'] for po in ops['purchase_orders'] if po['status']=='ORDERED' and po['sku']==stock['sku'])
        result=self.task(s,'inventory','Check simulated stock and pending deliveries',lambda:{'source':'SIMULATED','sku':stock['sku'],'on_hand':stock['on_hand'],'inbound':inbound,'target':stock['target'],'shortfall':max(0,stock['target']-stock['on_hand']-inbound),'limitation':'Simulation is not evidence of historical Olist stockouts.'})
        ev=self.store.evidence('SIMULATED','inventory/DEMO-CHAIR',ops['version'],dumps(result))
        self.event(s,'inventory','evidence_found',ev)
        return {'findings':{**s['findings'],'inventory':result},'evidence':s['evidence']+[ev]}

    def research(self,s):
        docs=self.task(s,'research','Retrieve policy and order-level feedback',lambda:self.retriever.search(s['request']['question'],s['scope'].get('category') or s['request']['category'],s['scope']['topic'] if s['scope']['kind']=='policy' else 'quality'))
        for doc in docs:self.event(s,'research','evidence_found',doc)
        return {'evidence':s['evidence']+docs,'findings':{**s['findings'],'research':{'citations':[d['id'] for d in docs],'limitation':'Reviews are sampled order-level reports; causation is unproven.'}}}

    def marketing(self,s):
        # Explicit counterproposal and one bounded revision make collaboration inspectable.
        inv=s['findings']['inventory']
        proposal='Consider a discount campaign, subject to margin and stock checks.'
        challenge='Inventory challenges a discount on scarce stock.' if inv['shortfall'] else 'Inventory reports adequate stock or pending replenishment.'
        revision='Prioritize replenishment; promote available alternatives. Measure delivered sales next period.' if inv['shortfall'] else 'Review margins before offering any discount; monitor next-period sales.'
        result=self.task(s,'marketing','Propose campaign and request Inventory review',lambda:{'proposal':proposal,'challenge':challenge,'revised_plan':revision,'source':'SIMULATED','followups':1})
        self.event(s,'inventory','agent_message',{'to':'marketing','message':challenge})
        self.event(s,'manager','plan_revised',{'reason':challenge,'plan':revision,'followup_limit':1})
        return {'findings':{**s['findings'],'marketing':result}}

    def finance(self,s):
        budget=self.store.operations()['budget']['available_cents']
        result=self.task(s,'finance','Check affordability and approval boundary',lambda:{'available_cents':budget,'currency':'BRL','source':'SIMULATED','decision':'A separate owner approval is required before any purchase or discount commitment. The listed budget is available.', 'discount_limitation':'Profit margin is unknown, so discount profitability cannot be evaluated.'})
        ev=self.store.evidence('SIMULATED','budget/current',self.store.version(),dumps(result))
        return {'findings':{**s['findings'],'finance':result},'evidence':s['evidence']+[ev]}

    def email(self,s):
        draft=self.task(s,'email','Draft an internal owner update',lambda:{'status':'DRAFT_ONLY','subject':'Sales investigation and proposed next steps','body':s['findings']['marketing']['revised_plan']+' Please review the evidence and any separate purchase proposal.','sent':False})
        return {'findings':{**s['findings'],'email':draft}}

    def synthesis(self,s):
        scope=s['scope']
        if scope['kind']=='policy':
            days=self.store.operations()['return_days'];template=POLICIES[scope['topic']].format(days=days)
        else:
            m=s['findings']['sales'];a,b=m['periods']
            template=f"Delivered product sales for {m['category']} were BRL {a['sales_cents']/100:,.2f} in {a['period']} and BRL {b['sales_cents']/100:,.2f} in {b['period']} ({m['delta_pct']}% change). Order counts: {a['orders']} and {b['orders']}. Historical comparison does not establish why sales changed."
            if scope['kind']=='investigation':template+=' '+s['findings']['marketing']['revised_plan']+' Stock and campaign information is simulated; margin data is unavailable.'
        generation=self.task(s,'manager','Synthesize grounded findings',lambda:self.llm.summarize(s['wid'],'manager',s['request']['question'],s['evidence'],template))
        result={**generation,'verified_facts':template,'findings':s['findings'],'evidence':s['evidence'],'scope':scope,'cache':s['cache_info'],'snapshot':self.snapshot(),'embedding_mode':self.embedding_mode,'action_owners':[{'role':'inventory','action':'Review replenishment proposal','kpi':'Stock shortfall'},{'role':'sales','action':'Monitor next complete period','kpi':'Delivered product sales'}] if scope['kind']=='investigation' else []}
        if s['request']['cache']!='A0':self.cache.put(s['request']['question'],scope,self.snapshot(),result)
        return {'result':result}

    def procurement(self,s):
        action=self.task(s,'procurement','Rank active offers and prepare exact purchase proposal',lambda:self.store.propose(s['wid'],s['scope']['sku']))
        payload=json.loads(action['payload']);action={**action,'payload':payload}
        self.task(s,'finance','Validate budget; require owner approval at every amount',lambda:{'status':action['status'],'total_cents':payload['total_cents'],'currency':'BRL','owner_approval_required':True})
        if action['status']=='BLOCKED': raise ValueError('Purchase blocked by budget or policy ceiling')
        self.event(s,'manager','approval_required',action)
        return {'action':action}

    def approval(self,s):
        # Nothing before interrupt mutates state; graph replay is safe.
        interrupt({'action_id':s['action']['id'],'digest':s['action']['digest']})
        return {}

    def finish_purchase(self,s):
        action=self.store.one('SELECT * FROM actions WHERE id=?',(s['action']['id'],))
        if action['status'] not in {'EXECUTED','REJECTED'}:raise ValueError('No persisted owner decision')
        po=self.store.one('SELECT * FROM purchase_orders WHERE action_id=?',(action['id'],))
        return {'result':{'summary':'Simulated purchase ordered; delivery has not been received.' if po else 'Owner rejected the proposal. No funds or stock changed.','mode':'DETERMINISTIC','action_status':action['status'],'purchase_order':po,'evidence':s['evidence'],'findings':s['findings'],'cache':{'hit':False,'reason':'financial actions bypass answer reuse'}}}

    def decide(self,aid,decision,expected_digest):
        action=self.store.one('SELECT * FROM actions WHERE id=?',(aid,))
        if not action:raise LookupError('Action not found')
        wid=action['workflow_id'];workflow=self.get(wid)
        if workflow['status']=='COMPLETED':return self.store.decide(aid,decision,expected_digest)
        if workflow['status']!='AWAITING_APPROVAL':raise ValueError('Workflow is not awaiting approval')
        receipt=self.store.decide(aid,decision,expected_digest)
        # The atomic purchase is durable before graph continuation. Retry cannot double-spend.
        result=self.graph.invoke(Command(resume={'decision':decision}),config={'configurable':{'thread_id':wid}})
        self.store.execute("UPDATE workflows SET status='COMPLETED',result=? WHERE id=?",(dumps(result['result']),wid))
        self.store.event(wid,'finance','action_executed' if decision=='APPROVE' else 'action_rejected',receipt)
        return receipt
