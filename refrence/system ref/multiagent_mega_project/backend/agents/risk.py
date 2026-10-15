from graph.state import WorkflowState, AgentTrace

def risk_node(state: WorkflowState) -> WorkflowState:
    if state.get("status") == "FAILED":
        return state
        
    amount = state.get("procurement_result", {}).get("total_cost", 0)
    finance_status = state.get("finance_result", {}).get("status", "APPROVED")
    
    # Deterministic Rule 1: Budget Constraint (exceeds ₹1,00,000)
    if finance_status == "REJECTED" or amount > 100000:
        risk_level = "BLOCKED"
        policy_outcome = "BLOCKED_BUDGET_EXCEEDED"
        state["status"] = "BLOCKED"
        state["error_message"] = f"Transaction amount ₹{amount:,} exceeds available corporate budget limit of ₹100,000."
        decision = (
            f"POLICY ENFORCEMENT - TRANSACTION BLOCKED: Order expenditure of ₹{amount:,} exceeds authorized "
            f"budget cap of ₹100,000. Autonomous execution is forbidden, and human override is disabled for fiscal compliance."
        )
        trace_status = "BLOCKED"
    # Deterministic Rule 2: High Financial Risk (>= ₹50,000 and <= ₹1,00,000)
    elif amount >= 50000:
        risk_level = "HIGH"
        policy_outcome = "PENDING_HUMAN_APPROVAL"
        state["status"] = "PAUSED_FOR_APPROVAL"
        decision = (
            f"HIGH RISK CLASSIFICATION: Order total of ₹{amount:,} meets or exceeds ₹50,000 governance tier. "
            f"Mandatory human approval required before purchase order execution."
        )
        trace_status = "PAUSED"
    # Deterministic Rule 3: Low Risk (< ₹50,000) - Mandatory HITL approval applies to all purchases
    else:
        risk_level = "LOW"
        policy_outcome = "PENDING_HUMAN_APPROVAL"
        state["status"] = "PAUSED_FOR_APPROVAL"
        decision = (
            f"LOW RISK CLASSIFICATION: Order total of ₹{amount:,} is below ₹50,000 governance tier. "
            f"Mandatory human approval policy enforced for all purchases before execution."
        )
        trace_status = "PAUSED"
        
    risk_data = {
        "level": risk_level,
        "policy_outcome": policy_outcome,
        "threshold": 50000,
        "budget_cap": 100000,
        "order_amount": amount,
        "mandatory_approval": True
    }
    state["risk_result"] = risk_data
    
    trace: AgentTrace = {
        "agent_name": "Risk Engine",
        "status": trace_status,
        "llm_mode": "DETERMINISTIC_FALLBACK",  # Risk policies are strictly deterministic Python rules
        "input_data": {
            "order_total": f"₹{amount:,}",
            "finance_approval": finance_status
        },
        "decision": decision,
        "tools_used": [],
        "tool_data": None,
        "evidence": {
            "rule_evaluated": "Corporate Spend & Risk Policy",
            "threshold_applied": "₹50,000 (Approval required), ₹100,000 (Hard Cap)",
            "risk_classification": risk_level,
            "policy_outcome": policy_outcome
        },
        "output_data": risk_data
    }
    state["agent_traces"].append(trace)
    
    log_text = (
        f"[Risk Engine] (DETERMINISTIC RULE)\n"
        f"Evaluation for ₹{amount:,}: Risk Level = {risk_level}.\n"
        f"Outcome: {policy_outcome}."
    )
    state["audit_log"].append(log_text)
    
    return state

