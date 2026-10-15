from typing import Optional
from graph.state import WorkflowState, AgentTrace
from tools.inventory_tool import check_inventory
from llm_utils import invoke_llm_structured
from pydantic import BaseModel, Field

class InventoryOutput(BaseModel):
    analysis: str = Field(description="Operational analysis distinguishing available stock, stated user demand, shortfall, and safety replenishment.")
    decision: str = Field(description="Replenishment recommendation clearly specifying units to order to fulfill demand.")

def inventory_node(state: WorkflowState) -> WorkflowState:
    if state.get("status") in ["FAILED", "NEEDS_CLARIFICATION"]:
        return state
        
    product = state.get("product")
    if not product:
        state["status"] = "FAILED"
        state["error_message"] = "No product identified for Inventory Agent."
        return state

    requested_qty = state.get("requested_quantity")
    qty_semantics = state.get("quantity_semantics", "UNSPECIFIED")
    additional_qty = state.get("additional_quantity")
    demand_qty = state.get("demand_quantity")
    target_stock = state.get("target_total_stock")
    
    # Execute database inventory tool
    tool_result = check_inventory(
        product,
        supplied_current=state.get("current_stock"),
        supplied_minimum=state.get("minimum_stock_level"),
        requested_quantity=requested_qty,
        quantity_semantics=qty_semantics,
        additional_quantity=additional_qty,
        demand_quantity=demand_qty,
        target_total_stock=target_stock
    )
    
    current_stock = tool_result["current_stock"]
    min_stock = tool_result["minimum_stock_level"]
    demand_shortfall = tool_result["demand_shortfall"]
    replenishment_qty = tool_result["replenishment_quantity"]
    
    # Build distinct selectable purchasing strategies
    if qty_semantics == "ADDITIONAL_QUANTITY" or additional_qty is not None:
        meet_demand_qty = additional_qty if additional_qty is not None else (requested_qty or 1)
        meet_desc = f"Order {meet_demand_qty} additional unit(s) as requested by the user."
        resulting_stock = current_stock + meet_demand_qty
        meet_conseq = f"Supplies {meet_demand_qty} more units. Warehouse inventory will increase from {current_stock} to {resulting_stock} units upon receipt."
    elif qty_semantics == "TOTAL_DEMAND" or demand_qty is not None:
        total_needed = demand_qty if demand_qty is not None else (requested_qty or 1)
        meet_demand_qty = max(0, total_needed - current_stock)
        meet_desc = f"Order {meet_demand_qty} unit(s) to fulfill the stated total requirement of {total_needed} units using {current_stock} usable units on hand."
        if meet_demand_qty > 0:
            meet_conseq = f"Satisfies total requirement of {total_needed} units. Existing warehouse stock of {current_stock} units will be fully dispatched."
        else:
            meet_conseq = f"Existing usable stock of {current_stock} units already covers the stated total requirement of {total_needed} units. 0 additional units needed."
    else:
        meet_demand_qty = demand_shortfall if demand_shortfall is not None else (requested_qty or 1)
        meet_desc = f"Order {meet_demand_qty} unit(s) to fulfill the stated operational demand of {requested_qty or meet_demand_qty} units using {current_stock} usable units on hand."
        meet_conseq = f"Satisfies stated demand with minimal upfront cost. Leaves usable warehouse stock at 0 units upon dispatch (below safety threshold of {min_stock})."

    safety_stock_qty = replenishment_qty
    custom_target_type = state.get("custom_target_type", "PURCHASE_QUANTITY")
    if custom_target_type == "TARGET_TOTAL_STOCK" and state.get("final_order_quantity") is not None:
        custom_qty = max(0, state["final_order_quantity"] - current_stock)
    else:
        custom_qty = state.get("final_order_quantity") or meet_demand_qty or safety_stock_qty or 1

    available_strategies = [
        {
            "strategy": "meet_demand",
            "strategy_id": "meet_demand",
            "name": "Meet Immediate Demand",
            "quantity": meet_demand_qty,
            "description": meet_desc,
            "consequences": meet_conseq,
            "recommended": True if (requested_qty is not None) else False
        },
        {
            "strategy": "restore_safety_stock",
            "strategy_id": "restore_safety_stock",
            "name": "Restore Safety Stock",
            "quantity": safety_stock_qty,
            "description": f"Order {safety_stock_qty} unit(s) to restore inventory back to the corporate safety threshold of {min_stock} units.",
            "consequences": f"Brings warehouse inventory up to {min_stock} units in full compliance with corporate safety stock policy.",
            "recommended": True if (requested_qty is None) else False
        },
        {
            "strategy": "custom",
            "strategy_id": "custom",
            "name": "Custom Target Quantity",
            "quantity": custom_qty,
            "description": "Specify a custom target procurement quantity or desired total stock level determined by the buyer.",
            "consequences": "Procures exact buyer-selected volume based on operational discretion.",
            "recommended": False
        }
    ]

    selected_strategy = state.get("selected_strategy")
    if not selected_strategy:
        selected_strategy = "meet_demand" if requested_qty is not None else "restore_safety_stock"

    if selected_strategy == "meet_demand":
        final_order_qty = meet_demand_qty
    elif selected_strategy == "restore_safety_stock":
        final_order_qty = safety_stock_qty
    elif selected_strategy == "custom":
        final_order_qty = state.get("final_order_quantity") or custom_qty
    else:
        final_order_qty = meet_demand_qty

    quantity_to_order = final_order_qty

    # Store clean, separated quantity metrics and strategies in state
    state["inventory_result"] = tool_result
    state["current_stock"] = current_stock
    state["minimum_stock_level"] = min_stock
    state["demand_shortfall"] = demand_shortfall
    state["replenishment_quantity"] = replenishment_qty
    state["available_strategies"] = available_strategies
    state["selected_strategy"] = selected_strategy
    state["final_order_quantity"] = final_order_qty
    state["quantity_to_order"] = final_order_qty

    system_prompt = (
        "You are an enterprise Inventory & Supply Chain Agent. Analyze warehouse stock levels. "
        "CRITICAL: Keep 'requested_quantity' (user demand), 'current_stock' (usable on hand), "
        "'demand_shortfall' (net units needed to satisfy demand), and 'replenishment_quantity' "
        "(units needed to restore safety stock) completely distinct. "
        "State the exact order quantity recommended to fulfill demand without inflating the order."
    )
    
    user_prompt = (
        f"Product: {tool_result['product']}. "
        f"Requested demand: {requested_qty if requested_qty is not None else 'Not explicitly stated'}. "
        f"Current available stock: {current_stock} units at {tool_result.get('location')}. "
        f"Demand shortfall: {demand_shortfall if demand_shortfall is not None else 'N/A'}. "
        f"Safety stock minimum: {min_stock} units. "
        f"Replenishment to restore safety minimum: {replenishment_qty} units. "
        f"Primary order quantity to satisfy operational demand: {quantity_to_order} units."
    )
    
    result, mode, err = invoke_llm_structured(system_prompt, user_prompt, InventoryOutput)
    
    if result is not None:
        llm_mode = "LIVE_LLM"
        decision_text = f"{result.analysis} Recommendation: {result.decision}"
    else:
        llm_mode = "DETERMINISTIC_FALLBACK"
        if requested_qty is not None and demand_shortfall is not None:
            decision_text = (
                f"STOCK ANALYSIS: Requested demand of {requested_qty} units with {current_stock} units on hand at {tool_result.get('location')} "
                f"creates an immediate demand shortfall of {demand_shortfall} units. "
                f"(Safety threshold of {min_stock} units would require {replenishment_qty} units for full buffer). "
                f"Proceeding with primary order quantity of {quantity_to_order} units to fulfill requested demand."
            )
        elif quantity_to_order > 0:
            decision_text = (
                f"LOW STOCK DETECTED at {tool_result.get('location')}: {current_stock} units on hand "
                f"falls below safety threshold of {min_stock}. Replenishment order of {quantity_to_order} units required."
            )
        else:
            decision_text = (
                f"SUFFICIENT STOCK at {tool_result.get('location')}: {current_stock} units on hand "
                f"meets or exceeds safety threshold of {min_stock}. No purchase needed."
            )
            
    trace: AgentTrace = {
        "agent_name": "Inventory Agent",
        "status": "SUCCESS",
        "llm_mode": llm_mode,
        "input_data": {
            "product": product,
            "requested_quantity": requested_qty,
            "current_stock_on_hand": current_stock,
            "minimum_stock_threshold": min_stock,
        },
        "decision": decision_text,
        "tools_used": ["database::inventory_items"],
        "tool_data": tool_result,
        "evidence": {
            "current_stock": current_stock,
            "requested_quantity": requested_qty,
            "demand_shortfall": demand_shortfall,
            "minimum_stock_level": min_stock,
            "replenishment_quantity": replenishment_qty,
            "quantity_to_order": quantity_to_order,
            "data_source": tool_result.get("data_source"),
        },
        "output_data": {
            "quantity_to_order": quantity_to_order,
            "status": tool_result["status"]
        }
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Inventory Agent]\n{decision_text}")
    return state
