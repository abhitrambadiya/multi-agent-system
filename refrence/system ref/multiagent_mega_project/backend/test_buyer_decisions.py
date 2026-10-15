import pytest
import uuid
from fastapi.testclient import TestClient
from graph.workflow import app as workflow_app
from main import app as fastapi_app
from database.db import (
    reset_db_state,
    get_supplier_quotes_for_product,
    list_recent_purchase_orders,
    get_inventory_record,
    get_finance_budget_status
)
from tools.supplier_tool import get_suppliers
from tools.inventory_tool import query_inventory_direct
from agents.procurement import configure_procurement_decision
from agents.execution import execution_node

client = TestClient(fastapi_app)

@pytest.fixture(autouse=True)
def clean_db():
    reset_db_state()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Current inventory count returns the actual count
# ─────────────────────────────────────────────────────────────────────────────
def test_1_current_inventory_count_returns_actual_count():
    """Current inventory count query returns the exact stock from PostgreSQL without confusion."""
    db_item = get_inventory_record("Laptops")
    actual_stock = db_item["current_stock"]  # 2 in seeded database
    
    res = query_inventory_direct("Laptops", sub_intent="current_count")
    assert res["status"] == "SUCCESS"
    assert res["current_stock"] == actual_stock
    assert res["sub_intent"] == "current_count"
    assert "units_needed_for_safety" not in res
    assert f"There are {actual_stock} units of {db_item['product']} in stock" in res["summary"]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Safety-threshold query returns threshold minus current usable stock
# ─────────────────────────────────────────────────────────────────────────────
def test_2_safety_threshold_query_returns_threshold_minus_stock():
    """For 'How many laptops will we need to reach the safety threshold?', returns max(0, threshold - stock)."""
    db_item = get_inventory_record("Laptops")
    current_stock = db_item["current_stock"]  # 2
    safety_threshold = db_item["minimum_stock"]  # 30
    expected_needed = max(0, safety_threshold - current_stock)  # 28
    
    # Direct tool verification
    res = query_inventory_direct("Laptops", sub_intent="safety_threshold_replenishment")
    assert res["status"] == "SUCCESS"
    assert res["current_stock"] == current_stock
    assert res["safety_threshold"] == safety_threshold
    assert res["units_needed_for_safety"] == expected_needed
    assert expected_needed == 28
    assert res["units_needed_for_safety"] != current_stock  # Must not return current count as answer
    assert f"{expected_needed} additional unit(s) are needed" in res["summary"]
    
    # End-to-end API verification
    response = client.post("/api/workflow/run", json={
        "business_event": "How many laptops will we need to reach the safety threshold?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUERY_ANSWERED"
    assert data["intent"] == "inventory_query"
    assert data["state"]["inventory_sub_intent"] == "safety_threshold_replenishment"
    assert data["query_result"]["units_needed_for_safety"] == 28
    assert data["query_result"]["current_stock"] == 2
    assert data["query_result"]["safety_threshold"] == 30

# ─────────────────────────────────────────────────────────────────────────────
# 3. Demand shortfall and safety replenishment remain separate
# ─────────────────────────────────────────────────────────────────────────────
def test_3_demand_shortfall_and_safety_replenishment_remain_separate():
    """For 2 laptops in stock, demand of 12, threshold 30: shortfall=10, replenishment=28."""
    response = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    assert response.status_code == 200
    data = response.json()
    state = data["state"]
    
    assert state["current_stock"] == 2
    assert state["requested_quantity"] == 12
    assert state["minimum_stock_level"] == 30
    assert state["demand_shortfall"] == 10
    assert state["replenishment_quantity"] == 28
    # Ensure requested quantity was not overwritten by replenishment quantity
    assert state["requested_quantity"] != state["replenishment_quantity"]
    assert state["demand_shortfall"] != state["replenishment_quantity"]

# ─────────────────────────────────────────────────────────────────────────────
# 4. Each purchasing strategy calculates the correct order quantity and total cost
# ─────────────────────────────────────────────────────────────────────────────
def test_4_each_purchasing_strategy_calculates_correct_quantity_and_cost():
    """Purchasing strategies offer meet_demand (10 units), restore_safety_stock (28 units), and custom."""
    response = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    assert response.status_code == 200
    data = response.json()
    thread_id = data["thread_id"]
    
    strategies = data["available_strategies"]
    assert len(strategies) >= 3
    strat_map = {s.get("strategy", s.get("strategy_id")): s for s in strategies}
    
    assert "meet_demand" in strat_map
    assert strat_map["meet_demand"]["quantity"] == 10
    assert "restore_safety_stock" in strat_map
    assert strat_map["restore_safety_stock"]["quantity"] == 28
    assert "custom" in strat_map
    
    # 1. Test selecting meet_demand
    conf1 = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_strategy": "meet_demand"
    })
    assert conf1.status_code == 200
    data1 = conf1.json()
    assert data1["selected_strategy"] == "meet_demand"
    assert data1["final_order_quantity"] == 10
    unit_price = data1["state"]["procurement_result"]["unit_price"]
    assert data1["state"]["procurement_result"]["total_cost"] == 10 * unit_price
    
    # 2. Test selecting restore_safety_stock
    conf2 = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_strategy": "restore_safety_stock"
    })
    assert conf2.status_code == 200
    data2 = conf2.json()
    assert data2["selected_strategy"] == "restore_safety_stock"
    assert data2["final_order_quantity"] == 28
    assert data2["state"]["procurement_result"]["total_cost"] == 28 * unit_price
    
    # 3. Test custom strategy
    conf3 = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_strategy": "custom",
        "final_order_quantity": 15
    })
    assert conf3.status_code == 200
    data3 = conf3.json()
    assert data3["selected_strategy"] == "custom"
    assert data3["final_order_quantity"] == 15
    assert data3["state"]["procurement_result"]["total_cost"] == 15 * unit_price

# ─────────────────────────────────────────────────────────────────────────────
# 5. Multiple supplier quotes are returned from the database
# ─────────────────────────────────────────────────────────────────────────────
def test_5_multiple_supplier_quotes_returned_from_database():
    """At least 3 quotes are returned from PostgreSQL for Laptops with all required metadata."""
    quotes = get_suppliers("Laptops")
    assert len(quotes) >= 3, "Expected at least 3 eligible quotes for Laptops"
    
    names = [q["name"] for q in quotes]
    assert "Premier Vendor Alliance" in names
    assert "Rapid Supply Direct" in names
    assert "Zenith Systems" in names
    
    for q in quotes:
        assert "name" in q
        assert "unit_price" in q and q["unit_price"] > 0
        assert q["currency"] == "INR"
        assert "delivery_days" in q and q["delivery_days"] > 0
        assert "rating" in q and q["rating"] > 0
        assert "reliability_score" in q
        assert "in_stock" in q

# ─────────────────────────────────────────────────────────────────────────────
# 6. Supplier selection is preserved through approval and execution
# ─────────────────────────────────────────────────────────────────────────────
def test_6_supplier_selection_preserved_through_approval_and_execution():
    """When a buyer chooses a specific non-default supplier, that vendor is used in PO execution."""
    response = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Buyer selects "Zenith Systems" instead of default
    conf = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_supplier_name": "Zenith Systems",
        "selected_strategy": "meet_demand"
    })
    assert conf.status_code == 200
    conf_data = conf.json()
    assert conf_data["selected_supplier"]["name"] == "Zenith Systems"
    assert conf_data["state"]["supplier_selection_mode"] == "MANUAL"
    assert conf_data["state"]["procurement_result"]["supplier"] == "Zenith Systems"
    expected_cost = 10 * 1400  # 10 units @ 1400 INR
    assert conf_data["state"]["procurement_result"]["total_cost"] == expected_cost
    
    # Approve transaction
    appr = client.post("/api/workflow/approve", json={
        "thread_id": thread_id,
        "action": "APPROVE"
    })
    assert appr.status_code == 200
    appr_data = appr.json()
    assert appr_data["status"] == "COMPLETED"
    po = appr_data["state"]["execution_result"]
    assert po is not None
    assert po["supplier"] == "Zenith Systems"
    assert po["quantity"] == 10
    assert po["total_cost"] == expected_cost

# ─────────────────────────────────────────────────────────────────────────────
# 7. Changing a supplier or quantity recalculates cost and budget
# ─────────────────────────────────────────────────────────────────────────────
def test_7_changing_supplier_or_quantity_recalculates_cost_and_budget():
    """Changing supplier or quantity automatically recalculates total cost and remaining budget."""
    initial_budget = get_finance_budget_status()["available_budget"]  # 95,000
    
    response = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    thread_id = response.json()["thread_id"]
    
    # Change to quantity 20 with Premier Vendor Alliance (1200 INR)
    conf1 = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_strategy": "custom",
        "final_order_quantity": 20,
        "selected_supplier_name": "Premier Vendor Alliance"
    })
    assert conf1.status_code == 200
    st1 = conf1.json()["state"]
    cost1 = 20 * 1200  # 24,000
    assert st1["procurement_result"]["total_cost"] == cost1
    assert st1["finance_result"]["remaining_budget"] == initial_budget - cost1
    
    # Change supplier to Rapid Supply Direct (1350 INR)
    conf2 = client.post("/api/workflow/configure", json={
        "thread_id": thread_id,
        "selected_supplier_name": "Rapid Supply Direct"
    })
    assert conf2.status_code == 200
    st2 = conf2.json()["state"]
    cost2 = 20 * 1350  # 27,000
    assert st2["procurement_result"]["total_cost"] == cost2
    assert st2["finance_result"]["remaining_budget"] == initial_budget - cost2

# ─────────────────────────────────────────────────────────────────────────────
# 8. Approval is invalidated if material transaction details change
# ─────────────────────────────────────────────────────────────────────────────
def test_8_approval_invalidated_if_material_details_change():
    """If buyer changes strategy, quantity, or supplier after approval, approval is invalidated."""
    state = {
        "thread_id": "test-invalidation",
        "product": "Laptops",
        "selected_strategy": "meet_demand",
        "final_order_quantity": 10,
        "quantity_to_order": 10,
        "demand_shortfall": 10,
        "replenishment_quantity": 28,
        "selected_supplier_name": "Premier Vendor Alliance",
        "approval_status": "APPROVED",
        "approved_transaction": {
            "supplier": "Premier Vendor Alliance",
            "product": "Laptops",
            "quantity": 10,
            "total_cost": 12000
        },
        "procurement_result": {
            "supplier": "Premier Vendor Alliance",
            "unit_price": 1200,
            "quantity": 10,
            "total_cost": 12000
        },
        "finance_result": {"status": "APPROVED", "remaining_budget": 83000},
        "risk_result": {"level": "LOW"},
        "status": "PAUSED_FOR_APPROVAL",
        "agent_traces": [],
        "audit_log": []
    }
    
    # Change quantity to 15 -> should invalidate approval
    updated_state = configure_procurement_decision(state, final_order_quantity=15)
    assert updated_state["approval_status"] is None, "Approval must be invalidated when quantity changes!"
    assert updated_state["approved_transaction"] is None
    
    # Verify execution guard blocks unapproved execution
    blocked_state = execution_node(updated_state)
    assert blocked_state.get("execution_result") is None, "Execution must not run with invalidated approval!"

# ─────────────────────────────────────────────────────────────────────────────
# 9. Fewer than three eligible suppliers are handled honestly
# ─────────────────────────────────────────────────────────────────────────────
def test_9_fewer_than_three_suppliers_handled_honestly():
    """When fewer than 3 suppliers exist (e.g. Laptop Stand has 2), only real quotes are returned."""
    quotes = get_supplier_quotes_for_product("Laptop Stand")
    assert len(quotes) == 2, "Laptop Stand must have exactly 2 quotes in database"
    
    tool_quotes = get_suppliers("Laptop Stand")
    assert len(tool_quotes) == 2, "Must return exactly 2 suppliers without fabricating a 3rd"
    names = [q["name"] for q in tool_quotes]
    assert "ABC Supplies" in names
    assert "XYZ Traders" in names

# ─────────────────────────────────────────────────────────────────────────────
# 10. Read-only requests never create purchase orders
# ─────────────────────────────────────────────────────────────────────────────
def test_10_read_only_requests_never_create_purchase_orders():
    """Inventory, supplier, budget, and risk queries never create purchase orders."""
    pos_before = len(list_recent_purchase_orders(100))
    
    r1 = client.post("/api/workflow/run", json={"business_event": "How many laptops are in inventory?"})
    assert r1.status_code == 200
    assert r1.json()["state"].get("execution_result") is None
    
    r2 = client.post("/api/workflow/run", json={"business_event": "Who supplies Laptop Stand?"})
    assert r2.status_code == 200
    assert r2.json()["state"].get("execution_result") is None
    
    r3 = client.post("/api/workflow/run", json={"business_event": "How much budget is left?"})
    assert r3.status_code == 200
    assert r3.json()["state"].get("execution_result") is None
    
    pos_after = len(list_recent_purchase_orders(100))
    assert pos_after == pos_before, "Read-only queries must never create purchase orders!"

# ─────────────────────────────────────────────────────────────────────────────
# 11. Over-budget transactions remain blocked
# ─────────────────────────────────────────────────────────────────────────────
def test_11_over_budget_transactions_remain_blocked():
    """Transactions exceeding ₹100,000 cap cannot be authorized or executed."""
    response = client.post("/api/workflow/run", json={
        "business_event": "Industrial Server Rack stock has fallen to 2 units. The minimum required is 20 units."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "BLOCKED"
    assert data["state"]["risk_result"]["level"] == "BLOCKED"
    thread_id = data["thread_id"]
    
    # Attempting approval must fail with 400
    appr_res = client.post("/api/workflow/approve", json={
        "thread_id": thread_id,
        "action": "APPROVE"
    })
    assert appr_res.status_code == 400
    
    # Direct execution guard check
    blocked_state = execution_node(data["state"])
    assert blocked_state.get("execution_result") is None

# ─────────────────────────────────────────────────────────────────────────────
# 12. Rejected and duplicate transactions never create additional purchase orders
# ─────────────────────────────────────────────────────────────────────────────
def test_12_rejected_and_duplicate_transactions_never_create_po():
    """Rejections and duplicate calls are safely handled without creating extra POs."""
    pos_start = len(list_recent_purchase_orders(100))
    
    # 1. Test Rejection
    r1 = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    thread_id_reject = r1.json()["thread_id"]
    rej_res = client.post("/api/workflow/approve", json={
        "thread_id": thread_id_reject,
        "action": "REJECT"
    })
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "REJECTED"
    assert rej_res.json()["state"].get("execution_result") is None
    assert len(list_recent_purchase_orders(100)) == pos_start
    
    # 2. Test Duplicate Execution Prevention
    r2 = client.post("/api/workflow/run", json={
        "business_event": "We have only 2 laptops left, but the IT department needs 12 by next week."
    })
    thread_id_approve = r2.json()["thread_id"]
    appr_res = client.post("/api/workflow/approve", json={
        "thread_id": thread_id_approve,
        "action": "APPROVE"
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "COMPLETED"
    assert len(list_recent_purchase_orders(100)) == pos_start + 1
    
    # Attempt duplicate approval on already executed thread
    dup_res = client.post("/api/workflow/approve", json={
        "thread_id": thread_id_approve,
        "action": "APPROVE"
    })
    assert dup_res.status_code == 400
    assert "not currently pending human approval" in dup_res.json()["detail"] or "already been executed" in dup_res.json()["detail"]
    assert len(list_recent_purchase_orders(100)) == pos_start + 1
