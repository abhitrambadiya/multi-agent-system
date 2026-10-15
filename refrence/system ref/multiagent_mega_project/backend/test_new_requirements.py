import pytest
import uuid
from unittest.mock import patch
from graph.workflow import app as workflow_app
from database.db import reset_db_state, get_inventory_record, list_all_suppliers, get_connection
from agents.execution import execution_node

@pytest.fixture(autouse=True)
def reset_database_state():
    reset_db_state()

# 1. "How many laptops are in inventory?" routes only to inventory
def test_1_inventory_query_routes_only_to_inventory():
    """Asking 'How many laptops are there in the inventory?' must route only to inventory and not trigger procurement."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "How many laptops are there in the inventory?",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "inventory_query"
    assert state.get("route_taken") == "inventory_query"
    assert state.get("procurement_result") is None, "Inventory query must not invoke procurement!"
    assert state.get("finance_result") is None, "Inventory query must not invoke finance!"
    assert state.get("risk_result") is None, "Inventory query must not invoke risk approval!"
    assert state.get("execution_result") is None, "Inventory query must never create a PO!"
    assert len(snapshot.next) == 0, "Inventory query must not pause for human approval!"
    
    query_res = state.get("query_result")
    assert query_res is not None
    assert query_res.get("found") is True
    assert query_res.get("current_stock") == 2
    assert "General Storage" in query_res.get("location", "")

# 2. A supplier query does not trigger procurement
def test_2_supplier_query_does_not_trigger_procurement():
    """Inquiring about suppliers and pricing must retrieve supplier quotes directly without procurement workflow."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Who are the suppliers for Laptop Stand and what are their quotes?",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "supplier_query"
    assert state.get("route_taken") == "supplier_query"
    assert state.get("procurement_result") is None, "Supplier query must not trigger procurement analysis!"
    assert state.get("execution_result") is None, "Supplier query must not create a PO!"
    assert len(snapshot.next) == 0

    query_res = state.get("query_result")
    assert query_res is not None
    assert len(query_res.get("suppliers", [])) >= 2
    names = [s["name"] for s in query_res["suppliers"]]
    assert "ABC Supplies" in names

# 3. A budget query does not trigger a purchase
def test_3_budget_query_does_not_trigger_purchase():
    """Checking available budget must return current fiscal balances directly without procurement."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "What is our available budget for this fiscal quarter?",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "budget_query"
    assert state.get("route_taken") == "budget_query"
    assert state.get("procurement_result") is None
    assert state.get("execution_result") is None
    assert len(snapshot.next) == 0

    query_res = state.get("query_result")
    assert query_res is not None
    assert query_res.get("total_budget") == 100000
    assert query_res.get("available_budget") == 100000

# 4. A request for 12 laptops preserves the requested quantity
def test_4_requested_quantity_preserved():
    """User request for 12 laptops preserves requested_quantity = 12 throughout state."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "procurement_request"
    assert state.get("requested_quantity") == 12, f"Expected 12 requested, got {state.get('requested_quantity')}"
    assert "next week" in (state.get("deadline") or "").lower()

# 5. Minimum-stock replenishment is calculated separately
def test_5_replenishment_versus_demand_shortfall_separated():
    """
    With 2 usable laptops and demand for 12:
    - requested_quantity = 12
    - current_stock = 2
    - demand_shortfall = 10
    - minimum_stock_level = 30
    - replenishment_quantity = 28
    - quantity_to_order = 10 (immediate demand shortfall, not inflated 28)
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    inv = state.get("inventory_result", {})
    assert state.get("requested_quantity") == 12
    assert inv.get("current_stock") == 2
    assert inv.get("demand_shortfall") == 10
    assert inv.get("minimum_stock_level") == 30
    assert inv.get("replenishment_quantity") == 28
    assert inv.get("quantity_to_order") == 10, "Must not automatically order 28 replenishment units!"
    assert state.get("quantity_to_order") == 10

# 6. Missing details trigger an appropriate clarification
def test_6_missing_details_trigger_clarification():
    """Ambiguous or vague requests without specific product details trigger clarification question."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "We need some stuff ordered for the office.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "clarification_required"
    assert state.get("status") == "NEEDS_CLARIFICATION"
    assert state.get("needs_clarification") is True
    assert state.get("clarification_question") is not None
    assert len(state["clarification_question"]) > 5
    assert state.get("execution_result") is None
    assert len(snapshot.next) == 0

# 7. A valid procurement request pauses for human approval
def test_7_valid_procurement_pauses_for_human_approval():
    """Every valid procurement pauses at human_approval gate before execution."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Wireless Mouse stock has dropped to 5. Minimum required is 20.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert snapshot.next == ("human_approval",), "Workflow must pause at human_approval gate!"
    assert state.get("execution_result") is None, "PO must not be created before explicit approval!"
    assert state.get("status") in ["RUNNING", "PAUSED_FOR_APPROVAL"]

# 8. A rejected request cannot create a purchase order
def test_8_rejected_request_cannot_create_po():
    """Rejecting a procurement request terminates workflow and creates no purchase order."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Wireless Mouse stock has dropped to 5. Minimum required is 20.",
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
    assert final_state.get("execution_result") is None

# 9. A transaction above ₹100,000 is blocked
def test_9_transaction_above_100k_is_blocked():
    """A transaction exceeding ₹100,000 budget cap is blocked and cannot be approved."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    # 18 units @ 6500 = 117,000 INR
    initial_state = {
        "business_event": "Industrial Server Rack stock has fallen to 2 units. The minimum required is 20 units.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("procurement_result", {}).get("total_cost") == 117000
    assert state.get("finance_result", {}).get("status") == "REJECTED"
    assert state.get("risk_result", {}).get("level") == "BLOCKED"
    assert state.get("status") == "BLOCKED"
    assert state.get("execution_result") is None
    assert len(snapshot.next) == 0, "Blocked workflow must not pause for human approval!"

    # Guard verifies direct execution also refuses
    state_copy = dict(state)
    state_copy["approval_status"] = "APPROVED"
    guarded = execution_node(state_copy)
    assert guarded.get("execution_result") is None

# 10. Arbitrary natural-language requests work beyond preset examples
def test_10_arbitrary_natural_language_request():
    """Handles unscripted, natural phrasing with custom items and quantities."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "Our factory line needs 80 units of Industrial Rivets immediately because stock reached 50 and safety floor is 200.",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    state = snapshot.values

    assert state.get("intent") == "procurement_request"
    assert state.get("product") == "Industrial Rivets"
    assert state.get("requested_quantity") == 80
    assert state.get("quantity_to_order") == 30  # 80 needed - 50 on hand = 30 shortfall to order
    assert snapshot.next == ("human_approval",)
    assert state.get("procurement_result") is not None
    assert state.get("procurement_result", {}).get("supplier") in ["Apex Industrial Fasteners", "Global Rivet Corp"]

# 11. Gemini API failure produces a clearly labelled fallback or safe error
def test_11_gemini_api_failure_produces_labelled_fallback():
    """When LLM API fails or throws, system gracefully uses DETERMINISTIC_FALLBACK without crashing."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "business_event": "How many laptops are there in the inventory?",
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }

    # Simulate Gemini API failure returning None, "DETERMINISTIC_FALLBACK", "Connection timeout"
    with patch("agents.manager.invoke_llm_structured", return_value=(None, "DETERMINISTIC_FALLBACK", "Mock API connection error")):
        workflow_app.invoke(initial_state, config=config)
        snapshot = workflow_app.get_state(config)
        state = snapshot.values

    assert state.get("llm_mode") == "DETERMINISTIC_FALLBACK"
    assert state.get("intent") == "inventory_query"
    assert state.get("route_taken") == "inventory_query"
    assert state.get("query_result") is not None
    assert state.get("query_result", {}).get("current_stock") == 2

# 12. Inventory and supplier responses match actual database records
def test_12_inventory_and_supplier_match_actual_db_records():
    """Responses from tools strictly reflect real PostgreSQL/SQLite records."""
    # 1. Compare inventory direct lookup with raw DB query
    db_item = get_inventory_record("Laptops")
    assert db_item is not None
    assert db_item["current_stock"] == 2
    assert db_item["minimum_stock"] == 30

    # 2. Compare supplier quotes with raw DB query
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT supplier_name, unit_price FROM supplier_quotes WHERE product = 'Laptop Stand' ORDER BY unit_price ASC")
        rows = cur.fetchall()
        assert len(rows) >= 2
        cheapest_supplier = rows[0][0]
        cheapest_price = rows[0][1]
    finally:
        conn.close()

    all_suppliers = list_all_suppliers()
    stand_quotes = [s for s in all_suppliers if s["product"] == "Laptop Stand"]
    assert stand_quotes[0]["supplier_name"] == cheapest_supplier
    assert stand_quotes[0]["unit_price"] == cheapest_price
