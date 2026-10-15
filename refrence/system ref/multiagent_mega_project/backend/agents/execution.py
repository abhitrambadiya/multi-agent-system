import uuid
from datetime import datetime, timezone
from graph.state import WorkflowState, AgentTrace
from tools.purchase_tool import execute_purchase

def execution_node(state: WorkflowState) -> WorkflowState:
    # Guard 1: Prevent duplicate execution
    if state.get("execution_result") is not None:
        return state
        
    # Guard 2: Workflow status check
    if state.get("status") in ["FAILED", "BLOCKED", "REJECTED", "QUERY_ANSWERED", "NEEDS_CLARIFICATION"]:
        return state
        
    # Guard 3: Budget and policy validation (never exceed ₹100,000 corporate cap)
    cost = state.get("procurement_result", {}).get("total_cost", 0)
    finance_status = state.get("finance_result", {}).get("status")
    risk_level = state.get("risk_result", {}).get("level")
    
    if finance_status != "APPROVED" or cost > 100000 or risk_level == "BLOCKED":
        return state
        
    # Guard 4: Mandatory Human-in-the-Loop approval check for EVERY purchase
    approval_status = state.get("approval_status")
    if approval_status != "APPROVED":
        return state
        
    supplier = state.get("procurement_result", {}).get("supplier")
    product = state.get("product")
    qty = state.get("procurement_result", {}).get("quantity", 0)
    approved_txn = state.get("approved_transaction")
    
    # Guard 5: Approved details matching guard
    if not approved_txn or not supplier or not product or qty <= 0:
        return state
        
    if (
        approved_txn.get("supplier") != supplier
        or approved_txn.get("product", "").strip().lower() != product.strip().lower()
        or approved_txn.get("quantity") != qty
        or approved_txn.get("total_cost") != cost
    ):
        # Transaction discrepancy detected: abort execution
        return state

    is_external = state.get("external_purchase_selected") or state.get("procurement_result", {}).get("is_external", False)

    # ── External Web Offer Execution Branch ───────────────────────────────────
    # For online retailers without an authorized automated purchasing API,
    # the supervisor authorizes the purchase and provides the verified product link for manual completion.
    # Never pretends to have placed an automated order on an external website.
    if is_external:
        po_id = f"EXT-AUTH-{uuid.uuid4().hex[:8].upper()}"
        external_url = (
            state.get("procurement_result", {}).get("external_checkout_url")
            or state.get("selected_supplier", {}).get("url")
            or state.get("selected_supplier", {}).get("external_checkout_url")
            or ""
        )
        source_platform = state.get("selected_supplier", {}).get("source_name") or supplier

        ext_result = {
            "po_id": po_id,
            "thread_id": state.get("thread_id", "direct_exec"),
            "supplier": supplier,
            "platform": source_platform,
            "product": product,
            "quantity": qty,
            "unit_price": state.get("procurement_result", {}).get("unit_price", 0),
            "total_cost": cost,
            "currency": "INR",
            "status": "EXTERNAL_CHECKOUT_REQUIRED",
            "action_required": "OPEN_PRODUCT_PAGE",
            "external_url": external_url,
            "data_source": state.get("procurement_result", {}).get("data_source", "WEB_OFFER"),
            "is_external": True,
            "message": (
                f"Purchase of {qty} unit(s) authorized by Human Supervisor. "
                f"Automated third-party order placement is disabled for security. "
                f"Please open the merchant listing and complete checkout on {source_platform}."
            ),
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        state["execution_result"] = ext_result
        state["status"] = "COMPLETED"

        decision_text = (
            f"EXTERNAL PURCHASE AUTHORIZED: Supervisor authorized {qty} units of '{product}' via '{supplier}'. "
            f"Total Authorized: ₹{cost:,}. Status: EXTERNAL_CHECKOUT_REQUIRED. "
            f"Action: Buyer must complete order externally via verified product URL: {external_url}."
        )

        trace: AgentTrace = {
            "agent_name": "Execution Agent",
            "status": "SUCCESS",
            "llm_mode": "DETERMINISTIC_FALLBACK",
            "input_data": {
                "supplier": supplier,
                "platform": source_platform,
                "product": product,
                "quantity": qty,
                "total_cost": f"₹{cost:,}",
                "authorized_by": "Human Supervisor",
                "is_external": True
            },
            "decision": decision_text,
            "tools_used": ["external_checkout_referral"],
            "tool_data": ext_result,
            "evidence": {
                "po_id": po_id,
                "external_url": external_url,
                "matching_validation": "PASSED - parameters match supervisor authorization",
                "integration_type": "MANUAL_EXTERNAL_CHECKOUT"
            },
            "output_data": ext_result
        }
        state["agent_traces"].append(trace)

        log_text = (
            f"[Execution Agent] (EXTERNAL PURCHASE AUTHORIZED)\n"
            f"Auth Reference: {po_id}\n"
            f"Retailer: {supplier} | Product: {product} | Quantity: {qty} | Total: ₹{cost:,}\n"
            f"Action: Complete checkout externally at {external_url} (No automated API order placed)."
        )
        state["audit_log"].append(log_text)
        return state

    # ── Internal Supplier Execution Branch (PostgreSQL Purchase Order) ────────
    po_result = execute_purchase(
        supplier=supplier,
        product=product,
        quantity=qty,
        cost=cost,
        thread_id=state.get("thread_id", "direct_exec")
    )
    state["execution_result"] = po_result
    state["status"] = "COMPLETED"
    
    decision_text = (
        f"PURCHASE ORDER ISSUED: Created order reference {po_result['po_id']} with vendor '{supplier}'. "
        f"Quantity: {qty} units | Total Amount: ₹{cost:,}. Status: {po_result['status']}."
    )
    
    trace: AgentTrace = {
        "agent_name": "Execution Agent",
        "status": "SUCCESS",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {
            "supplier": supplier,
            "product": product,
            "quantity": qty,
            "total_cost": f"₹{cost:,}",
            "authorized_by": "Human Supervisor"
        },
        "decision": decision_text,
        "tools_used": ["database::purchase_orders"],
        "tool_data": po_result,
        "evidence": {
            "po_id": po_result["po_id"],
            "currency": po_result.get("currency", "INR"),
            "data_source": po_result.get("data_source"),
            "matching_validation": "PASSED - parameters match supervisor authorization"
        },
        "output_data": po_result
    }
    state["agent_traces"].append(trace)
    
    log_text = (
        f"[Execution Agent] (TRANSACTION FINALIZED)\n"
        f"PO Reference: {po_result['po_id']}\n"
        f"Vendor: {supplier} | Product: {product} | Quantity: {qty} | Total: ₹{cost:,}"
    )
    state["audit_log"].append(log_text)
    
    return state
