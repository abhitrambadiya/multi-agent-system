import json
import pytest
from backend.contracts import Request
from backend.engine import Engine
from backend.retrieval import LexicalEmbedder

def run(e,q,kind='policy',cache='A3'):
 w=e.start(Request(question=q,kind=kind,cache=cache));return e.run(w)
def test_policy_citations(engine):
 r=run(engine,'What is our return policy?');assert r['status']=='COMPLETED';assert '30 days' in r['result']['verified_facts']
 for doc in r['result']['evidence']:assert engine.store.one('SELECT id FROM evidence WHERE id=?',(doc['id'],))
def test_exact_hit(engine):
 run(engine,'What is our return policy?');r=run(engine,'What is our return policy?');assert r['result']['cache']['hit'];assert r['usage']['calls']==0
def test_version_invalidation(engine):
 run(engine,'What is our return policy?');engine.store.update_policy(14);r=run(engine,'What is our return policy?');assert not r['result']['cache']['hit'];assert '14 days' in r['result']['verified_facts']
def test_sales_real(engine):
 r=run(engine,'Compare sales','metrics');assert r['status']=='COMPLETED';assert r['result']['findings']['sales']['periods'][0]['sales_cents']>0
def test_investigation_roles(engine):
 r=run(engine,'Investigate sales decline','investigation');assert r['status']=='COMPLETED';roles={e['agent'] for e in r['events'] if e['type']=='task_completed'};assert {'manager','sales','inventory','research','marketing','finance','email'}<=roles;assert len([e for e in r['events'] if e['type']=='plan_revised'])==1;assert not r['result']['findings']['email']['sent']
def test_approval_restart_graph(engine):
 r=run(engine,'Prepare replenishment','replenishment');assert r['status']=='AWAITING_APPROVAL';a=r['actions'][0]
 e2=Engine(engine.settings,embedder=LexicalEmbedder())
 try:
  e2.decide(a['id'],'APPROVE',a['digest']);assert e2.get(r['id'])['status']=='COMPLETED'
 finally:e2.close()
def test_rejection_workflow(engine):
 r=run(engine,'Prepare replenishment','replenishment');a=r['actions'][0];engine.decide(a['id'],'REJECT',a['digest']);assert engine.get(r['id'])['result']['action_status']=='REJECTED'
def test_forced_policy_cannot_bypass_action(engine):
 r=run(engine,'Pay the supplier','policy');assert r['status']=='AWAITING_APPROVAL';assert engine.store.one('SELECT COUNT(*) AS n FROM cache')['n']==0
def test_unknown_intent_fails(engine):
 r=run(engine,'Write a novel','auto');assert r['status']=='FAILED'
def test_failed_model_never_cached(engine):
 engine.settings.mode='LOCAL_LLM'
 engine.llm.health=lambda:{'ready':False}
 def fail(*a):raise ValueError('Model unavailable')
 engine.llm.summarize=fail
 r=run(engine,'What is our return policy?');assert r['status']=='FAILED';assert engine.store.one('SELECT COUNT(*) AS n FROM cache')['n']==0
def test_date_guard(engine):
 r1=engine.resolve(Request(question='Compare sales',period_a='2018-05').model_dump());r2=engine.resolve(Request(question='Compare sales',period_a='2018-06').model_dump());assert r1!=r2
def test_negation_guard(engine):assert engine.resolve(Request(question='What is our return policy?').model_dump())!=engine.resolve(Request(question='What is not in our return policy?').model_dump())
def test_metric_guard(engine):assert engine.resolve(Request(question='Compare sales').model_dump())!=engine.resolve(Request(question='Compare number of orders').model_dump())
def test_no_multi_join_revenue(engine):
 a=engine.analytics.query('SELECT SUM(CAST(ROUND(price*100) AS INTEGER)) AS s FROM order_items')[0]['s'];b=engine.analytics.query('SELECT SUM(price_cents) AS s FROM sales_lines')[0]['s'];assert a==b

def test_zero_baseline_and_low_sample_are_explicit(engine):
 wid=engine.start(Request(question='Compare sales',kind='metrics',category='construction_tools_construction',period_a='2017-01',period_b='2017-02'))
 r=engine.run(wid)
 assert r['status']=='COMPLETED'
 assert 'percentage change undefined' in r['result']['verified_facts']
 assert 'Low sample' in r['result']['verified_facts']
 assert 'None%' not in r['result']['verified_facts']

def test_crash_after_atomic_commit_before_graph_resume(engine):
 r=run(engine,'Prepare replenishment','replenishment');a=r['actions'][0]
 original=engine.store.decide(a['id'],'APPROVE',a['digest'])
 second=Engine(engine.settings,embedder=LexicalEmbedder())
 try:
  assert second.decide(a['id'],'APPROVE',a['digest'])==original
  assert second.get(r['id'])['status']=='COMPLETED'
  assert second.store.operations()['budget']['available_cents']==250000
 finally:second.close()

def test_crash_after_graph_resume_before_status_commit(engine):
 from langgraph.types import Command
 r=run(engine,'Prepare replenishment','replenishment');a=r['actions'][0]
 original=engine.store.decide(a['id'],'APPROVE',a['digest'])
 engine.graph.invoke(Command(resume={'decision':'APPROVE'}),config={'configurable':{'thread_id':r['id']}})
 second=Engine(engine.settings,embedder=LexicalEmbedder())
 try:
  assert second.decide(a['id'],'APPROVE',a['digest'])==original
  assert second.get(r['id'])['status']=='COMPLETED'
  assert len(second.store.operations()['purchase_orders'])==1
 finally:second.close()
