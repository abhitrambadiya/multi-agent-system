"""Verify template workflows have no external-network dependency."""
import socket
from backend.contracts import Request

def test_no_network_required_for_template_workflow(engine,monkeypatch):
 def forbidden(*a,**k):raise AssertionError('Unexpected network call')
 monkeypatch.setattr(socket,'create_connection',forbidden)
 wid=engine.start(Request(question='Investigate sales',kind='investigation'))
 result=engine.run(wid)
 assert result['status']=='COMPLETED'
