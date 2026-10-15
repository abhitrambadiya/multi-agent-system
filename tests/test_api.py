import time
from fastapi.testclient import TestClient
from backend.main import create_app

def test_api_journey(engine):
 with TestClient(create_app(engine.settings,engine)) as c:
  token=c.get('/api/session').json()['owner_token'];headers={'X-Owner-Token':token}
  assert c.post('/api/workflows',json={'question':'Pay supplier'}).status_code==403
  assert c.post('/api/workflows',headers={**headers,'Origin':'https://evil.example'},json={'question':'Pay supplier'}).status_code==403
  assert c.get('/api/workflows/missing').status_code==404
  assert c.get('/api/evidence/missing').status_code==404
  r=c.post('/api/workflows',headers=headers,json={'question':'Prepare replenishment','kind':'replenishment'});assert r.status_code==202
  wid=r.json()['id']
  for _ in range(100):
   w=c.get('/api/workflows/'+wid).json()
   if w['status']=='AWAITING_APPROVAL':break
   time.sleep(.03)
  assert w['status']=='AWAITING_APPROVAL'
  stream=c.get(f'/api/workflows/{wid}/events');assert 'approval_required' in stream.text
  last=w['events'][-1]['seq'];assert 'id:' not in c.get(f'/api/workflows/{wid}/events',headers={'Last-Event-ID':str(last)}).text
  a=w['actions'][0]
  assert c.post('/api/actions/'+a['id']+'/decision',headers=headers,json={'decision':'YES','digest':a['digest']}).status_code==422
  r=c.post('/api/actions/'+a['id']+'/decision',headers=headers,json={'decision':'APPROVE','digest':a['digest']});assert r.status_code==200
  assert c.post('/api/actions/'+a['id']+'/decision',headers=headers,json={'decision':'APPROVE','digest':a['digest']}).json()==r.json()
  assert c.post('/api/demo/reset?workspace=wrong',headers=headers,json={}).status_code==409

def test_production_rejects_unsafe_cache_arm(engine):
 with TestClient(create_app(engine.settings,engine)) as c:
  h={'X-Owner-Token':c.get('/api/session').json()['owner_token']}
  assert c.post('/api/workflows',headers=h,json={'question':'Return policy','cache':'A2'}).status_code==422

def test_wrong_host_rejected(engine):
 with TestClient(create_app(engine.settings,engine)) as c:
  assert c.get('/api/session',headers={'Host':'evil.example'}).status_code==403

def test_invalid_policy_bounds(engine):
 with TestClient(create_app(engine.settings,engine)) as c:
  h={'X-Owner-Token':c.get('/api/session').json()['owner_token']}
  assert c.post('/api/demo/policy',headers=h,json={'days':0}).status_code==422
  assert c.post('/api/demo/policy',headers=h,json={'days':999}).status_code==422
