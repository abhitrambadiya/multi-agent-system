from typing import Optional, List, Dict, Any
from graph.state import WorkflowState, AgentTrace
from tools.supplier_tool import get_suppliers
from llm_utils import invoke_llm_structured
from pydantic import BaseModel, Field

class ProcurementOutput(BaseModel):
    selected_supplier_name: str = Field(description="The exact name of the selected supplier from the database quotes")
    evaluation_summary: str = Field(description="Comparison of supplier pricing, delivery lead times, stock availability, and ratings")
    decision_rationale: str = Field(description="Clear explanation of why this vendor was chosen")

def procurement_node(state: WorkflowState) -> WorkflowState:
    if state.get("status") in ["FAILED", "NEEDS_CLARIFICATION"]:
        return state
        
    product = state.get("product", "Unknown")
    # Procure the quantity_to_order calculated by Inventory Agent
    qty = state.get("quantity_to_order", 0)
    
    if qty <= 0:
        state["procurement_result"] = {
            "supplier": "N/A",
            "unit_price": 0,
            "quantity": 0,
            "total_cost": 0,
            "status": "SKIPPED_SUFFICIENT_STOCK",
            "data_source": "inventory_check"
        }
        trace: AgentTrace = {
            "agent_name": "Procurement Agent",
            "status": "SUCCESS",
            "llm_mode": "DETERMINISTIC_FALLBACK",
            "input_data": {"product": product, "quantity_to_order": 0},
            "decision": "Order quantity is 0 (current stock satisfies demand). Procurement skipped.",
            "tools_used": [],
            "tool_data": None,
            "evidence": {"quantity": 0},
            "output_data": {"status": "SKIPPED_SUFFICIENT_STOCK"}
        }
        state["agent_traces"].append(trace)
        return state

    # 1. Query real database supplier records (Internal Approved Suppliers)
    suppliers = get_suppliers(product)
    
    # Calculate total price for selected quantity on each internal vendor quote
    for s in suppliers:
        s["total_price"] = s["unit_price"] * qty
        s["currency"] = s.get("currency", "INR")
        s["reliability_score"] = s.get("reliability_score", round(s.get("rating", 4.5) / 5.0, 2))
        s["is_external"] = False

    # 2. Incorporate public web research offers (Marketplace Comparison)
    web_offers = state.get("web_offers") or []
    for w in web_offers:
        w["is_external"] = True
        if w.get("unit_price") is not None:
            ship = w.get("shipping_cost") or 0.0
            tax = w.get("taxes_and_fees") or 0.0
            w["total_cost"] = round(w["unit_price"] * qty + ship + tax, 2)
            w["total_price"] = w["total_cost"]

    # Transparent multi-criteria recommendation ranking for internal database suppliers
    sorted_quotes = sorted(
        suppliers,
        key=lambda x: (not x.get("in_stock", True), x["unit_price"], x.get("delivery_days", 99), -x.get("rating", 0.0))
    )
    recommended_vendor = sorted_quotes[0] if sorted_quotes else {
        "name": "N/A", "unit_price": 0, "total_price": 0, "delivery_days": 0, "rating": 0.0, "currency": "INR", "in_stock": False
    }

    has_three_or_more = len(suppliers) >= 3
    if has_three_or_more:
        supplier_options_note = f"Found {len(suppliers)} eligible supplier quotes from PostgreSQL database."
    else:
        supplier_options_note = f"Notice: Only {len(suppliers)} eligible supplier(s) registered in database catalog (< 3 target). Displaying all verified quotes."

    # Comparative market intelligence between internal quotes and online web offers
    comparison_notes: List[str] = []
    if web_offers:
        valid_web = [w for w in web_offers if w.get("unit_price") is not None and w.get("in_stock")]
        if valid_web:
            cheapest_web = min(valid_web, key=lambda x: x["unit_price"])
            if recommended_vendor.get("unit_price"):
                diff = recommended_vendor["unit_price"] - cheapest_web["unit_price"]
                if diff > 0:
                    comparison_notes.append(
                        f"Marketplace Analysis: Lowest online offer on {cheapest_web['source_name']} ({cheapest_web['model']}) "
                        f"is listed @ ₹{cheapest_web['unit_price']:,}/unit (Potential unit savings: ₹{diff:,}). "
                        f"Internal vendor '{recommended_vendor['name']}' @ ₹{recommended_vendor['unit_price']:,}/unit provides verified corporate contract terms."
                    )
                elif diff < 0:
                    comparison_notes.append(
                        f"Marketplace Analysis: Internal vendor '{recommended_vendor['name']}' @ ₹{recommended_vendor['unit_price']:,}/unit "
                        f"is ₹{abs(diff):,}/unit cheaper than the lowest online offer on {cheapest_web['source_name']} (₹{cheapest_web['unit_price']:,})."
                    )
                else:
                    comparison_notes.append(
                        f"Marketplace Analysis: Internal vendor pricing exactly matches lowest online listing on {cheapest_web['source_name']}."
                    )

    online_comparison_summary = " ".join(comparison_notes) if comparison_notes else "Online price comparison: No public marketplace alternatives matched criteria."

    system_prompt = (
        "You are an enterprise Procurement Agent. Evaluate quotes from registered database suppliers and compare with online market research. "
        "Transparently compare price, delivery lead times, stock availability, and reliability ratings. "
        "State your transparent recommendation while acknowledging that the human buyer will make the final selection."
    )
    user_prompt = (
        f"Product: {product}. Order volume: {qty} units. "
        f"Registered Suppliers from Database: {suppliers}. "
        f"Web Research Offers: {web_offers[:3]}. "
        f"Target recommendation criteria: in_stock confirmed, lowest unit price, fastest delivery, highest reliability."
    )
    
    result, mode, err = invoke_llm_structured(system_prompt, user_prompt, ProcurementOutput)
    
    if result is not None:
        llm_mode = "LIVE_LLM"
        eval_summary = result.evaluation_summary
        rationale = result.decision_rationale
    else:
        llm_mode = "DETERMINISTIC_FALLBACK"
        eval_summary = f"Evaluated {len(suppliers)} database vendors and {len(web_offers)} online marketplace offers. {supplier_options_note}"
        rationale = f"Recommended '{recommended_vendor['name']}' based on best balance of price (₹{recommended_vendor['unit_price']:,}) and lead time ({recommended_vendor.get('delivery_days', 2)} days)."

    # Buyer-controlled vendor selection
    sel_sup = state.get("selected_supplier")
    if isinstance(sel_sup, str):
        sel_name = sel_sup
    elif isinstance(sel_sup, dict):
        sel_name = sel_sup.get("name")
    else:
        sel_name = None
    user_chosen_name = state.get("selected_supplier_name") or sel_name
    active_supplier = None
    selection_mode = "RECOMMENDED"
    is_external_selected = False

    if user_chosen_name:
        # Check internal suppliers first
        for s in suppliers:
            if s["name"].lower() == user_chosen_name.strip().lower():
                active_supplier = s
                selection_mode = "MANUAL"
                is_external_selected = False
                break
        # Check web offers if not found in internal suppliers
        if not active_supplier and web_offers:
            for w in web_offers:
                if (
                    w.get("name", "").lower() == user_chosen_name.strip().lower()
                    or w.get("offer_id", "").lower() == user_chosen_name.strip().lower()
                    or w.get("source_name", "").lower() == user_chosen_name.strip().lower()
                    or user_chosen_name.strip().lower() in w.get("title", "").lower()
                ):
                    active_supplier = w
                    selection_mode = "MANUAL"
                    is_external_selected = True
                    break

    if not active_supplier:
        active_supplier = recommended_vendor
        selection_mode = "RECOMMENDED"
        is_external_selected = False

    unit_price = active_supplier.get("unit_price", 0)
    shipping = active_supplier.get("shipping_cost") or 0.0
    tax = active_supplier.get("taxes_and_fees") or 0.0
    total_cost = round((unit_price * qty) + shipping + tax, 2)
    
    procurement_result = {
        "supplier": active_supplier["name"],
        "unit_price": unit_price,
        "quantity": qty,
        "total_cost": total_cost,
        "currency": active_supplier.get("currency", "INR"),
        "delivery_days": active_supplier.get("delivery_days", 2),
        "rating": active_supplier.get("rating", 4.5),
        "reliability_score": active_supplier.get("reliability_score", 0.95),
        "in_stock": active_supplier.get("in_stock", True),
        "quotes_evaluated": suppliers,
        "web_offers_evaluated": web_offers,
        "online_comparison_summary": online_comparison_summary,
        "recommended_supplier": recommended_vendor["name"],
        "recommendation_rationale": rationale,
        "supplier_selection_mode": selection_mode,
        "supplier_options_note": supplier_options_note,
        "has_target_supplier_count": has_three_or_more,
        "data_source": active_supplier.get("data_source", "database::supplier_quotes"),
        "is_external": is_external_selected,
        "external_checkout_url": active_supplier.get("external_checkout_url") or active_supplier.get("url")
    }

    state["eligible_quotes"] = suppliers
    state["web_offers"] = web_offers
    state["recommended_supplier"] = recommended_vendor["name"]
    state["recommended_supplier_name"] = recommended_vendor["name"]
    state["recommended_supplier_quote"] = recommended_vendor
    state["selected_supplier"] = active_supplier
    state["selected_supplier_name"] = active_supplier["name"]
    state["supplier_selection_mode"] = selection_mode
    state["external_purchase_selected"] = is_external_selected
    state["procurement_result"] = procurement_result
    
    decision_text = (
        f"SUPPLIER EVALUATION COMPLETED: {len(suppliers)} internal quote(s) and {len(web_offers)} web offer(s) evaluated. "
        f"AI Recommendation: '{recommended_vendor['name']}'. "
        f"Active Selection ({selection_mode}): '{active_supplier['name']}' @ ₹{unit_price:,}/unit. "
        f"Total procurement cost for {qty} units: ₹{total_cost:,}. "
        f"Lead Time: {active_supplier.get('delivery_days', 2)} days (Rating: {active_supplier.get('rating', 4.5)}/5.0). "
        f"{eval_summary} {rationale} {online_comparison_summary}"
    )
    
    trace: AgentTrace = {
        "agent_name": "Procurement Agent",
        "status": "SUCCESS",
        "llm_mode": llm_mode,
        "input_data": {
            "product": product,
            "quantity_to_order": qty,
            "quotes_count": len(suppliers),
            "web_offers_count": len(web_offers),
            "selection_mode": selection_mode
        },
        "decision": decision_text,
        "tools_used": ["database::supplier_quotes", "web_comparison_engine"],
        "tool_data": {
            "selected_vendor": active_supplier["name"],
            "unit_price": unit_price,
            "total_cost": total_cost,
            "recommended_vendor": recommended_vendor["name"],
            "quotes_count": len(suppliers),
            "web_offers_count": len(web_offers)
        },
        "evidence": {
            "selected_supplier": active_supplier["name"],
            "recommended_supplier": recommended_vendor["name"],
            "unit_price": unit_price,
            "total_cost": total_cost,
            "quotes_evaluated": suppliers,
            "web_offers_evaluated": web_offers,
            "is_external": is_external_selected,
            "has_target_supplier_count": has_three_or_more
        },
        "output_data": procurement_result
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Procurement Agent]\n{decision_text}")
    return state

def configure_procurement_decision(
    state: WorkflowState,
    selected_strategy: Optional[str] = None,
    final_order_quantity: Optional[int] = None,
    selected_supplier_name: Optional[str] = None,
    custom_target_type: Optional[str] = None
) -> WorkflowState:
    """
    Recalculates cost and validates budget whenever the user changes the strategy, quantity, or supplier.
    Never trusts frontend-submitted prices or totals.
    Supports selecting either internal PostgreSQL suppliers or external web offers.
    Invalidates any previous approval since material transaction details changed.
    """
    from tools.finance_tool import check_budget

    # Invalidate previous approval if material parameters change
    material_change = False
    if selected_strategy and selected_strategy != state.get("selected_strategy"):
        material_change = True
    if final_order_quantity is not None and final_order_quantity != state.get("final_order_quantity"):
        material_change = True
    if selected_supplier_name and selected_supplier_name != state.get("selected_supplier_name"):
        material_change = True

    if material_change and state.get("approval_status") == "APPROVED":
        state["approval_status"] = None
        state["approved_transaction"] = None
        state["audit_log"].append(
            "[System Guard] Transaction parameters updated by buyer. Previous human approval invalidated. Re-approval required."
        )

    if custom_target_type:
        state["custom_target_type"] = custom_target_type

    # Current usable inventory and thresholds from state
    current_stock = state.get("current_stock")
    if current_stock is None:
        current_stock = state.get("inventory_result", {}).get("current_stock", 0)

    min_stock = state.get("minimum_stock_level")
    if min_stock is None:
        min_stock = state.get("inventory_result", {}).get("minimum_stock_level", 0)

    qty_sem = state.get("quantity_semantics", "UNSPECIFIED")
    additional_qty = state.get("additional_quantity")
    demand_qty = state.get("demand_quantity")
    requested_qty = state.get("requested_quantity")

    # 1. Update Strategy and Quantity
    if selected_strategy:
        state["selected_strategy"] = selected_strategy
        if selected_strategy == "meet_demand":
            if qty_sem == "ADDITIONAL_QUANTITY" or additional_qty is not None:
                qty = additional_qty if additional_qty is not None else (requested_qty or 1)
            elif qty_sem == "TOTAL_DEMAND" or demand_qty is not None:
                total_needed = demand_qty if demand_qty is not None else (requested_qty or 1)
                qty = max(0, total_needed - current_stock)
            else:
                qty = state.get("demand_shortfall") if state.get("demand_shortfall") is not None else (final_order_quantity or state.get("final_order_quantity") or state.get("quantity_to_order") or requested_qty or 1)
        elif selected_strategy == "restore_safety_stock":
            qty = max(0, min_stock - current_stock)
            state["replenishment_quantity"] = qty
        elif selected_strategy == "custom":
            target_mode = custom_target_type or state.get("custom_target_type", "PURCHASE_QUANTITY")
            input_val = final_order_quantity if final_order_quantity is not None else (state.get("final_order_quantity") or 1)
            if target_mode == "TARGET_TOTAL_STOCK":
                qty = max(0, input_val - current_stock)
            else:
                qty = input_val
        else:
            qty = final_order_quantity or state.get("final_order_quantity") or 1
    elif final_order_quantity is not None:
        target_mode = custom_target_type or state.get("custom_target_type", "PURCHASE_QUANTITY")
        if target_mode == "TARGET_TOTAL_STOCK":
            qty = max(0, final_order_quantity - current_stock)
        else:
            qty = final_order_quantity
        state["selected_strategy"] = "custom"
    else:
        qty = state.get("final_order_quantity") or state.get("quantity_to_order") or 1

    state["final_order_quantity"] = qty
    state["quantity_to_order"] = qty

    # 2. Update Supplier from internal PostgreSQL records or web offers
    product = state.get("product", "")
    quotes = get_suppliers(product)
    web_offers = state.get("web_offers") or []

    # Re-calculate web offer totals for new quantity
    for w in web_offers:
        w["is_external"] = True
        if w.get("unit_price") is not None:
            ship = w.get("shipping_cost") or 0.0
            tax = w.get("taxes_and_fees") or 0.0
            w["total_cost"] = round(w["unit_price"] * qty + ship + tax, 2)
            w["total_price"] = w["total_cost"]
    state["web_offers"] = web_offers

    target_name = selected_supplier_name or state.get("selected_supplier_name") or state.get("procurement_result", {}).get("supplier")
    
    matched = None
    is_external = False

    # Check internal quotes first
    if target_name:
        for q in quotes:
            if q["name"].lower() == target_name.strip().lower():
                matched = q
                is_external = False
                break
    
    # Check web offers if not matched in internal quotes
    if not matched and target_name and web_offers:
        for w in web_offers:
            if (
                w.get("name", "").lower() == target_name.strip().lower()
                or w.get("offer_id", "").lower() == target_name.strip().lower()
                or w.get("source_name", "").lower() == target_name.strip().lower()
                or target_name.strip().lower() in w.get("title", "").lower()
            ):
                matched = w
                is_external = True
                break

    if not matched and quotes:
        matched = quotes[0]
        is_external = False

    if matched:
        unit_price = matched.get("unit_price", 0)
        shipping = matched.get("shipping_cost") or 0.0
        tax = matched.get("taxes_and_fees") or 0.0
        total_cost = round((unit_price * qty) + shipping + tax, 2)
        
        # Update internal quotes total_price
        for q in quotes:
            q["total_price"] = q["unit_price"] * qty
            q["currency"] = q.get("currency", "INR")
            q["reliability_score"] = q.get("reliability_score", round(q.get("rating", 4.5) / 5.0, 2))
            q["is_external"] = False

        state["eligible_quotes"] = quotes
        state["selected_supplier"] = matched
        state["selected_supplier_name"] = matched["name"]
        state["external_purchase_selected"] = is_external
        if selected_supplier_name:
            state["supplier_selection_mode"] = "MANUAL"

        proc_res = state.get("procurement_result", {})
        proc_res.update({
            "supplier": matched["name"],
            "unit_price": unit_price,
            "quantity": qty,
            "total_cost": total_cost,
            "currency": matched.get("currency", "INR"),
            "delivery_days": matched.get("delivery_days", 2),
            "rating": matched.get("rating", 4.5),
            "reliability_score": matched.get("reliability_score", 0.95),
            "in_stock": matched.get("in_stock", True),
            "quotes_evaluated": quotes,
            "web_offers_evaluated": web_offers,
            "is_external": is_external,
            "external_checkout_url": matched.get("external_checkout_url") or matched.get("url"),
            "supplier_selection_mode": state.get("supplier_selection_mode", "RECOMMENDED")
        })
        state["procurement_result"] = proc_res

        # 3. Recalculate Finance Budget & Risk
        fin_res = check_budget(total_cost)
        state["finance_result"] = fin_res

        if total_cost > 100000 or fin_res["status"] == "REJECTED":
            state["status"] = "BLOCKED"
            state["approval_status"] = None
            state["approved_transaction"] = None
            state["risk_result"] = {
                "level": "BLOCKED",
                "policy_outcome": "BLOCKED_BUDGET_CAP",
                "threshold": 50000,
                "budget_cap": 100000,
                "order_amount": total_cost,
                "mandatory_approval": True,
                "reason": f"Order cost of ₹{total_cost:,} exceeds corporate limit of ₹100,000."
            }
        else:
            state["status"] = "PAUSED_FOR_APPROVAL"
            state["risk_result"] = {
                "level": "HIGH" if total_cost >= 50000 else "LOW",
                "policy_outcome": "PENDING_HUMAN_APPROVAL",
                "threshold": 50000,
                "budget_cap": 100000,
                "order_amount": total_cost,
                "mandatory_approval": True
            }

        vendor_origin = "Online Marketplace" if is_external else "Internal Catalog"
        state["audit_log"].append(
            f"[Decision Update] Configured strategy '{state.get('selected_strategy')}' -> {qty} units with [{vendor_origin}] '{matched['name']}' @ ₹{unit_price:,}/unit. Total: ₹{total_cost:,}."
        )

    return state
