import httpx,pytest
from backend.llm import LocalModel
from backend.config import Settings
from backend.db import dumps

class FakeResponse:
 def __init__(self,payload):self.payload=payload
 def raise_for_status(self):pass
 def json(self):return self.payload
class FakeClient:
 payload={}
 def __init__(self,*a,**k):pass
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def post(self,*a,**k):return FakeResponse(self.payload)

@pytest.mark.parametrize('response,status',[(dumps({'summary':'Grounded','citations':['e1'],'limitations':[]}), 'OK'),('{broken','FAILED'),(dumps({'summary':'Wrong','citations':['invented'],'limitations':[]}), 'FAILED')])
def test_model_validation_and_usage(store,monkeypatch,response,status):
 FakeClient.payload={'response':response,'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':10,'load_duration':1000000};monkeypatch.setattr(httpx,'Client',FakeClient)
 llm=LocalModel(Settings(),store)
 if status=='FAILED':
  with pytest.raises(ValueError):llm.summarize('w','manager','q',[{'id':'e1','source':'TEST','text':'a'}],'fact')
 else:assert llm.summarize('w','manager','q',[{'id':'e1','source':'TEST','text':'a'}],'fact')['mode']=='LOCAL_LLM'
 row=store.one('SELECT * FROM invocations');assert row['status']==status;assert row['input_tokens']==20;assert row['output_tokens']==10

def test_template_does_not_fake_usage(store):
 llm=LocalModel(Settings(mode='TEMPLATE'),store);assert llm.summarize('w','manager','q',[],'fact')['mode']=='TEMPLATE';assert not store.rows('SELECT * FROM invocations')

def test_money_unit_guard_rejects_centavos_as_reais(store,monkeypatch):
 FakeClient.payload={'response':dumps({'summary':'Sales were BRL 4,204,222','citations':['e1'],'limitations':[]}), 'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':10}
 monkeypatch.setattr(httpx,'Client',FakeClient)
 with pytest.raises(ValueError):LocalModel(Settings(),store).summarize('w','manager','sales',[{'id':'e1','source':'REAL_PUBLIC','text':'{"sales_cents":4204222}'}],'Sales were BRL 42,042.22')
 assert len(store.rows('SELECT * FROM invocations'))==2
 assert all(r['status']=='FAILED' for r in store.rows('SELECT * FROM invocations'))

def test_money_preparation():
 from backend.llm import prepare_text
 assert 'BRL 42,042.22' in prepare_text('{"sales_cents":4204222,"orders":316}')

def test_incorrect_approval_reason_is_rejected(store,monkeypatch):
 FakeClient.payload={'response':dumps({'summary':'No spending authorized due to unavailable margin data.','citations':['e1'],'limitations':[]}), 'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':10}
 monkeypatch.setattr(httpx,'Client',FakeClient)
 with pytest.raises(ValueError):LocalModel(Settings(),store).summarize('w','manager','q',[{'id':'e1','source':'TEST','text':'Owner approval required.'}],'Owner approval required.')

@pytest.mark.parametrize('summary,rejected',[
 ('Simulation indicates stock levels are sufficient (4 units on hand).',True),
 ('There is adequate stock.',True),
 ('Simulated stock is insufficient against target.',False),
])
def test_inventory_contradiction_guard(store,monkeypatch,summary,rejected):
 FakeClient.payload={'response':dumps({'summary':summary,'citations':['e1'],'limitations':[]}), 'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':10}
 monkeypatch.setattr(httpx,'Client',FakeClient)
 llm=LocalModel(Settings(),store)
 evidence=[{'id':'e1','source':'SIMULATED','text':dumps({'on_hand':4,'target':24,'shortfall':20})}]
 if rejected:
  with pytest.raises(ValueError,match='shortfall'):llm.summarize('w','manager','q',evidence,'Prioritize replenishment.')
  assert all(r['status']=='FAILED' for r in store.rows('SELECT * FROM invocations'))
 else:assert llm.summarize('w','manager','q',evidence,'Prioritize replenishment.')['summary']==summary

@pytest.mark.parametrize('amount,accepted',[('11,664.23',True),('12,000.00',False)])
def test_negative_delta_can_be_expressed_as_decrease_magnitude(store,monkeypatch,amount,accepted):
 FakeClient.payload={'response':dumps({'summary':f'Sales decreased by BRL {amount}.','citations':['e1'],'limitations':[]}), 'done':True,'done_reason':'stop','prompt_eval_count':20,'eval_count':10}
 monkeypatch.setattr(httpx,'Client',FakeClient)
 llm=LocalModel(Settings(),store);evidence=[{'id':'e1','source':'REAL_PUBLIC','text':'Change: BRL -11,664.23'}]
 if accepted:assert llm.summarize('w','manager','q',evidence,'Change: BRL -11,664.23')['mode']=='LOCAL_LLM'
 else:
  with pytest.raises(ValueError,match='Unsupported monetary'):llm.summarize('w','manager','q',evidence,'Change: BRL -11,664.23')
