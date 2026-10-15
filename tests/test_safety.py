import json,time
from concurrent.futures import ThreadPoolExecutor
import pytest
from backend.db import Store,dumps,digest

def action(store):return store.propose('workflow-1')
def approve(store,a,**kw):return store.decide(a['id'],'APPROVE',a['digest'],**kw)
def budget(store):return store.operations()['budget']['available_cents']
def stock(store):return store.operations()['inventory'][0]['on_hand']

def test_pending_no_effect(store):
 a=action(store);assert a['status']=='PENDING';assert budget(store)==500000;assert stock(store)==4;assert not store.operations()['purchase_orders']
def test_approve_exact(store):
 a=action(store);po=approve(store,a);assert po['quantity']==20;assert budget(store)==250000;assert stock(store)==4
def test_reject(store):
 a=action(store);store.decide(a['id'],'REJECT',a['digest']);assert budget(store)==500000;assert stock(store)==4
def test_no_approval_after_rejection(store):
 a=action(store);store.decide(a['id'],'REJECT',a['digest'])
 with pytest.raises(ValueError):approve(store,a)
def test_duplicate_approval(store):
 a=action(store);assert approve(store,a)==approve(store,a);assert budget(store)==250000;assert len(store.operations()['purchase_orders'])==1
def test_concurrent_approval(store):
 a=action(store)
 with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:approve(store,a),range(2)))
 assert results[0]==results[1];assert budget(store)==250000
def test_duplicate_reject(store):
 a=action(store);assert store.decide(a['id'],'REJECT',a['digest'])==store.decide(a['id'],'REJECT',a['digest'])
def test_wrong_digest(store):
 a=action(store)
 with pytest.raises(ValueError):store.decide(a['id'],'APPROVE','0'*64)
 assert budget(store)==500000
def test_expiry(store):
 a=action(store);store.execute('UPDATE actions SET expires=0')
 with pytest.raises(ValueError):approve(store,a)
def test_budget_recheck(store):
 a=action(store);store.execute('UPDATE budget SET available_cents=1')
 with pytest.raises(ValueError):approve(store,a)
 assert budget(store)==1
def test_stock_recheck(store):
 a=action(store);store.execute('UPDATE inventory SET on_hand=10')
 with pytest.raises(ValueError):approve(store,a)
def test_supplier_price_change(store):
 a=action(store);store.execute("UPDATE offers SET unit_cents=999 WHERE id='offer-a'")
 with pytest.raises(ValueError):approve(store,a)
def test_supplier_disabled(store):
 a=action(store);store.execute("UPDATE offers SET active=0 WHERE id='offer-a'")
 with pytest.raises(ValueError):approve(store,a)
def test_supplier_name_change(store):
 a=action(store);store.execute("UPDATE offers SET supplier='other' WHERE id='offer-a'")
 with pytest.raises(ValueError):approve(store,a)
def test_policy_change(store):
 a=action(store);store.update_policy(14)
 with pytest.raises(ValueError):approve(store,a)
def test_payload_tamper(store):
 a=action(store);p=json.loads(a['payload']);p['quantity']=999;store.execute('UPDATE actions SET payload=?',(dumps(p),))
 with pytest.raises(ValueError):approve(store,a)
def test_rollback(store):
 a=action(store)
 def fail():raise RuntimeError('Injected failure after budget reservation')
 with pytest.raises(RuntimeError):approve(store,a,failpoint=fail)
 assert budget(store)==500000;assert not store.operations()['purchase_orders'];assert store.one('SELECT status FROM actions')['status']=='PENDING'
def test_receive_separate(store):
 po=approve(store,action(store));assert stock(store)==4;store.receive(po['id']);assert stock(store)==24;assert budget(store)==250000
def test_duplicate_receipt(store):
 po=approve(store,action(store));assert store.receive(po['id'])==store.receive(po['id']);assert stock(store)==24
def test_missing_receipt_order(store):
 with pytest.raises(LookupError):store.receive('missing')
def test_pending_inbound_prevents_reorder(store):
 approve(store,action(store))
 with pytest.raises(ValueError):store.propose('different-workflow')
def test_low_budget_blocks_proposal(store):
 store.execute('UPDATE budget SET available_cents=100');a=action(store);assert a['status']=='BLOCKED'
 with pytest.raises(ValueError):approve(store,a)
def test_invalid_decision(store):
 a=action(store)
 with pytest.raises(ValueError):store.decide(a['id'],'yes',a['digest'])
def test_restart_decision(store):
 a=action(store);second=Store(store.path);approve(second,a);assert budget(store)==250000

def test_reset_invalidates_pending(store):
 a=action(store);v=store.version();store.reset();assert store.version()>v
 with pytest.raises(ValueError):approve(store,a)
def test_idempotent_proposal(store):assert action(store)['id']==action(store)['id']
def test_unknown_sku(store):
 with pytest.raises(ValueError):store.propose('w','unknown')
def test_no_supplier(store):
 store.execute('UPDATE offers SET active=0')
 with pytest.raises(ValueError):action(store)

def test_old_approval_invalid_after_reset(store):
 a=action(store);approve(store,a);store.reset()
 with pytest.raises(ValueError):approve(store,a)
