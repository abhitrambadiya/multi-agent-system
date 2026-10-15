import pytest
import uuid
from fastapi.testclient import TestClient
from main import app as fastapi_app, _normalize_supplier_name
from graph.workflow import app as workflow_app
from agents.manager import _deterministic_intent_classifier
from tools.inventory_tool import check_inventory
from agents.procurement import configure_procurement_decision
from tools.supplier_tool import get_suppliers
from database.db import list_recent_purchase_orders

client = TestClient(fastapi_app)

def test_1_demand_semantics_8_more_laptops():
    """
    Test 1: 'We have 12 laptops and need 8 more' results in an order quantity of 8.
    Does not subtract existing stock (12) from requested additional units (8).
    """
    prompt = "We have 12 laptops and need 8 more laptops"
    classified = _deterministic_intent_classifier(prompt)
    
    assert classified.intent == "procurement_request"
    assert classified.quantity_semantics == "ADDITIONAL_QUANTITY"
    assert classified.additional_quantity == 8

    inv = check_inventory(
        "laptop",
        supplied_current=12,
        supplied_minimum=10,
        requested_quantity=8,
        quantity_semantics="ADDITIONAL_QUANTITY",
        additional_quantity=8
    )
    assert inv["demand_shortfall"] == 8
    assert inv["current_stock"] == 12

    # End-to-end workflow invocation
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": prompt,
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    values = snapshot.values

    assert values["status"] == "PAUSED_FOR_APPROVAL"
    assert values["final_order_quantity"] == 8
    assert values["procurement_result"]["quantity"] == 8
    assert values["quantity_semantics"] == "ADDITIONAL_QUANTITY"
    assert values["additional_quantity"] == 8

def test_2_demand_semantics_8_in_total_zero_needed():
    """
    Test 2: 'We have 12 laptops and need 8 in total' results in an order quantity of 0.
    12 available stock already covers 8 total demand.
    """
    prompt = "We have 12 laptops and need 8 laptops in total"
    classified = _deterministic_intent_classifier(prompt)
    
    assert classified.intent == "procurement_request"
    assert classified.quantity_semantics == "TOTAL_DEMAND"
    assert classified.demand_quantity == 8

    inv = check_inventory(
        "laptop",
        supplied_current=12,
        supplied_minimum=10,
        requested_quantity=8,
        quantity_semantics="TOTAL_DEMAND",
        demand_quantity=8
    )
    assert inv["demand_shortfall"] == 0
    assert inv["current_stock"] == 12

    # End-to-end workflow invocation
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": prompt,
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    values = snapshot.values

    # Immediate demand strategy requires 0 units
    meet_strat = next(s for s in values["available_strategies"] if s["strategy"] == "meet_demand")
    assert meet_strat["quantity"] == 0

def test_3_demand_semantics_20_in_total_shortfall_8():
    """
    Test 3: 'We have 12 laptops and need 20 in total' results in an order quantity of 8.
    Shortfall = max(0, 20 - 12) = 8.
    """
    prompt = "We have 12 laptops and need 20 laptops in total"
    classified = _deterministic_intent_classifier(prompt)
    
    assert classified.intent == "procurement_request"
    assert classified.quantity_semantics == "TOTAL_DEMAND"
    assert classified.demand_quantity == 20

    inv = check_inventory(
        "laptop",
        supplied_current=12,
        supplied_minimum=10,
        requested_quantity=20,
        quantity_semantics="TOTAL_DEMAND",
        demand_quantity=20
    )
    assert inv["demand_shortfall"] == 8
    assert inv["current_stock"] == 12

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": prompt,
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    values = snapshot.values

    assert values["status"] == "PAUSED_FOR_APPROVAL"
    assert values["final_order_quantity"] == 8
    assert values["procurement_result"]["quantity"] == 8

def test_4_reach_safety_threshold_replenishment_18():
    """
    Test 4: 'We have 12 laptops and need enough to reach a safety threshold of 30'
    Results in safety replenishment quantity = max(0, 30 - 12) = 18.
    """
    prompt = "We have 12 laptops and need enough to reach a safety threshold of 30"
    classified = _deterministic_intent_classifier(prompt)
    assert classified.quantity_semantics in ["TARGET_STOCK", "ADDITIONAL_QUANTITY", "TOTAL_DEMAND"]

    inv = check_inventory(
        "laptop",
        supplied_current=12,
        supplied_minimum=30,
        target_total_stock=30,
        quantity_semantics="TARGET_STOCK"
    )
    assert inv["replenishment_quantity"] == 18
    assert inv["current_stock"] == 12
    assert inv["minimum_stock_level"] == 30

def test_5_custom_purchase_qty_vs_target_total_stock():
    """
    Test 5: The custom purchase quantity is not confused with a target total stock level.
    - Purchase Volume 15 -> orders exactly 15 units.
    - Target Total Stock 25 with current stock 12 -> orders max(0, 25 - 12) = 13 units.
    """
    state_mock = {
        "current_stock": 12,
        "minimum_stock_level": 10,
        "product": "laptop",
        "selected_strategy": "custom",
        "final_order_quantity": 15,
        "custom_target_type": "PURCHASE_QUANTITY",
        "approval_status": None,
        "audit_log": [],
        "procurement_result": {}
    }

    # Case A: Direct purchase volume of 15
    updated_a = configure_procurement_decision(
        state=dict(state_mock),
        selected_strategy="custom",
        final_order_quantity=15,
        custom_target_type="PURCHASE_QUANTITY"
    )
    assert updated_a["final_order_quantity"] == 15
    assert updated_a["procurement_result"]["quantity"] == 15

    # Case B: Target Total Stock level of 25 (when current is 12)
    updated_b = configure_procurement_decision(
        state=dict(state_mock),
        selected_strategy="custom",
        final_order_quantity=25,
        custom_target_type="TARGET_TOTAL_STOCK"
    )
    # Expected order quantity: 25 - 12 = 13
    assert updated_b["final_order_quantity"] == 13
    assert updated_b["procurement_result"]["quantity"] == 13

def test_6_supplier_objects_schema_and_string_normalization():
    """
    Test 6: Supplier objects render without a React child-object exception.
    Verifies that recommended_supplier is normalized to a string name across backend API outputs,
    while recommended_supplier_quote preserves the dictionary with all keys:
    {name, product, unit_price, delivery_days, in_stock, rating, reliability_score, currency, data_source, total_price}
    """
    quote_obj = {
        "name": "Zenith Systems",
        "product": "laptop",
        "unit_price": 5000,
        "delivery_days": 2,
        "in_stock": True,
        "rating": 4.8,
        "reliability_score": 0.96,
        "currency": "INR",
        "data_source": "database::supplier_quotes",
        "total_price": 25000
    }

    # Verify normalizer converts object to name string
    assert _normalize_supplier_name(quote_obj) == "Zenith Systems"
    assert _normalize_supplier_name("Zenith Systems") == "Zenith Systems"
    assert _normalize_supplier_name(None) == "—"

    # Verify API boundary normalizes recommended_supplier to string
    res = client.post("/api/workflow/run", json={"business_event": "Order 10 more laptops for engineering"})
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["recommended_supplier"], str)
    assert isinstance(data["recommended_supplier_name"], str)
    assert data["recommended_supplier"] in [q["name"] for q in data["eligible_quotes"]]
    assert isinstance(data["recommended_supplier_quote"], dict)
    assert "name" in data["recommended_supplier_quote"]
    assert "unit_price" in data["recommended_supplier_quote"]

def test_7_supplier_comparison_displays_all_eligible_quotes():
    """
    Test 7: Supplier comparison displays all eligible database-backed quotes (at least 3 quotes for laptop).
    """
    quotes = get_suppliers("laptop")
    assert len(quotes) >= 3
    for q in quotes:
        assert "name" in q
        assert "unit_price" in q
        assert "delivery_days" in q
        assert "rating" in q

def test_8_selecting_supplier_updates_final_transaction():
    """
    Test 8: Selecting a supplier updates the final transaction correctly.
    """
    quotes = get_suppliers("laptop")
    target_vendor = quotes[-1]  # Select a non-default vendor

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": "Procure 2 laptops for engineering",
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    
    updated = configure_procurement_decision(
        state=dict(snapshot.values),
        selected_supplier_name=target_vendor["name"]
    )
    assert updated["selected_supplier_name"] == target_vendor["name"]
    assert updated["procurement_result"]["supplier"] == target_vendor["name"]
    assert updated["procurement_result"]["unit_price"] == target_vendor["unit_price"]
    assert updated["procurement_result"]["total_cost"] == target_vendor["unit_price"] * updated["final_order_quantity"]

def test_9_changing_supplier_or_qty_recalculates_cost_and_invalidates_approval():
    """
    Test 9: Changing a supplier or quantity recalculates cost and invalidates previous approval.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": "Procure 2 laptops for marketing",
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    
    state = dict(snapshot.values)
    # Simulate human approval
    state["approval_status"] = "APPROVED"
    state["approved_transaction"] = dict(state["procurement_result"])

    # Buyer changes quantity to 3
    reconfigured = configure_procurement_decision(
        state=state,
        final_order_quantity=3
    )
    # Approval must be invalidated
    assert reconfigured["approval_status"] is None
    assert reconfigured["approved_transaction"] is None
    assert any("invalidated" in log.lower() for log in reconfigured["audit_log"])

def test_10_over_budget_transactions_remain_blocked():
    """
    Test 10: Transactions exceeding corporate limit (₹100,000) remain blocked.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    # 150 enterprise laptops @ ₹1,200 = ₹180,000 > ₹100,000
    initial_state = {
        "thread_id": thread_id,
        "business_event": "Emergency purchase: 150 enterprise laptops required immediately.",
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    vals = snapshot.values

    assert vals["status"] == "BLOCKED"
    assert vals["risk_result"]["level"] == "BLOCKED"
    assert vals["procurement_result"]["total_cost"] > 100000

def test_11_rejected_transactions_cannot_create_purchase_orders():
    """
    Test 11: Rejected transactions cannot create purchase orders.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "thread_id": thread_id,
        "business_event": "Order 2 laptops for finance",
        "audit_log": [],
        "agent_traces": [],
        "status": "PENDING"
    }
    workflow_app.invoke(initial_state, config=config)
    snapshot = workflow_app.get_state(config)
    assert snapshot.next == ("human_approval",)
    
    pos_before = len(list_recent_purchase_orders())
    # Human rejects
    workflow_app.update_state(config, {"approval_status": "REJECTED"})
    workflow_app.invoke(None, config=config)

    pos_after = len(list_recent_purchase_orders())
    assert pos_after == pos_before

    final_snapshot = workflow_app.get_state(config)
    assert final_snapshot.values.get("execution_result") is None
    assert final_snapshot.values.get("status") == "REJECTED"
