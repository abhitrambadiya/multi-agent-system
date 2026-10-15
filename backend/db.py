"""Local SQLite authority. Money is always integer BRL centavos."""
import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def uid(): return uuid.uuid4().hex

def dumps(value): return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def digest(value): return hashlib.sha256(dumps(value).encode()).hexdigest()

SCHEMA = '''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS inventory(sku TEXT PRIMARY KEY, name TEXT, on_hand INTEGER NOT NULL CHECK(on_hand>=0), target INTEGER NOT NULL CHECK(target>0));
CREATE TABLE IF NOT EXISTS offers(id TEXT PRIMARY KEY, sku TEXT, supplier TEXT, unit_cents INTEGER NOT NULL CHECK(unit_cents>0), lead_days INTEGER, active INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY CHECK(id=1), available_cents INTEGER NOT NULL CHECK(available_cents>=0));
CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY, request TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created REAL NOT NULL, error TEXT);
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT NOT NULL, agent TEXT NOT NULL, type TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS event_workflow ON events(workflow_id,seq);
CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, payload TEXT NOT NULL, digest TEXT NOT NULL, snapshot INTEGER NOT NULL, expires REAL NOT NULL, status TEXT NOT NULL, decision TEXT);
CREATE TABLE IF NOT EXISTS purchase_orders(id TEXT PRIMARY KEY, action_id TEXT UNIQUE NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), total_cents INTEGER NOT NULL CHECK(total_cents>0), status TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, po_id TEXT UNIQUE NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, source TEXT NOT NULL, locator TEXT NOT NULL, version TEXT NOT NULL, text TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cache(id TEXT PRIMARY KEY, query TEXT, vector TEXT, scope TEXT, snapshot TEXT, result TEXT, created REAL);
CREATE TABLE IF NOT EXISTS invocations(id TEXT PRIMARY KEY, workflow_id TEXT, role TEXT, mode TEXT, model TEXT, model_digest TEXT, prompt_hash TEXT, snapshot TEXT, input_tokens INTEGER, output_tokens INTEGER, duration_ms REAL, load_ms REAL, status TEXT, error TEXT, created REAL, raw_usage TEXT);
'''

class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.executescript(SCHEMA)
            c.execute('INSERT OR IGNORE INTO meta VALUES(?,?)', ('version', '1'))
            c.execute('INSERT OR IGNORE INTO meta VALUES(?,?)', ('return_days', '30'))
            c.execute('INSERT OR IGNORE INTO inventory VALUES(?,?,?,?)', ('DEMO-CHAIR','Simulated office chair', 4, 24))
            c.execute('INSERT OR IGNORE INTO offers VALUES(?,?,?,?,?,?)', ('offer-a','DEMO-CHAIR','Cedar Supply (simulated)',12500,7,1))
            c.execute('INSERT OR IGNORE INTO offers VALUES(?,?,?,?,?,?)', ('offer-b','DEMO-CHAIR','Swift Furnishings (simulated)',14800,3,1))
            c.execute('INSERT OR IGNORE INTO budget VALUES(1,500000)')

    @contextmanager
    def connect(self):
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA foreign_keys=ON')
        try:
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def rows(self, sql, args=()):
        with self.connect() as c: return [dict(x) for x in c.execute(sql,args)]

    def one(self, sql, args=()):
        rows = self.rows(sql,args)
        return rows[0] if rows else None

    def execute(self, sql, args=()):
        with self.connect() as c: c.execute(sql,args)

    def version(self): return int(self.one("SELECT value FROM meta WHERE key='version'")['value'])

    @staticmethod
    def bump(c): c.execute("UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='version'")

    def event(self, wid, agent, kind, payload):
        self.execute('INSERT INTO events(workflow_id,agent,type,payload,created) VALUES(?,?,?,?,?)', (wid,agent,kind,dumps(payload),time.time()))

    def evidence(self, source, locator, version, text):
        key = digest([source,locator,str(version),text])[:24]
        self.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?)', (key,source,locator,str(version),text))
        return {'id':key,'source':source,'locator':locator,'version':str(version),'text':text}

    def operations(self):
        return {'source':'SIMULATED','currency':'BRL','version':self.version(), 'inventory':self.rows('SELECT * FROM inventory'), 'offers':self.rows('SELECT * FROM offers'), 'budget':self.one('SELECT * FROM budget'), 'purchase_orders':self.rows('SELECT * FROM purchase_orders ORDER BY created DESC'), 'return_days':int(self.one("SELECT value FROM meta WHERE key='return_days'")['value'])}

    def propose(self, wid, sku='DEMO-CHAIR'):
        # Read all inputs and persist the exact proposal under one write lock.
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            previous = c.execute('SELECT * FROM actions WHERE workflow_id=?', (wid,)).fetchone()
            if previous: return dict(previous)
            stock = c.execute('SELECT * FROM inventory WHERE sku=?',(sku,)).fetchone()
            if not stock: raise ValueError('Unknown simulated SKU')
            inbound = c.execute("SELECT COALESCE(SUM(quantity),0) FROM purchase_orders WHERE sku=? AND status='ORDERED'",(sku,)).fetchone()[0]
            qty = max(0, stock['target']-stock['on_hand']-inbound)
            if qty == 0: raise ValueError('No replenishment needed, including pending inbound')
            offer = c.execute('SELECT * FROM offers WHERE sku=? AND active=1 ORDER BY unit_cents,lead_days LIMIT 1',(sku,)).fetchone()
            if not offer: raise ValueError('No active supplier offer')
            version = int(c.execute("SELECT value FROM meta WHERE key='version'").fetchone()[0])
            payload = {'type':'SIMULATED_PURCHASE','sku':sku,'quantity':qty,'offer_id':offer['id'],'supplier':offer['supplier'],'unit_cents':offer['unit_cents'],'total_cents':qty*offer['unit_cents'],'currency':'BRL','lead_days':offer['lead_days']}
            available = c.execute('SELECT available_cents FROM budget WHERE id=1').fetchone()[0]
            status = 'PENDING' if payload['total_cents'] <= min(available, 1000000) else 'BLOCKED'
            action = dict(id=uid(),workflow_id=wid,payload=dumps(payload),digest=digest(payload),snapshot=version,expires=time.time()+3600,status=status,decision=None)
            c.execute('INSERT INTO actions VALUES(:id,:workflow_id,:payload,:digest,:snapshot,:expires,:status,:decision)',action)
            return action

    def decide(self, action_id, decision, expected_digest, failpoint=None):
        if decision not in {'APPROVE','REJECT'}: raise ValueError('Invalid decision')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            a = c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone()
            if not a: raise LookupError('Action not found')
            if a['digest'] != expected_digest: raise ValueError('Approval digest mismatch')
            if a['status'] == 'EXECUTED' and decision == 'APPROVE':
                return dict(c.execute('SELECT * FROM purchase_orders WHERE action_id=?',(action_id,)).fetchone())
            if a['status'] == 'REJECTED' and decision == 'REJECT': return {'status':'REJECTED'}
            if a['status'] != 'PENDING': raise ValueError('Action is not pending')
            if decision == 'REJECT':
                c.execute("UPDATE actions SET status='REJECTED',decision='REJECT' WHERE id=?",(action_id,))
                c.execute('INSERT INTO audit(event,payload,created) VALUES(?,?,?)',('owner_rejected',dumps({'action_id':action_id}),time.time()))
                return {'status':'REJECTED'}
            if a['expires'] < time.time(): raise ValueError('Approval expired; create a fresh proposal')
            version = int(c.execute("SELECT value FROM meta WHERE key='version'").fetchone()[0])
            if a['snapshot'] != version: raise ValueError('Business state changed; create a fresh proposal')
            p = json.loads(a['payload'])
            if digest(p) != a['digest']: raise ValueError('Proposal was modified')
            offer = c.execute('SELECT * FROM offers WHERE id=?',(p['offer_id'],)).fetchone()
            if not offer or not offer['active'] or offer['sku'] != p['sku'] or offer['unit_cents'] != p['unit_cents'] or offer['supplier'] != p['supplier'] or offer['lead_days'] != p['lead_days']: raise ValueError('Supplier offer changed')
            if p['quantity'] <= 0 or p['total_cents'] != p['quantity']*p['unit_cents']: raise ValueError('Invalid financial arithmetic')
            stock = c.execute('SELECT * FROM inventory WHERE sku=?',(p['sku'],)).fetchone()
            inbound = c.execute("SELECT COALESCE(SUM(quantity),0) FROM purchase_orders WHERE sku=? AND status='ORDERED'",(p['sku'],)).fetchone()[0]
            if not stock or p['quantity'] != max(0,stock['target']-stock['on_hand']-inbound): raise ValueError('Stock requirements changed')
            if p['total_cents'] > 1000000: raise ValueError('Policy ceiling exceeded')
            updated = c.execute('UPDATE budget SET available_cents=available_cents-? WHERE id=1 AND available_cents>=?',(p['total_cents'],p['total_cents']))
            if updated.rowcount != 1: raise ValueError('Insufficient available budget')
            if failpoint: failpoint()
            po = dict(id=uid(),action_id=action_id,sku=p['sku'],quantity=p['quantity'],total_cents=p['total_cents'],status='ORDERED',created=time.time())
            c.execute('INSERT INTO purchase_orders VALUES(:id,:action_id,:sku,:quantity,:total_cents,:status,:created)',po)
            c.execute("UPDATE actions SET status='EXECUTED',decision='APPROVE' WHERE id=?",(action_id,))
            c.execute('INSERT INTO audit(event,payload,created) VALUES(?,?,?)',('owner_approved_simulated_purchase',dumps(po),time.time()))
            self.bump(c)
            return po

    def receive(self, po_id):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            po = c.execute('SELECT * FROM purchase_orders WHERE id=?',(po_id,)).fetchone()
            if not po: raise LookupError('Purchase order not found')
            existing = c.execute('SELECT * FROM receipts WHERE po_id=?',(po_id,)).fetchone()
            if existing: return dict(existing)
            if po['status'] != 'ORDERED': raise ValueError('PO is not awaiting delivery')
            receipt = {'id':uid(),'po_id':po_id,'created':time.time()}
            c.execute('INSERT INTO receipts VALUES(:id,:po_id,:created)',receipt)
            c.execute('UPDATE inventory SET on_hand=on_hand+? WHERE sku=?',(po['quantity'],po['sku']))
            c.execute("UPDATE purchase_orders SET status='RECEIVED' WHERE id=?",(po_id,))
            c.execute('INSERT INTO audit(event,payload,created) VALUES(?,?,?)',('simulated_receipt',dumps(receipt),time.time()))
            self.bump(c)
            return receipt

    def update_policy(self, days):
        if not 1 <= days <= 90: raise ValueError('Return days must be 1..90')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute("UPDATE meta SET value=? WHERE key='return_days'",(str(days),))
            self.bump(c)
            c.execute('INSERT INTO audit(event,payload,created) VALUES(?,?,?)',('simulated_policy_changed',dumps({'return_days':days}),time.time()))

    def reset(self):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('DELETE FROM receipts')
            c.execute('DELETE FROM purchase_orders')
            c.execute("UPDATE actions SET status='INVALIDATED' WHERE status IN ('PENDING','EXECUTED')")
            c.execute("UPDATE workflows SET status='CANCELLED' WHERE status='AWAITING_APPROVAL'")
            c.execute('UPDATE inventory SET on_hand=4,target=24')
            c.execute('UPDATE budget SET available_cents=500000')
            c.execute("UPDATE meta SET value='30' WHERE key='return_days'")
            c.execute('DELETE FROM cache')
            self.bump(c)
            c.execute('INSERT INTO audit(event,payload,created) VALUES(?,?,?)',('demo_reset','{}',time.time()))
