"""
AI-EOS Regression Test Suite: Web Research Agent for Live Procurement Price Comparison
Covers all 10 core requirements:
1. Multiple web offers can be normalized.
2. Invalid or missing prices are handled safely.
3. Different product models are not incorrectly merged.
4. Web offers are compared with internal supplier quotes.
5. Unavailable delivery information is not fabricated.
6. Search failures fall back safely to internal quotes.
7. The source URL and retrieval timestamp are preserved.
8. Read-only queries do not trigger web research unnecessarily.
9. Budget and approval safeguards remain enforced.
10. Web offers cannot cause an external purchase without an authorized integration.
"""

import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from main import app as fastapi_app
from graph.workflow import app as workflow_app
from tools.web_research_tool import (
    normalize_web_offer,
    deduplicate_and_distinguish_offers,
    discover_online_offers,
    sanitize_web_text
)
from agents.procurement import configure_procurement_decision
from agents.web_research import web_research_node
from graph.state import WorkflowState

client = TestClient(fastapi_app)

# ─── Test 1: Multiple Web Offers Can Be Normalized ───────────────────────────

def test_1_multiple_web_offers_normalized():
    """Multiple web offers from various platforms normalize into validated, structured records."""
    raw_offers = [
        {
            "source_name": "Amazon India",
            "title": "Lenovo ThinkPad E14 Gen 5 (16GB RAM, 512GB SSD)",
            "url": "https://www.amazon.in/dp/B0CBV9P18Q",
            "unit_price": 54990.0,
            "currency": "INR",
            "shipping_cost": 0.0,
            "availability": "IN_STOCK",
            "delivery_days": 2,
            "specifications": {"ram": "16GB", "storage": "512GB SSD"}
        },
        {
            "source_name": "Dell Technologies Store",
            "title": "Dell Latitude 3440 Laptop (16GB RAM, 512GB SSD)",
            "url": "https://www.dell.com/en-in/shop/dell-laptops/latitude-3440-laptop",
            "unit_price": 58900.0,
            "currency": "INR",
            "shipping_cost": 500.0,
            "availability": "IN_STOCK",
            "delivery_days": 3,
            "specifications": {"ram": "16GB", "storage": "512GB SSD"}
        }
    ]

    normalized = [
        normalize_web_offer(
            source_name=o["source_name"],
            title=o["title"],
            url=o["url"],
            unit_price=o["unit_price"],
            currency=o["currency"],
            quantity=2,
            shipping_cost=o.get("shipping_cost"),
            availability=o["availability"],
            delivery_days=o["delivery_days"],
            specifications=o["specifications"]
        )
        for o in raw_offers
    ]

    assert len(normalized) == 2
    for item in normalized:
        assert item["source_name"] in ["Amazon India", "Dell Technologies Store"]
        assert item["currency"] == "INR"
        assert item["is_external"] is True
        assert item["url"].startswith("http")
        assert item["retrieved_at"] is not None
        assert "verification_status" in item
        assert "unverified_fields" in item

    # Verify calculation: 54990 * 2 + 0 = 109980
    assert normalized[0]["total_cost"] == 109980.0
    # Verify calculation: 58900 * 2 + 500 = 118300
    assert normalized[1]["total_cost"] == 118300.0


# ─── Test 2: Invalid or Missing Prices Are Handled Safely ────────────────────

def test_2_invalid_or_missing_prices_handled_safely():
    """Unlisted, corrupted, or non-numeric prices are handled safely without crashing."""
    norm_missing = normalize_web_offer(
        source_name="Marketplace Portal",
        title="Custom Enterprise Server",
        url="https://example.com/server",
        unit_price=None,
        quantity=5
    )
    assert norm_missing["unit_price"] is None
    assert norm_missing["total_cost"] is None
    assert norm_missing["verification_status"] == "UNVERIFIED"
    assert "unit_price" in norm_missing["unverified_fields"]

    norm_invalid_str = normalize_web_offer(
        source_name="Marketplace Portal",
        title="Custom Server Rack",
        url="https://example.com/rack",
        unit_price="Contact for quote",  # type: ignore
        quantity=1
    )
    assert norm_invalid_str["unit_price"] is None
    assert norm_invalid_str["total_cost"] is None
    assert norm_invalid_str["verification_status"] == "UNVERIFIED"

    norm_negative = normalize_web_offer(
        source_name="Marketplace Portal",
        title="Defective Listing",
        url="https://example.com/bad",
        unit_price=-500.0,
        quantity=1
    )
    assert norm_negative["unit_price"] is None
    assert norm_negative["total_cost"] is None


# ─── Test 3: Different Product Models Are Not Incorrectly Merged ──────────────

def test_3_different_product_models_not_incorrectly_merged():
    """Different models and configurations are kept distinct and not merged during deduplication."""
    offers = [
        normalize_web_offer(
            source_name="Amazon India",
            title="Lenovo ThinkPad E14 Gen 5 (8GB RAM, 256GB SSD)",
            model="ThinkPad E14 8GB",
            url="https://amazon.in/dp/MODEL_8GB",
            unit_price=45000.0,
            specifications={"ram": "8GB", "storage": "256GB"}
        ),
        normalize_web_offer(
            source_name="Amazon India",
            title="Lenovo ThinkPad E14 Gen 5 (16GB RAM, 512GB SSD)",
            model="ThinkPad E14 16GB",
            url="https://amazon.in/dp/MODEL_16GB",
            unit_price=54990.0,
            specifications={"ram": "16GB", "storage": "512GB"}
        ),
        # Identical duplicate listing that SHOULD be deduplicated
        normalize_web_offer(
            source_name="Amazon India",
            title="Lenovo ThinkPad E14 Gen 5 (8GB RAM, 256GB SSD) Duplicate",
            model="ThinkPad E14 8GB",
            url="https://amazon.in/dp/MODEL_8GB",
            unit_price=45000.0,
            specifications={"ram": "8GB", "storage": "256GB"}
        )
    ]

    deduped = deduplicate_and_distinguish_offers(offers)
    assert len(deduped) == 2
    models = [d["model"] for d in deduped]
    assert "ThinkPad E14 8GB" in models
    assert "ThinkPad E14 16GB" in models


# ─── Test 4: Web Offers Are Compared With Internal Supplier Quotes ───────────

def test_4_web_offers_compared_with_internal_supplier_quotes():
    """Procurement Agent compares database catalog quotes with discovered web offers."""
    web_res = discover_online_offers("laptop stand", quantity=2)
    assert web_res["offers_count"] >= 1

    state_mock = {
        "thread_id": "test_comp_thread",
        "product": "laptop stand",
        "quantity_to_order": 2,
        "final_order_quantity": 2,
        "status": "RUNNING",
        "web_offers": web_res["offers"],
        "agent_traces": [],
        "audit_log": []
    }

    from agents.procurement import procurement_node
    updated = procurement_node(dict(state_mock))

    proc_res = updated["procurement_result"]
    assert "quotes_evaluated" in proc_res
    assert len(proc_res["quotes_evaluated"]) > 0
    assert "web_offers_evaluated" in proc_res
    assert len(proc_res["web_offers_evaluated"]) > 0
    assert "online_comparison_summary" in proc_res
    assert len(proc_res["online_comparison_summary"]) > 0
    assert updated["eligible_quotes"] is not None
    assert updated["web_offers"] is not None


# ─── Test 5: Unavailable Delivery Information Is Not Fabricated ──────────────

def test_5_unavailable_delivery_information_not_fabricated():
    """Missing delivery days or unverified shipping costs are preserved as None."""
    offer = normalize_web_offer(
        source_name="Croma",
        title="Enterprise Server Accessory",
        url="https://croma.com/p/123",
        unit_price=1200.0,
        shipping_cost=None,  # Missing shipping cost
        delivery_days=None,  # Missing delivery estimate
        delivery_estimate=None
    )

    assert offer["delivery_days"] is None
    assert offer["shipping_cost"] is None
    assert "shipping_cost" in offer["unverified_fields"]
    assert "delivery_estimate" in offer["unverified_fields"]
    assert offer["delivery_estimate"] == "Unverified"
    assert "Unknown" in offer["shipping_note"]


# ─── Test 6: Search Failures Fall Back Safely to Internal Quotes ─────────────

def test_6_search_failures_fallback_safely_to_internal_quotes():
    """When web research is disabled or yields no results, internal supplier evaluation continues normally."""
    state_mock: WorkflowState = {
        "business_event": "Procure 2 laptop stands with internal suppliers only",
        "intent": "procurement_request",
        "intent_details": {},
        "route_taken": "procurement_flow",
        "status": "RUNNING",
        "error_message": None,
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "product": "laptop stand",
        "deadline": None,
        "department": None,
        "quantity_semantics": "UNSPECIFIED",
        "additional_quantity": None,
        "demand_quantity": None,
        "target_total_stock": None,
        "requested_quantity": 2,
        "current_stock": 5,
        "demand_shortfall": 2,
        "minimum_stock_level": 10,
        "replenishment_quantity": 5,
        "quantity_to_order": 2,
        "business_objective": "Procure items using internal catalog only",
        "needs_clarification": False,
        "clarification_question": None,
        "query_result": None,
        "inventory_sub_intent": None,
        "available_strategies": None,
        "selected_strategy": "meet_demand",
        "final_order_quantity": 2,
        "custom_target_type": None,
        "eligible_quotes": None,
        "recommended_supplier": None,
        "recommended_supplier_name": None,
        "recommended_supplier_quote": None,
        "selected_supplier": None,
        "selected_supplier_name": None,
        "supplier_selection_mode": None,
        "web_research_enabled": False,  # Explicitly disabled
        "web_research_status": None,
        "web_research_summary": None,
        "web_offers": None,
        "external_purchase_selected": False,
        "inventory_result": {},
        "procurement_result": None,
        "finance_result": None,
        "risk_result": None,
        "approval_status": None,
        "approved_transaction": None,
        "execution_result": None,
        "agent_traces": [],
        "audit_log": []
    }

    # Run Web Research Agent node with disabled search
    web_state = web_research_node(dict(state_mock))
    assert web_state["web_research_status"] == "SKIPPED"
    assert web_state["web_offers"] == []

    # Procurement node should still evaluate internal quotes successfully
    from agents.procurement import procurement_node
    proc_state = procurement_node(web_state)

    assert len(proc_state["eligible_quotes"]) > 0
    assert proc_state["procurement_result"]["supplier"] != "N/A"
    assert proc_state["procurement_result"]["total_cost"] > 0


# ─── Test 7: Source URL and Retrieval Timestamp Are Preserved ────────────────

def test_7_source_url_and_retrieval_timestamp_preserved():
    """Source URL and valid ISO timestamp are preserved across all offers."""
    res = discover_online_offers("laptop", quantity=1)
    assert res["offers_count"] > 0

    for offer in res["offers"]:
        assert offer["url"].startswith("http")
        # Timestamp must be parseable ISO format
        dt = datetime.fromisoformat(offer["retrieved_at"].replace("Z", "+00:00"))
        assert dt is not None
        assert offer["data_source"].startswith("WEB_SEARCH::")


# ─── Test 8: Read-Only Queries Do Not Trigger Web Research ───────────────────

def test_8_read_only_queries_do_not_trigger_web_research():
    """Read-only questions (inventory, budget, supplier, PO) must not trigger web research."""
    read_only_queries = [
        "How many laptops are in inventory?",
        "How much budget is left?",
        "Who are the suppliers for Laptop Stand?",
        "What is the status of PO-2026-001?"
    ]

    for q in read_only_queries:
        res = client.post("/api/workflow/run", json={"business_event": q})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "QUERY_ANSWERED"
        # Web offers must not be populated
        assert data.get("web_offers") == []
        # Agent traces must not contain Web Research Agent
        trace_agents = [t["agent_name"] for t in data["state"].get("agent_traces", [])]
        assert "Web Research Agent" not in trace_agents


# ─── Test 9: Budget and Approval Safeguards Enforced for Web Offers ───────────

def test_9_budget_and_approval_safeguards_enforced_for_web_offers():
    """Hard ₹100,000 budget cap and mandatory human approval apply equally to external web offers."""
    web_offer = normalize_web_offer(
        source_name="Amazon India",
        title="High-End Workstation Laptop",
        url="https://amazon.in/dp/HIGH_END",
        unit_price=60000.0,
        quantity=2  # Total: 120,000 > ₹100k cap
    )

    state_mock = {
        "product": "laptop",
        "current_stock": 2,
        "minimum_stock_level": 10,
        "quantity_to_order": 2,
        "final_order_quantity": 2,
        "selected_strategy": "meet_demand",
        "selected_supplier_name": web_offer["name"],
        "web_offers": [web_offer],
        "eligible_quotes": [],
        "approval_status": "APPROVED",
        "audit_log": [],
        "procurement_result": {}
    }

    # Configuration with order amount 120,000 must be BLOCKED
    updated = configure_procurement_decision(
        state=dict(state_mock),
        selected_strategy="meet_demand",
        final_order_quantity=2,
        selected_supplier_name=web_offer["name"]
    )

    assert updated["status"] == "BLOCKED"
    assert updated["risk_result"]["level"] == "BLOCKED"
    assert updated["approval_status"] is None  # Invalidated!
    assert updated["external_purchase_selected"] is True


# ─── Test 10: Web Offers Cannot Cause Automated External Purchase ────────────

def test_10_web_offers_cannot_cause_automated_external_purchase():
    """Approving an external web offer authorizes checkout but does not fake an external PO creation."""
    web_offer = normalize_web_offer(
        source_name="Reliance Digital",
        title="HP ProBook 440 G10 Business Laptop",
        url="https://www.reliancedigital.in/hp-probook/p/493839201",
        unit_price=45000.0,
        quantity=1
    )

    state_mock: WorkflowState = {
        "business_event": "Order 1 HP ProBook laptop",
        "intent": "procurement_request",
        "intent_details": {},
        "route_taken": "procurement_flow",
        "status": "PAUSED_FOR_APPROVAL",
        "error_message": None,
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "product": "laptop",
        "deadline": None,
        "department": None,
        "quantity_semantics": "UNSPECIFIED",
        "additional_quantity": None,
        "demand_quantity": None,
        "target_total_stock": None,
        "requested_quantity": 1,
        "current_stock": 0,
        "demand_shortfall": 1,
        "minimum_stock_level": 10,
        "replenishment_quantity": 10,
        "quantity_to_order": 1,
        "business_objective": "Procure laptop",
        "needs_clarification": False,
        "clarification_question": None,
        "query_result": None,
        "inventory_sub_intent": None,
        "available_strategies": None,
        "selected_strategy": "meet_demand",
        "final_order_quantity": 1,
        "custom_target_type": None,
        "eligible_quotes": [],
        "recommended_supplier": web_offer["name"],
        "recommended_supplier_name": web_offer["name"],
        "recommended_supplier_quote": web_offer,
        "selected_supplier": web_offer,
        "selected_supplier_name": web_offer["name"],
        "supplier_selection_mode": "MANUAL",
        "web_research_enabled": True,
        "web_research_status": "COMPLETED",
        "web_research_summary": "Discovered online offer",
        "web_offers": [web_offer],
        "external_purchase_selected": True,
        "inventory_result": {},
        "procurement_result": {
            "supplier": web_offer["name"],
            "unit_price": 45000.0,
            "quantity": 1,
            "total_cost": 45000.0,
            "is_external": True,
            "external_checkout_url": web_offer["url"]
        },
        "finance_result": {"status": "APPROVED"},
        "risk_result": {"level": "LOW"},
        "approval_status": "APPROVED",
        "approved_transaction": {
            "supplier": web_offer["name"],
            "product": "laptop",
            "quantity": 1,
            "total_cost": 45000.0
        },
        "execution_result": None,
        "agent_traces": [],
        "audit_log": []
    }

    from agents.execution import execution_node
    final_state = execution_node(dict(state_mock))

    exec_res = final_state["execution_result"]
    assert exec_res is not None
    # Must NOT pretend to have created a standard database PO
    assert exec_res["status"] == "EXTERNAL_CHECKOUT_REQUIRED"
    assert exec_res["action_required"] == "OPEN_PRODUCT_PAGE"
    assert exec_res["external_url"] == web_offer["url"]
    assert exec_res["is_external"] is True
    assert "EXTERNAL PURCHASE AUTHORIZED" in final_state["audit_log"][-1]
