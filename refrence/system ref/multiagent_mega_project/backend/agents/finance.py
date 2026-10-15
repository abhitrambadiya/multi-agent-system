from graph.state import WorkflowState, AgentTrace
from tools.finance_tool import check_budget
from llm_utils import invoke_llm_structured
from pydantic import BaseModel, Field

class FinanceOutput(BaseModel):
    budget_analysis: str = Field(description="Assessment of purchase amount against fiscal limits, available balance, and corporate caps")
    fiscal_recommendation: str = Field(description="Formal financial decision statement (Approved or Rejected) with specific figures")

def finance_node(state: WorkflowState) -> WorkflowState:
    if state.get("status") in ["FAILED", "NEEDS_CLARIFICATION"]:
        return state
        
    amount = state.get("procurement_result", {}).get("total_cost", 0)
    
    # Query real database finance budget
    tool_result = check_budget(amount)
    state["finance_result"] = tool_result
    
    available = tool_result["available_budget"]
    hard_limit = tool_result["hard_limit"]
    is_approved = tool_result["status"] == "APPROVED"
    
    system_prompt = (
        "You are an enterprise Finance Controller Agent. Evaluate whether the purchase amount is within "
        "authorized corporate budget limits (ceiling: ₹100,000). State your decision clearly with exact figures. "
        "CRITICAL: If the amount exceeds ₹100,000 or the available budget, you MUST reject the transaction."
    )
    user_prompt = (
        f"Purchase amount: ₹{amount:,}. "
        f"Available operational budget: ₹{available:,}. "
        f"Corporate hard spending limit: ₹{hard_limit:,}. "
        f"Budget check status: {tool_result['status']}."
    )
    
    result, mode, err = invoke_llm_structured(system_prompt, user_prompt, FinanceOutput)
    
    if result is not None:
        llm_mode = "LIVE_LLM"
        decision_text = f"{result.budget_analysis} {result.fiscal_recommendation}"
    else:
        llm_mode = "DETERMINISTIC_FALLBACK"
        if is_approved:
            decision_text = (
                f"BUDGET APPROVED: Purchase amount of ₹{amount:,} is within authorized budget of ₹{available:,} "
                f"(Hard limit: ₹{hard_limit:,}). Remaining fiscal budget: ₹{tool_result['remaining_budget']:,}."
            )
        else:
            decision_text = (
                f"BUDGET REJECTED: Purchase amount of ₹{amount:,} exceeds authorized fiscal limit of ₹{min(available, hard_limit):,}. "
                f"Over budget by ₹{tool_result['over_budget_by']:,}. Purchase order creation blocked."
            )
            
    trace: AgentTrace = {
        "agent_name": "Finance Agent",
        "status": "SUCCESS" if is_approved else "BLOCKED",
        "llm_mode": llm_mode,
        "input_data": {
            "purchase_amount": amount,
            "available_budget": available,
            "hard_limit": hard_limit,
        },
        "decision": decision_text,
        "tools_used": ["database::finance_budgets"],
        "tool_data": tool_result,
        "evidence": {
            "authorized": is_approved,
            "purchase_amount": amount,
            "available_budget": available,
            "remaining_budget": tool_result.get("remaining_budget"),
            "data_source": tool_result.get("data_source")
        },
        "output_data": tool_result
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Finance Agent]\n{decision_text}")
    return state
