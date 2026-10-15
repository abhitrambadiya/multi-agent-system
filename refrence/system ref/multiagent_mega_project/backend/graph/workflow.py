from langgraph.graph import StateGraph, START, END
from graph.state import WorkflowState, AgentTrace
from agents.manager import manager_node
from agents.inventory import inventory_node
from agents.web_research import web_research_node
from agents.procurement import procurement_node
from agents.finance import finance_node
from agents.risk import risk_node
from agents.execution import execution_node
from agents.audit import audit_node
from tools.inventory_tool import query_inventory_direct
from tools.supplier_tool import query_suppliers_direct
from tools.finance_tool import query_budget_direct
from tools.purchase_tool import query_purchase_orders_direct
from langgraph.checkpoint.memory import MemorySaver

# ─── Read-Only Query Direct Nodes ─────────────────────────────────────────────

def inventory_direct_node(state: WorkflowState) -> WorkflowState:
    product = state.get("product")
    sub_intent = state.get("inventory_sub_intent", "current_count")
    stated_demand = state.get("requested_quantity")
    res = query_inventory_direct(product, sub_intent=sub_intent, stated_demand=stated_demand)
    state["query_result"] = res
    state["status"] = "QUERY_ANSWERED"
    state["route_taken"] = "inventory_query"
    
    trace: AgentTrace = {
        "agent_name": "Inventory Agent",
        "status": "QUERY_ANSWERED",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {"product_query": product},
        "decision": res["summary"],
        "tools_used": ["database::inventory_items"],
        "tool_data": res,
        "evidence": {"query_type": "read_only_inventory", "data_source": res.get("data_source")},
        "output_data": res
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Inventory Agent - Query Response]\n{res['summary']}")
    return state

def supplier_direct_node(state: WorkflowState) -> WorkflowState:
    product = state.get("product")
    res = query_suppliers_direct(product)
    state["query_result"] = res
    state["status"] = "QUERY_ANSWERED"
    state["route_taken"] = "supplier_query"
    
    trace: AgentTrace = {
        "agent_name": "Procurement Agent",
        "status": "QUERY_ANSWERED",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {"product_query": product},
        "decision": res["summary"],
        "tools_used": ["database::supplier_quotes"],
        "tool_data": res,
        "evidence": {"query_type": "read_only_suppliers"},
        "output_data": res
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Procurement Agent - Supplier Query Response]\n{res['summary']}")
    return state

def budget_direct_node(state: WorkflowState) -> WorkflowState:
    res = query_budget_direct()
    state["query_result"] = res
    state["status"] = "QUERY_ANSWERED"
    state["route_taken"] = "budget_query"
    
    trace: AgentTrace = {
        "agent_name": "Finance Agent",
        "status": "QUERY_ANSWERED",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {"budget_inquiry": "fiscal_balance"},
        "decision": res["summary"],
        "tools_used": ["database::finance_budgets"],
        "tool_data": res,
        "evidence": {"query_type": "read_only_budget", "data_source": res.get("data_source")},
        "output_data": res
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Finance Agent - Budget Query Response]\n{res['summary']}")
    return state

def po_direct_node(state: WorkflowState) -> WorkflowState:
    import re
    text = state.get("business_event", "")
    po_m = re.search(r"(PO-[\w-]+)", text, re.IGNORECASE)
    po_id = po_m.group(1) if po_m else None
    
    res = query_purchase_orders_direct(po_id)
    state["query_result"] = res
    state["status"] = "QUERY_ANSWERED"
    state["route_taken"] = "purchase_order_query"
    
    trace: AgentTrace = {
        "agent_name": "Execution Agent",
        "status": "QUERY_ANSWERED",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {"po_id": po_id},
        "decision": res["summary"],
        "tools_used": ["database::purchase_orders"],
        "tool_data": res,
        "evidence": {"query_type": "read_only_purchase_orders"},
        "output_data": res
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Execution Agent - PO Query Response]\n{res['summary']}")
    return state

def risk_direct_node(state: WorkflowState) -> WorkflowState:
    summary = (
        "AI-EOS Risk & Compliance Policy: Mandatory human supervisor approval is required for EVERY purchase order. "
        "Transactions < ₹50,000 are classified as LOW RISK. Transactions between ₹50,000 and ₹100,000 are HIGH RISK. "
        "Hard budget ceiling is ₹100,000; transactions exceeding ₹100,000 are strictly BLOCKED and cannot be approved."
    )
    res = {
        "found": True,
        "hard_limit": 100000,
        "approval_policy": "MANDATORY_ALL_TRANSACTIONS",
        "risk_threshold": 50000,
        "summary": summary
    }
    state["query_result"] = res
    state["status"] = "QUERY_ANSWERED"
    state["route_taken"] = "risk_query"
    
    trace: AgentTrace = {
        "agent_name": "Risk Engine",
        "status": "QUERY_ANSWERED",
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {"policy_query": "governance_rules"},
        "decision": summary,
        "tools_used": ["risk_policy_engine"],
        "tool_data": res,
        "evidence": {"hard_cap": 100000, "mandatory_hitl": True},
        "output_data": res
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Risk Engine - Policy Overview]\n{summary}")
    return state

# ─── Routers ──────────────────────────────────────────────────────────────────

def route_from_manager(state: WorkflowState):
    status = state.get("status")
    intent = state.get("intent")
    
    if status == "FAILED" or status == "NEEDS_CLARIFICATION":
        return "audit"
        
    if intent == "inventory_query":
        return "inventory_direct"
    elif intent == "supplier_query":
        return "supplier_direct"
    elif intent == "budget_query":
        return "budget_direct"
    elif intent == "purchase_order_query":
        return "po_direct"
    elif intent in ["risk_query", "general_business_query"]:
        return "risk_direct"
    else:  # procurement_request
        return "inventory"

def should_route_from_risk(state: WorkflowState):
    if state.get("status") in ["BLOCKED", "FAILED"]:
        return "audit"
    risk_level = state.get("risk_result", {}).get("level")
    if risk_level == "BLOCKED":
        return "audit"
    # Mandatory Human-in-the-Loop approval for EVERY valid purchase
    return "human_approval"

def human_approval_node(state: WorkflowState) -> WorkflowState:
    raw_action = str(state.get("approval_status", "")).upper()
    is_approved = raw_action in ["APPROVE", "APPROVED"]
    normalized = "APPROVED" if is_approved else "REJECTED"
    state["approval_status"] = normalized

    if is_approved:
        procurement = state.get("procurement_result", {})
        # Capture approved transaction parameters for execution validation guard
        state["approved_transaction"] = {
            "supplier": procurement.get("supplier"),
            "product": state.get("product"),
            "quantity": procurement.get("quantity"),
            "total_cost": procurement.get("total_cost"),
        }
        decision_text = "Human Supervisor AUTHORIZED the transaction. Proceeding to purchase order execution."
        trace_status = "SUCCESS"
    else:
        state["status"] = "REJECTED"
        state["approved_transaction"] = None
        decision_text = "Human Supervisor REJECTED the transaction. Purchase order execution is aborted. No PO was created."
        trace_status = "REJECTED"

    trace: AgentTrace = {
        "agent_name": "Human Approval",
        "status": trace_status,
        "llm_mode": "DETERMINISTIC_FALLBACK",
        "input_data": {
            "order_cost": f"₹{state.get('procurement_result', {}).get('total_cost', 0):,}",
            "supplier": state.get("procurement_result", {}).get("supplier"),
            "risk_tier": state.get("risk_result", {}).get("level", "LOW")
        },
        "decision": decision_text,
        "tools_used": [],
        "tool_data": None,
        "evidence": {
            "action_submitted": raw_action,
            "normalized_status": normalized,
            "approved_transaction": state.get("approved_transaction")
        },
        "output_data": {"approval_status": normalized}
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Human Supervisor]\n{decision_text}")
    return state

def should_continue_after_approval(state: WorkflowState):
    raw_action = str(state.get("approval_status", "")).upper()
    if raw_action in ["APPROVE", "APPROVED"]:
        return "execution"
    return "audit"

def should_route_from_inventory(state: WorkflowState):
    qty = state.get("quantity_to_order", 0)
    # If no units need to be ordered, skip web research and proceed straight to procurement
    if qty <= 0:
        return "procurement"
    # If user explicitly requested internal suppliers only or disabled research
    if state.get("web_research_enabled") is False:
        return "procurement"
    # If product is unknown
    if not state.get("product"):
        return "procurement"
    return "web_research"

# ─── StateGraph Definition ───────────────────────────────────────────────────

builder = StateGraph(WorkflowState)

# Nodes
builder.add_node("manager", manager_node)
builder.add_node("inventory_direct", inventory_direct_node)
builder.add_node("supplier_direct", supplier_direct_node)
builder.add_node("budget_direct", budget_direct_node)
builder.add_node("po_direct", po_direct_node)
builder.add_node("risk_direct", risk_direct_node)
builder.add_node("inventory", inventory_node)
builder.add_node("web_research", web_research_node)
builder.add_node("procurement", procurement_node)
builder.add_node("finance", finance_node)
builder.add_node("risk", risk_node)
builder.add_node("human_approval", human_approval_node)
builder.add_node("execution", execution_node)
builder.add_node("audit", audit_node)

# Edges
builder.add_edge(START, "manager")

builder.add_conditional_edges(
    "manager",
    route_from_manager,
    {
        "inventory_direct": "inventory_direct",
        "supplier_direct": "supplier_direct",
        "budget_direct": "budget_direct",
        "po_direct": "po_direct",
        "risk_direct": "risk_direct",
        "inventory": "inventory",
        "audit": "audit"
    }
)

# Read-only routes lead directly to audit
builder.add_edge("inventory_direct", "audit")
builder.add_edge("supplier_direct", "audit")
builder.add_edge("budget_direct", "audit")
builder.add_edge("po_direct", "audit")
builder.add_edge("risk_direct", "audit")

# Procurement workflow pipeline with Web Research comparison
builder.add_conditional_edges(
    "inventory",
    should_route_from_inventory,
    {
        "web_research": "web_research",
        "procurement": "procurement"
    }
)
builder.add_edge("web_research", "procurement")
builder.add_edge("procurement", "finance")
builder.add_edge("finance", "risk")

builder.add_conditional_edges(
    "risk",
    should_route_from_risk,
    {
        "human_approval": "human_approval",
        "audit": "audit"
    }
)

builder.add_conditional_edges(
    "human_approval",
    should_continue_after_approval,
    {
        "execution": "execution",
        "audit": "audit"
    }
)

builder.add_edge("execution", "audit")
builder.add_edge("audit", END)

memory = MemorySaver()
app = builder.compile(checkpointer=memory, interrupt_before=["human_approval"])
