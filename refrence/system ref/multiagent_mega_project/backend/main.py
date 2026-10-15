from typing import Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from graph.workflow import app as workflow_app
from agents.procurement import configure_procurement_decision
from llm_utils import is_live_llm_available, get_active_provider, get_active_model
from database.db import (
    init_db,
    list_all_inventory,
    list_all_suppliers,
    get_finance_budget_status,
    list_recent_purchase_orders,
)

# Initialize database schemas and seed data on engine load
init_db()

app = FastAPI(title="AI-EOS Multi-Agent Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunRequest(BaseModel):
    business_event: str

class ApproveRequest(BaseModel):
    thread_id: str
    action: str  # "APPROVE" or "REJECT"

class ConfigureWorkflowRequest(BaseModel):
    thread_id: str
    selected_strategy: Optional[str] = None
    final_order_quantity: Optional[int] = None
    selected_supplier_name: Optional[str] = None
    custom_target_type: Optional[str] = None

def _normalize_supplier_name(val: Any) -> str:
    if not val:
        return "—"
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("name") or val.get("supplier") or "—"
    return str(val)

def _extract_supplier_quote(val: Any, quotes: Optional[list] = None) -> Optional[dict]:
    if isinstance(val, dict):
        return val
    if isinstance(val, str) and quotes:
        for q in quotes:
            if isinstance(q, dict) and q.get("name", "").lower() == val.lower():
                return q
    return None


@app.get("/api/health")
async def health_check():
    live = is_live_llm_available()
    return {
        "status": "healthy",
        "live_llm_configured": live,
        "llm_provider": get_active_provider() if live else "none",
        "llm_model": get_active_model() if live else None,
    }

@app.post("/api/workflow/run")
async def run_workflow(request: RunRequest):
    if not request.business_event or not request.business_event.strip():
        raise HTTPException(status_code=422, detail="business_event must not be empty.")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "business_event": request.business_event.strip(),
        "thread_id": thread_id,
        "status": "RUNNING",
        "agent_traces": [],
        "audit_log": []
    }

    # Run the workflow until completion or interruption
    workflow_app.invoke(initial_state, config=config)

    snapshot = workflow_app.get_state(config)
    state_values = snapshot.values if snapshot else {}
    is_paused = bool(snapshot and snapshot.next and "human_approval" in snapshot.next)
    status = state_values.get("status", "COMPLETED")
    if is_paused:
        status = "PAUSED_FOR_APPROVAL"

    quotes = state_values.get("eligible_quotes") or state_values.get("procurement_result", {}).get("quotes_evaluated") or []
    raw_rec = state_values.get("recommended_supplier_name") or state_values.get("recommended_supplier") or state_values.get("procurement_result", {}).get("recommended_supplier")
    rec_name = _normalize_supplier_name(raw_rec)
    rec_quote = state_values.get("recommended_supplier_quote") or _extract_supplier_quote(raw_rec, quotes)
    sel_name = state_values.get("selected_supplier_name") or _normalize_supplier_name(state_values.get("selected_supplier") or state_values.get("procurement_result", {}).get("supplier"))

    web_offers = state_values.get("web_offers") or []

    return {
        "thread_id": thread_id,
        "status": status,
        "is_paused": is_paused,
        "intent": state_values.get("intent"),
        "route_taken": state_values.get("route_taken"),
        "query_result": state_values.get("query_result"),
        "needs_clarification": state_values.get("needs_clarification", False),
        "clarification_question": state_values.get("clarification_question"),
        "available_strategies": state_values.get("available_strategies"),
        "selected_strategy": state_values.get("selected_strategy"),
        "final_order_quantity": state_values.get("final_order_quantity"),
        "eligible_quotes": quotes,
        "web_offers": web_offers,
        "web_research_status": state_values.get("web_research_status"),
        "web_research_summary": state_values.get("web_research_summary"),
        "external_purchase_selected": state_values.get("external_purchase_selected", False),
        "selected_supplier": state_values.get("selected_supplier") or state_values.get("procurement_result", {}).get("supplier"),
        "selected_supplier_name": sel_name,
        "recommended_supplier": rec_name,
        "recommended_supplier_name": rec_name,
        "recommended_supplier_quote": rec_quote,
        "state": state_values
    }

@app.get("/api/workflow/status/{thread_id}")
async def get_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow_app.get_state(config)

    if not snapshot or not hasattr(snapshot, 'values') or not snapshot.values:
        raise HTTPException(status_code=404, detail="Thread session not found")

    is_paused = bool(snapshot.next and "human_approval" in snapshot.next)
    status = snapshot.values.get("status", "COMPLETED")
    if is_paused and status != "BLOCKED":
        status = "PAUSED_FOR_APPROVAL"

    quotes = snapshot.values.get("eligible_quotes") or snapshot.values.get("procurement_result", {}).get("quotes_evaluated") or []
    raw_rec = snapshot.values.get("recommended_supplier_name") or snapshot.values.get("recommended_supplier") or snapshot.values.get("procurement_result", {}).get("recommended_supplier")
    rec_name = _normalize_supplier_name(raw_rec)
    rec_quote = snapshot.values.get("recommended_supplier_quote") or _extract_supplier_quote(raw_rec, quotes)
    sel_name = snapshot.values.get("selected_supplier_name") or _normalize_supplier_name(snapshot.values.get("selected_supplier") or snapshot.values.get("procurement_result", {}).get("supplier"))

    web_offers = snapshot.values.get("web_offers") or []

    return {
        "thread_id": thread_id,
        "status": status,
        "is_paused": is_paused,
        "intent": snapshot.values.get("intent"),
        "route_taken": snapshot.values.get("route_taken"),
        "query_result": snapshot.values.get("query_result"),
        "needs_clarification": snapshot.values.get("needs_clarification", False),
        "clarification_question": snapshot.values.get("clarification_question"),
        "available_strategies": snapshot.values.get("available_strategies"),
        "selected_strategy": snapshot.values.get("selected_strategy"),
        "final_order_quantity": snapshot.values.get("final_order_quantity"),
        "eligible_quotes": quotes,
        "web_offers": web_offers,
        "web_research_status": snapshot.values.get("web_research_status"),
        "web_research_summary": snapshot.values.get("web_research_summary"),
        "external_purchase_selected": snapshot.values.get("external_purchase_selected", False),
        "selected_supplier": snapshot.values.get("selected_supplier") or snapshot.values.get("procurement_result", {}).get("supplier"),
        "selected_supplier_name": sel_name,
        "recommended_supplier": rec_name,
        "recommended_supplier_name": rec_name,
        "recommended_supplier_quote": rec_quote,
        "state": snapshot.values
    }

@app.post("/api/workflow/configure")
async def configure_workflow(request: ConfigureWorkflowRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    snapshot = workflow_app.get_state(config)
    if not snapshot or not hasattr(snapshot, 'values') or not snapshot.values:
        raise HTTPException(status_code=404, detail="Thread session not found")

    current_state = dict(snapshot.values)
    if current_state.get("execution_result") is not None:
        raise HTTPException(status_code=400, detail="Order has already been executed; configuration rejected.")

    updated_state = configure_procurement_decision(
        state=current_state,
        selected_strategy=request.selected_strategy,
        final_order_quantity=request.final_order_quantity,
        selected_supplier_name=request.selected_supplier_name,
        custom_target_type=request.custom_target_type
    )

    workflow_app.update_state(config, updated_state)

    updated_snapshot = workflow_app.get_state(config)
    final_values = updated_snapshot.values if updated_snapshot else updated_state
    is_paused = bool(updated_snapshot and updated_snapshot.next and "human_approval" in updated_snapshot.next)
    status = final_values.get("status", "PAUSED_FOR_APPROVAL")
    if is_paused and status != "BLOCKED":
        status = "PAUSED_FOR_APPROVAL"

    quotes = final_values.get("eligible_quotes") or final_values.get("procurement_result", {}).get("quotes_evaluated") or []
    raw_rec = final_values.get("recommended_supplier_name") or final_values.get("recommended_supplier") or final_values.get("procurement_result", {}).get("recommended_supplier")
    rec_name = _normalize_supplier_name(raw_rec)
    rec_quote = final_values.get("recommended_supplier_quote") or _extract_supplier_quote(raw_rec, quotes)
    sel_name = final_values.get("selected_supplier_name") or _normalize_supplier_name(final_values.get("selected_supplier") or final_values.get("procurement_result", {}).get("supplier"))
    web_offers = final_values.get("web_offers") or []

    return {
        "thread_id": request.thread_id,
        "status": status,
        "is_paused": is_paused,
        "intent": final_values.get("intent"),
        "route_taken": final_values.get("route_taken"),
        "available_strategies": final_values.get("available_strategies"),
        "selected_strategy": final_values.get("selected_strategy"),
        "final_order_quantity": final_values.get("final_order_quantity"),
        "eligible_quotes": quotes,
        "web_offers": web_offers,
        "web_research_status": final_values.get("web_research_status"),
        "web_research_summary": final_values.get("web_research_summary"),
        "external_purchase_selected": final_values.get("external_purchase_selected", False),
        "selected_supplier": final_values.get("selected_supplier") or final_values.get("procurement_result", {}).get("supplier"),
        "selected_supplier_name": sel_name,
        "recommended_supplier": rec_name,
        "recommended_supplier_name": rec_name,
        "recommended_supplier_quote": rec_quote,
        "state": final_values
    }

@app.post("/api/workflow/approve")
async def approve_workflow(request: ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    snapshot = workflow_app.get_state(config)
    if not snapshot or not snapshot.next or "human_approval" not in snapshot.next:
        raise HTTPException(status_code=400, detail="Workflow thread is not currently pending human approval.")

    current_values = snapshot.values
    if current_values.get("status") == "BLOCKED" or current_values.get("risk_result", {}).get("level") == "BLOCKED":
        raise HTTPException(status_code=400, detail="Cannot approve transaction: corporate budget limit exceeded.")

    if current_values.get("execution_result") is not None:
        raise HTTPException(status_code=400, detail="Order has already been executed; duplicate execution rejected.")

    raw_action = request.action.strip().upper()
    normalized = "APPROVED" if raw_action in ["APPROVE", "APPROVED"] else "REJECTED"

    # Pre-populate approved_transaction before resuming so execution guard passes
    update_payload = {"approval_status": normalized, "thread_id": request.thread_id}
    if normalized == "APPROVED":
        procurement = current_values.get("procurement_result", {})
        update_payload["approved_transaction"] = {
            "supplier": procurement.get("supplier"),
            "product": current_values.get("product"),
            "quantity": procurement.get("quantity"),
            "total_cost": procurement.get("total_cost"),
        }

    # Inject decision into state and resume
    workflow_app.update_state(config, update_payload)
    workflow_app.invoke(None, config=config)

    final_snapshot = workflow_app.get_state(config)
    final_values = final_snapshot.values if final_snapshot else {}
    current_status = final_values.get("status", "COMPLETED")

    return {
        "thread_id": request.thread_id,
        "status": current_status,
        "is_paused": False,
        "intent": final_values.get("intent"),
        "route_taken": final_values.get("route_taken"),
        "state": final_values
    }

# ─── Direct Domain Endpoints (Real Database Data) ─────────────────────────────

@app.get("/api/inventory")
async def get_inventory_items():
    """Returns real inventory records from the Inventory Agent's database."""
    return {"items": list_all_inventory()}

@app.get("/api/suppliers")
async def get_all_suppliers():
    """Returns approved supplier records from the Procurement Agent's database."""
    return {"suppliers": list_all_suppliers()}

@app.get("/api/budget")
async def get_budget_overview():
    """Returns fiscal budget and allocation from the Finance Agent's database."""
    return get_finance_budget_status()

@app.get("/api/purchase_orders")
async def get_all_orders():
    """Returns purchase orders recorded in the Execution Agent's database."""
    return {"purchase_orders": list_recent_purchase_orders(20)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
