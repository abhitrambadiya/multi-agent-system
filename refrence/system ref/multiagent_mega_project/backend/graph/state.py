from typing import TypedDict, List, Optional, Dict, Any

class AgentTrace(TypedDict):
    agent_name: str
    status: str  # "SUCCESS", "PAUSED", "REJECTED", "BLOCKED", "FAILED", "NEEDS_CLARIFICATION", "QUERY_ANSWERED"
    llm_mode: str  # "LIVE_LLM", "DETERMINISTIC_FALLBACK"
    input_data: Dict[str, Any]
    decision: str
    tools_used: List[str]
    tool_data: Optional[Dict[str, Any]]
    evidence: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]

class WorkflowState(TypedDict):
    business_event: str
    intent: Optional[str]  # "inventory_query", "supplier_query", "budget_query", "procurement_request", "risk_query", "purchase_order_query", "general_business_query", "clarification_required", "out_of_scope"
    intent_details: Optional[Dict[str, Any]]
    route_taken: Optional[str]  # "inventory_query", "supplier_query", "budget_query", "procurement_flow", "clarification", "out_of_scope", etc.
    status: str  # "RUNNING", "COMPLETED", "QUERY_ANSWERED", "PAUSED_FOR_APPROVAL", "REJECTED", "BLOCKED", "FAILED", "NEEDS_CLARIFICATION"
    error_message: Optional[str]
    llm_mode: Optional[str]  # Overall workflow LLM status

    # Extracted entity parameters
    product: Optional[str]
    deadline: Optional[str]
    department: Optional[str]
    quantity_semantics: Optional[str]    # "ADDITIONAL_QUANTITY" | "TOTAL_DEMAND" | "TARGET_STOCK" | "UNSPECIFIED"
    additional_quantity: Optional[int]   # Additional units explicitly requested (e.g. '8 more' -> 8)
    demand_quantity: Optional[int]       # Explicit total demand (e.g. 'needs 20 in total' -> 20)
    target_total_stock: Optional[int]    # Desired total inventory level after operation
    requested_quantity: Optional[int]    # Quantity explicitly requested by the user
    current_stock: Optional[int]         # Current inventory stock on hand
    demand_shortfall: Optional[int]      # Additional units needed to satisfy demand
    minimum_stock_level: Optional[int]   # Inventory safety threshold
    replenishment_quantity: Optional[int] # Units needed to restore safety stock: max(0, min_stock - current)
    quantity_to_order: Optional[int]     # Actual order quantity sent to procurement
    
    business_objective: Optional[str]
    needs_clarification: Optional[bool]
    clarification_question: Optional[str]

    # Query response for read-only intents
    query_result: Optional[Dict[str, Any]]

    # Strategy & Decision Control (Buyer-Controlled Decisions)
    inventory_sub_intent: Optional[str] # "current_count", "safety_threshold_replenishment", "demand_shortfall", "general_shortfall_analysis"
    available_strategies: Optional[List[Dict[str, Any]]] # [{strategy, strategy_id, name, quantity, description, consequences, recommended}]
    selected_strategy: Optional[str]    # "meet_demand" | "restore_safety_stock" | "custom"
    final_order_quantity: Optional[int] # The confirmed quantity to purchase
    custom_target_type: Optional[str]   # "PURCHASE_QUANTITY" | "TARGET_TOTAL_STOCK"
    eligible_quotes: Optional[List[Dict[str, Any]]]      # All eligible vendor quotes from PostgreSQL
    recommended_supplier: Optional[Any]                  # Normalized AI recommended supplier (string name or quote dict)
    recommended_supplier_name: Optional[str]             # Explicit string name of recommended supplier
    recommended_supplier_quote: Optional[Dict[str, Any]] # Full quote dictionary for recommended supplier
    selected_supplier: Optional[Dict[str, Any]]         # User/Buyer confirmed supplier
    selected_supplier_name: Optional[str]
    supplier_selection_mode: Optional[str]              # "RECOMMENDED" | "MANUAL"

    # Web Research Agent Outputs (Live Online Price Comparison)
    web_research_enabled: Optional[bool]                # Set to False if user requests internal suppliers only
    web_research_status: Optional[str]                 # "COMPLETED", "SKIPPED", "NO_OFFERS_FOUND", "FAILED"
    web_research_summary: Optional[str]
    web_offers: Optional[List[Dict[str, Any]]]         # Normalized online marketplace listings
    external_purchase_selected: Optional[bool]         # True if buyer selects an external web offer

    # Multi-agent transaction outputs
    inventory_result: Optional[Dict[str, Any]]
    procurement_result: Optional[Dict[str, Any]]
    finance_result: Optional[Dict[str, Any]]
    risk_result: Optional[Dict[str, Any]]
    approval_status: Optional[str]
    approved_transaction: Optional[Dict[str, Any]]
    execution_result: Optional[Dict[str, Any]]

    agent_traces: List[AgentTrace]
    audit_log: List[str]
