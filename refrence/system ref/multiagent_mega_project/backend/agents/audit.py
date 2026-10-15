from graph.state import WorkflowState, AgentTrace
from database.db import insert_audit_entry

def audit_node(state: WorkflowState) -> WorkflowState:
    status = state.get("status", "COMPLETED")
    intent = state.get("intent", "UNKNOWN")
    product = state.get("product", "N/A")
    cost = state.get("procurement_result", {}).get("total_cost", 0)
    supplier = state.get("procurement_result", {}).get("supplier", "N/A")
    po_id = state.get("execution_result", {}).get("po_id", "NONE")
    approval = state.get("approval_status", "N/A")
    risk_level = state.get("risk_result", {}).get("level", "N/A")
    thread_id = state.get("thread_id", "direct")
    
    if intent in ["inventory_query", "supplier_query", "budget_query", "purchase_order_query", "risk_query"]:
        summary = (
            f"AUDIT TRAIL FINALIZED: Read-only query '{intent}' resolved successfully.\n"
            f"• Workflow Outcome: {status}\n"
            f"• Data Source: Real Database Records\n"
            f"• Purchase Order Created: None (Read-only execution safeguard)"
        )
    elif status == "NEEDS_CLARIFICATION":
        summary = (
            f"AUDIT TRAIL FINALIZED: Workflow requires user clarification.\n"
            f"• Clarification Question: {state.get('clarification_question')}\n"
            f"• Purchase Order Created: None"
        )
    elif status == "FAILED":
        summary = (
            f"AUDIT TRAIL FINALIZED: Workflow terminated with status 'FAILED'.\n"
            f"• Reason: {state.get('error_message', 'Out of scope or validation error')}\n"
            f"• Purchase Order Created: None"
        )
    else:
        summary = (
            f"AUDIT TRAIL FINALIZED: Procurement workflow concluded with status '{status}'.\n"
            f"• Product: {product}\n"
            f"• Selected Vendor: {supplier}\n"
            f"• Total Order Cost: ₹{cost:,}\n"
            f"• Governance Risk Tier: {risk_level}\n"
            f"• Human Approval Decision: {approval}\n"
            f"• Purchase Order ID: {po_id}"
        )
    
    # Persist audit entry in database
    try:
        insert_audit_entry(
            thread_id=thread_id,
            agent_name="Audit Agent",
            status=status,
            llm_mode=state.get("llm_mode", "DETERMINISTIC_FALLBACK"),
            decision=summary
        )
    except Exception:
        pass

    trace: AgentTrace = {
        "agent_name": "Audit Agent",
        "status": status,
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {
            "workflow_status": status,
            "intent": intent,
            "product": product,
            "total_cost": f"₹{cost:,}" if cost else "N/A",
            "purchase_order": po_id
        },
        "decision": summary,
        "tools_used": ["database::audit_logs"],
        "tool_data": {
            "status": status,
            "intent": intent,
            "po_id": po_id,
            "data_source": "database::audit_logs"
        },
        "evidence": {
            "final_status": status,
            "po_created": bool(po_id != "NONE"),
            "total_agent_steps": len(state.get("agent_traces", []))
        },
        "output_data": {
            "status": status,
            "po_id": po_id
        }
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Audit Logger]\n{summary}")
    return state
