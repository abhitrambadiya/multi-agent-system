import pytest
import uuid
from graph.workflow import app as workflow_app
from agents.execution import execution_node
from database.db import reset_db_state

@pytest.fixture(autouse=True)
def reset_database_state():
    reset_db_state()

def test_1_low_risk_purchase_pauses_and_approves():
    """A ₹32,300 low-risk purchase pauses for approval and creates no PO before approval. Approving creates a PO."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Laptop Stand inventory has dropped to 12. Minimum required is 50.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    # 1. Initial invoke MUST pause for human approval
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values
    
    assert state.get("product") == "Laptop Stand"
    assert state.get("inventory_result", {}).get("quantity_to_order") == 38
    assert state.get("procurement_result", {}).get("total_cost") == 38 * 850  # ₹32,300
    assert state.get("risk_result", {}).get("level") == "LOW"
    assert snapshot.next == ("human_approval",), "Low-risk purchase must pause at human_approval gate!"
    assert state.get("execution_result") is None, "No PO must be created before human approval!"
    
    # 2. Approving resumes and creates PO
    workflow_app.update_state(config, {"approval_status": "APPROVED"})
    workflow_app.invoke(None, config=config)
    
    final_snapshot = workflow_app.get_state(config)
    final_state = final_snapshot.values
    assert final_state.get("approval_status") == "APPROVED"
    assert final_state.get("status") == "COMPLETED"
    assert final_state.get("execution_result") is not None
    assert "PO-2026-" in final_state["execution_result"]["po_id"]
    assert final_state["execution_result"]["status"] == "CREATED"

def test_2_low_risk_purchase_rejection():
    """Rejecting a ₹32,300 low-risk purchase creates no PO."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Laptop Stand inventory has dropped to 12. Minimum required is 50.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    assert snapshot.next == ("human_approval",)
    
    # Reject
    workflow_app.update_state(config, {"approval_status": "REJECTED"})
    workflow_app.invoke(None, config=config)
    
    final_snapshot = workflow_app.get_state(config)
    final_state = final_snapshot.values
    assert final_state.get("approval_status") == "REJECTED"
    assert final_state.get("status") == "REJECTED"
    assert final_state.get("execution_result") is None, "Rejected low-risk purchase must never create a PO!"

def test_3_high_risk_purchase_pauses_and_approves():
    """A ₹78,000 high-risk purchase also requires approval and creates a PO upon approval."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Server Rack stock has fallen to 2 units. The minimum required stock is 15 units.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values
    
    assert state.get("product") == "Server Rack"
    assert state.get("inventory_result", {}).get("quantity_to_order") == 13
    assert state.get("procurement_result", {}).get("total_cost") == 13 * 6000  # ₹78,000
    assert state.get("risk_result", {}).get("level") == "HIGH"
    assert snapshot.next == ("human_approval",)
    assert state.get("execution_result") is None
    
    # Approve
    workflow_app.update_state(config, {"approval_status": "APPROVED"})
    workflow_app.invoke(None, config=config)
    
    final_snapshot = workflow_app.get_state(config)
    final_state = final_snapshot.values
    assert final_state.get("approval_status") == "APPROVED"
    assert final_state.get("status") == "COMPLETED"
    assert final_state.get("execution_result") is not None
    assert "PO-2026-" in final_state["execution_result"]["po_id"]

def test_4_high_risk_purchase_rejection():
    """Rejecting a ₹78,000 high-risk purchase creates no PO."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Server Rack stock has fallen to 2 units. The minimum required stock is 15 units.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    assert snapshot.next == ("human_approval",)
    
    # Reject
    workflow_app.update_state(config, {"approval_status": "REJECTED"})
    workflow_app.invoke(None, config=config)
    
    final_snapshot = workflow_app.get_state(config)
    final_state = final_snapshot.values
    assert final_state.get("approval_status") == "REJECTED"
    assert final_state.get("status") == "REJECTED"
    assert final_state.get("execution_result") is None, "Rejected high-risk purchase must never create a PO!"

def test_5_insufficient_budget_blocked():
    """An order exceeding ₹100,000 is blocked and cannot execute even if an approval request is submitted."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Industrial Server Rack stock has fallen to 2 units. The minimum required is 20 units.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values
    
    assert state.get("inventory_result", {}).get("quantity_to_order") == 18
    assert state.get("procurement_result", {}).get("total_cost") == 117000
    assert state.get("finance_result", {}).get("status") == "REJECTED"
    assert state.get("risk_result", {}).get("level") == "BLOCKED"
    assert state.get("status") == "BLOCKED"
    assert state.get("execution_result") is None
    assert len(snapshot.next) == 0, "Blocked workflow must not pause for human approval!"
    
    # Attempting to artificially update state to APPROVED and execute MUST fail
    state_copy = dict(state)
    state_copy["approval_status"] = "APPROVED"
    guarded_state = execution_node(state_copy)
    assert guarded_state.get("execution_result") is None, "Execution guard must block PO creation on budget violation!"

def test_6_invalid_events_cannot_create_po():
    """Invalid events cannot create purchase orders."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "All team members should attend the town hall tomorrow at 3 PM.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values
    
    assert state.get("status") == "FAILED"
    assert state.get("error_message") is not None
    assert state.get("execution_result") is None
    assert len(snapshot.next) == 0

def test_7_direct_or_repeated_execution_prevention():
    """Direct or repeated execution requests cannot bypass approval or create duplicate POs."""
    # 1. Unapproved state cannot execute
    unapproved_state = {
        "status": "PAUSED_FOR_APPROVAL",
        "product": "Laptop Stand",
        "procurement_result": {"supplier": "ABC Supplies", "quantity": 10, "total_cost": 8500},
        "finance_result": {"status": "APPROVED"},
        "risk_result": {"level": "LOW"},
        "approval_status": None,  # Not approved!
        "agent_traces": [],
        "audit_log": []
    }
    res1 = execution_node(dict(unapproved_state))
    assert res1.get("execution_result") is None, "Execution without approval must be refused!"
    
    # 2. Approved state with mismatched parameters cannot execute
    mismatched_state = {
        "status": "RUNNING",
        "product": "Laptop Stand",
        "procurement_result": {"supplier": "ABC Supplies", "quantity": 10, "total_cost": 8500},
        "finance_result": {"status": "APPROVED"},
        "risk_result": {"level": "LOW"},
        "approval_status": "APPROVED",
        "approved_transaction": {"supplier": "ABC Supplies", "product": "Laptop Stand", "quantity": 10, "total_cost": 5000},  # Amount mismatch!
        "agent_traces": [],
        "audit_log": []
    }
    res2 = execution_node(dict(mismatched_state))
    assert res2.get("execution_result") is None, "Execution with mismatched approved details must be refused!"
    
    # 3. Repeated execution cannot overwrite or duplicate existing PO
    already_executed_state = {
        "status": "COMPLETED",
        "product": "Laptop Stand",
        "procurement_result": {"supplier": "ABC Supplies", "quantity": 10, "total_cost": 8500},
        "finance_result": {"status": "APPROVED"},
        "risk_result": {"level": "LOW"},
        "approval_status": "APPROVED",
        "approved_transaction": {"supplier": "ABC Supplies", "product": "Laptop Stand", "quantity": 10, "total_cost": 8500},
        "execution_result": {"po_id": "PO-2026-ORIGINAL", "status": "CREATED"},
        "agent_traces": [],
        "audit_log": []
    }
    res3 = execution_node(dict(already_executed_state))
    assert res3["execution_result"]["po_id"] == "PO-2026-ORIGINAL", "Existing PO must not be duplicated or overwritten!"
