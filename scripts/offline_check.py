"""Deny outbound Python sockets except loopback while exercising real inference.
Ollama is a separate local process started with OLLAMA_NO_CLOUD=1 and downloaded weights.
This does not alter the user's network settings.
"""
import socket,json
from backend.config import ROOT,Settings
original=socket.socket.connect
attempts=[]
def local_only(sock,address):
 if isinstance(address,tuple) and address[0] not in {'127.0.0.1','::1','localhost'}:
  attempts.append(str(address));raise RuntimeError('Outbound network denied by offline verification')
 return original(sock,address)
socket.socket.connect=local_only
from backend.engine import Engine
from backend.contracts import Request
out=ROOT/'results/offline';out.mkdir(exist_ok=True)
e=Engine(Settings(db=out/'offline.sqlite'))
w=e.start(Request(question='What is our return policy?',kind='policy',cache='A0'));r=e.run(w)
assert r['status']=='COMPLETED',r['error']
w=e.start(Request(question='Prepare replenishment',kind='replenishment'));p=e.run(w);assert p['status']=='AWAITING_APPROVAL';a=p['actions'][0];e.decide(a['id'],'REJECT',a['digest'])
result={'generation_status':r['status'],'mode':r['result']['mode'],'usage':r['usage'],'replenishment_rejected':e.get(w)['status']=='COMPLETED','blocked_external_attempts':attempts,'scope':'Python sockets denied except loopback; local Ollama cloud disabled. Not an operating-system network disconnect.'}
(out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));e.close()
