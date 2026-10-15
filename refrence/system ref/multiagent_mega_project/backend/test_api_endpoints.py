import pytest
from fastapi.testclient import TestClient
from main import app
from database.db import reset_db_state

@pytest.fixture(autouse=True)
def reset_database_state():
    reset_db_state()

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_api_low_risk_pauses_and_approves():
    """Every purchase (even low risk) must pause for approval before executing."""
    payload = {"business_event": "Laptop Stand inventory has dropped to 12. Minimum required is 50."}
    res = client.post("/api/workflow/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_paused"] is True, "Low-risk purchase must pause for approval!"
    assert data["status"] == "PAUSED_FOR_APPROVAL"
    assert "thread_id" in data
    assert data["state"].get("execution_result") is None
    thread_id = data["thread_id"]

    # Approving executes
    approve_res = client.post("/api/workflow/approve", json={"thread_id": thread_id, "action": "APPROVE"})
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["is_paused"] is False
    assert approved_data["status"] == "COMPLETED"
    assert approved_data["state"]["execution_result"] is not None
    assert "PO-2026-" in approved_data["state"]["execution_result"]["po_id"]

def test_api_low_risk_rejection():
    """Rejecting a low-risk purchase creates no PO."""
    payload = {"business_event": "Laptop Stand inventory has dropped to 12. Minimum required is 50."}
    res = client.post("/api/workflow/run", json=payload)
    assert res.status_code == 200
    thread_id = res.json()["thread_id"]

    reject_res = client.post("/api/workflow/approve", json={"thread_id": thread_id, "action": "REJECT"})
    assert reject_res.status_code == 200
    rejected_data = reject_res.json()
    assert rejected_data["is_paused"] is False
    assert rejected_data["status"] == "REJECTED"
    assert rejected_data["state"].get("execution_result") is None

def test_api_high_risk_pause_and_approve():
    payload = {"business_event": "Server Rack stock has fallen to 2 units. The minimum required stock is 15 units."}
    res = client.post("/api/workflow/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_paused"] is True
    assert data["status"] == "PAUSED_FOR_APPROVAL"
    thread_id = data["thread_id"]

    # Check status endpoint
    status_res = client.get(f"/api/workflow/status/{thread_id}")
    assert status_res.status_code == 200
    assert status_res.json()["is_paused"] is True

    # Approve
    approve_res = client.post("/api/workflow/approve", json={"thread_id": thread_id, "action": "APPROVE"})
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["is_paused"] is False
    assert approved_data["status"] == "COMPLETED"
    assert approved_data["state"]["execution_result"] is not None

def test_api_high_risk_pause_and_reject():
    payload = {"business_event": "Server Rack stock has fallen to 2 units. The minimum required stock is 15 units."}
    res = client.post("/api/workflow/run", json=payload)
    assert res.status_code == 200
    thread_id = res.json()["thread_id"]

    # Reject
    reject_res = client.post("/api/workflow/approve", json={"thread_id": thread_id, "action": "REJECT"})
    assert reject_res.status_code == 200
    rejected_data = reject_res.json()
    assert rejected_data["is_paused"] is False
    assert rejected_data["status"] == "REJECTED"
    assert rejected_data["state"].get("execution_result") is None

def test_api_insufficient_budget_cannot_be_approved():
    payload = {"business_event": "Industrial Server Rack stock has fallen to 2 units. The minimum required is 20 units."}
    res = client.post("/api/workflow/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_paused"] is False
    assert data["status"] == "BLOCKED"
    assert data["state"].get("execution_result") is None
    thread_id = data["thread_id"]

    # Submitting approval on a blocked workflow must be rejected with 400
    approve_res = client.post("/api/workflow/approve", json={"thread_id": thread_id, "action": "APPROVE"})
    assert approve_res.status_code == 400
