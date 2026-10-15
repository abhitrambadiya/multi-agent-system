import re
from typing import Optional, Dict, Any, List
from graph.state import WorkflowState, AgentTrace
from llm_utils import invoke_llm_structured
from pydantic import BaseModel, Field

VALID_INTENTS = [
    "inventory_query",
    "supplier_query",
    "budget_query",
    "procurement_request",
    "risk_query",
    "purchase_order_query",
    "general_business_query",
    "clarification_required",
    "out_of_scope",
]

class IntentOutput(BaseModel):
    intent: str = Field(
        description=(
            "Exact classification. Choose one of: "
            "'inventory_query' (asking a read-only question about stock counts, inventory levels, or storage location, e.g. 'How many laptops are in inventory?'), "
            "'supplier_query' (asking about approved suppliers, vendor prices, lead times, ratings), "
            "'budget_query' (asking about corporate budget, spending limits, remaining funds), "
            "'procurement_request' (explicit request to order/buy/replenish, OR a stock alert where inventory dropped below safety threshold that triggers restocking), "
            "'risk_query' (asking about risk policies, approval rules, thresholds, compliance), "
            "'purchase_order_query' (asking about existing purchase orders, PO status, PO history), "
            "'general_business_query' (general queries about AI-EOS capabilities or procurement workflows), "
            "'clarification_required' (ambiguous or missing critical details like product name or intent), "
            "'out_of_scope' (unrelated tasks like meetings, flights, personal requests, HR)."
        )
    )
    inventory_sub_intent: Optional[str] = Field(
        default=None,
        description=(
            "For inventory queries, classify exact sub-intent: "
            "'current_count' (asking how many units currently in stock, e.g. 'How many laptops are in inventory?'), "
            "'safety_threshold_replenishment' (asking how many units needed to reach safety/minimum threshold, e.g. 'How many laptops will we need to reach the safety threshold?'), "
            "'demand_shortfall' (asking how many units needed to meet department demand, e.g. 'How many laptops needed to meet IT demand?'), "
            "'general_shortfall_analysis' (stock deficiency / health check). None if not an inventory query."
        )
    )
    confidence: float = Field(default=0.95, description="Confidence score between 0.0 and 1.0")
    product: Optional[str] = Field(default=None, description="The specific product/item name, or None.")
    quantity_semantics: str = Field(
        default="UNSPECIFIED",
        description=(
            "Exact semantic meaning of the requested quantity: "
            "'ADDITIONAL_QUANTITY' (when the user explicitly asks for additional or extra units, e.g. '8 more laptops', 'need an additional 5', 'buy 10 more'), "
            "'TOTAL_DEMAND' (when the user specifies an explicit total requirement to satisfy, e.g. 'need 8 laptops in total', 'department requires 20 laptops altogether', 'needs 12 by next week'), "
            "'TARGET_STOCK' (when the user specifies a target inventory level to reach, e.g. 'bring total stock to 20', 'reach a total of 30'), "
            "'UNSPECIFIED' (when no quantity modifier is present or for stock-drop alerts)."
        )
    )
    additional_quantity: Optional[int] = Field(
        default=None,
        description="The number of additional/more units explicitly requested (e.g. '8 more laptops' -> 8). None if not additional demand."
    )
    demand_quantity: Optional[int] = Field(
        default=None,
        description="The total demand requirement specified by the user or department (e.g. 'needs 20 in total' -> 20)."
    )
    target_total_stock: Optional[int] = Field(
        default=None,
        description="Desired target total inventory stock level to reach after operation, if specified (e.g. 'reach total of 30' -> 30)."
    )
    requested_quantity: Optional[int] = Field(
        default=None,
        description=(
            "Explicit quantity the user or department asked for to consume or receive (e.g. 'needs 12 laptops' -> 12, '8 more laptops' -> 8). "
            "CRITICAL: If the prompt is a stock drop or replenishment alert ('dropped to 12. Minimum required is 50'), "
            "do NOT set requested_quantity (leave it None). The deficit is safety replenishment, NOT an explicit user demand."
        )
    )
    current_stock_stated: Optional[int] = Field(default=None, description="Stock on hand explicitly stated in prompt, or None.")
    minimum_stock_stated: Optional[int] = Field(default=None, description="Minimum stock threshold explicitly stated in prompt, or None.")
    deadline: Optional[str] = Field(default=None, description="Explicit timeframe or deadline (e.g. 'next week', 'ASAP', 'Friday'), or None.")
    department: Optional[str] = Field(default=None, description="Requesting department (e.g. 'IT', 'Software Engineering'), or None.")
    clarification_question: Optional[str] = Field(
        default=None,
        description="A single clear clarifying question if intent is clarification_required, else None."
    )
    business_objective: str = Field(description="One concise sentence stating the user's operational objective.")
    reasoning: str = Field(description="Clear explanation of why this intent was selected and how entities were extracted.")
    decision: str = Field(description="Manager's action statement.")

def manager_node(state: WorkflowState) -> WorkflowState:
    event_text = state.get("business_event", "").strip()

    if not event_text:
        state["status"] = "FAILED"
        state["intent"] = "out_of_scope"
        state["error_message"] = "Empty business event received."
        trace: AgentTrace = {
            "agent_name": "Manager Agent",
            "status": "FAILED",
            "llm_mode": "DETERMINISTIC_FALLBACK",
            "input_data": {"business_event": event_text},
            "decision": "Empty input received. Cannot process workflow.",
            "tools_used": [],
            "tool_data": None,
            "evidence": {"validation_error": "Empty input"},
            "output_data": {"intent": "out_of_scope"}
        }
        state["agent_traces"].append(trace)
        return state

    system_prompt = (
        "You are the Intent Router and Chief Operations Manager for AI-EOS (Enterprise Operating System). "
        "Analyze the user's business event and classify it into exactly one of the 9 supported intents:\n\n"
        "1. inventory_query: The user is asking a read-only question about stock counts, safety threshold calculations, or shortfall analysis.\n"
        "   CRITICAL SUB-INTENTS for inventory_query:\n"
        "   - 'current_count': Asking about current on-hand stock (e.g. 'How many laptops are in inventory?').\n"
        "   - 'safety_threshold_replenishment': Asking how many units are needed to reach the safety threshold or minimum stock level (e.g. 'How many laptops will we need to reach the safety threshold?').\n"
        "   - 'demand_shortfall': Asking how many units are needed to meet a stated department demand.\n"
        "   - 'general_shortfall_analysis': Inquiring about stock deficits or inventory health.\n"
        "   CRITICAL: Do NOT classify valid read-only inventory questions as procurement or clarification_required!\n"
        "2. supplier_query: The user is asking a read-only question about vendors, quotes, pricing, ratings "
        "   (e.g. 'Who are the suppliers for Laptop Stand?', 'List approved vendors for Server Rack').\n"
        "3. budget_query: The user is asking a read-only question about budget balance, available funds, fiscal limits "
        "   (e.g. 'How much budget is left?', 'What is our available budget?').\n"
        "4. purchase_order_query: Inquiring about existing purchase orders or status of a PO.\n"
        "5. risk_query: Inquiring about risk tiers, approval policies, or compliance caps.\n"
        "6. general_business_query: General operational questions about corporate procurement rules.\n"
        "7. clarification_required: The user expresses procurement intent but is too vague (e.g. 'We need some stuff ordered', 'order 10 items' without saying what).\n"
        "8. out_of_scope: Requests completely outside enterprise procurement and inventory (e.g. 'Schedule a team meeting', 'Book flight tickets', 'What is the weather?').\n"
        "9. procurement_request: Any action-oriented request to order, purchase, replenish, or buy items, "
        "   OR a warehouse stock shortfall event reporting that stock has dropped below minimum threshold (e.g. 'Inventory has dropped to 12. Minimum required is 50.', 'We have only 2 laptops left, but IT needs 12 by next week.', 'Server Rack stock has fallen to 2 units. Minimum required is 15.'). "
        "   Extract: product, requested_quantity, quantity_semantics, additional_quantity, demand_quantity, target_total_stock, current_stock_stated, minimum_stock_stated, and deadline.\n"
        "   CRITICAL QUANTITY SEMANTICS:\n"
        "   - 'ADDITIONAL_QUANTITY': User requests additional/more units (e.g. 'we have 12 laptops and need 8 more' -> additional_quantity=8, requested_quantity=8).\n"
        "   - 'TOTAL_DEMAND': User specifies a total requirement (e.g. 'we have 12 laptops and need 8 in total' -> demand_quantity=8; 'department requires 20 laptops' -> demand_quantity=20).\n"
        "   - 'TARGET_STOCK': User specifies a desired total inventory level to reach (e.g. 'reach total of 30' -> target_total_stock=30).\n"
        "   - 'UNSPECIFIED': Stock replenishment alert without explicit consumption demand."
    )

    result, mode, err = invoke_llm_structured(system_prompt, event_text, IntentOutput)

    # Validate model output and sanitize
    if result is not None and result.intent in VALID_INTENTS:
        parsed = result
        llm_mode = "LIVE_LLM"
    else:
        # Fall back gracefully to deterministic rule-based classifier
        parsed = _deterministic_intent_classifier(event_text, err)
        llm_mode = "DETERMINISTIC_FALLBACK"

    # Guard: If user prompt is a warehouse stock alert without explicit consumption/department demand,
    # ensure requested_quantity is None so safety replenishment is calculated cleanly without subtracting current stock twice.
    if parsed.requested_quantity is not None:
        has_explicit_demand_phrase = bool(re.search(r"\b(needs?|require|need|demands?|order|procure|buy|for the team|for the department)\s+\d+", event_text, re.IGNORECASE))
        if not has_explicit_demand_phrase and re.search(r"\b(dropped to|fallen to|minimum required|safety threshold)\b", event_text, re.IGNORECASE):
            parsed.requested_quantity = None
            parsed.quantity_semantics = "UNSPECIFIED"
    elif parsed.intent == "procurement_request":
        m_explicit = re.search(r"\b(?:needs?|require|need|demands?|order|procure|buy)\s+(\d+)", event_text, re.IGNORECASE)
        if m_explicit:
            parsed.requested_quantity = int(m_explicit.group(1))
            parsed.quantity_semantics = "UNSPECIFIED"

    # Populate state with extracted intent and entities
    state["intent"] = parsed.intent
    state["inventory_sub_intent"] = parsed.inventory_sub_intent or "current_count"
    state["llm_mode"] = llm_mode
    state["product"] = parsed.product
    state["requested_quantity"] = parsed.requested_quantity
    state["quantity_semantics"] = parsed.quantity_semantics or "UNSPECIFIED"
    state["additional_quantity"] = parsed.additional_quantity
    state["demand_quantity"] = parsed.demand_quantity
    state["target_total_stock"] = parsed.target_total_stock
    state["deadline"] = parsed.deadline
    state["department"] = parsed.department
    state["business_objective"] = parsed.business_objective

    # Check if user explicitly requested internal suppliers only or disabled online search
    internal_only_keywords = [
        "internal supplier", "internal vendor", "approved supplier", "approved vendor",
        "registered vendor", "registered supplier", "catalog only", "from database only",
        "skip online", "skip web", "no web search", "internal only"
    ]
    is_internal_only = any(kw in event_text.lower() for kw in internal_only_keywords)
    state["web_research_enabled"] = not is_internal_only

    if parsed.current_stock_stated is not None:
        state["current_stock"] = parsed.current_stock_stated
    if parsed.minimum_stock_stated is not None:
        state["minimum_stock_level"] = parsed.minimum_stock_stated

    intent_details = {
        "intent": parsed.intent,
        "inventory_sub_intent": parsed.inventory_sub_intent or "current_count",
        "confidence": parsed.confidence,
        "reasoning": parsed.reasoning,
        "product": parsed.product,
        "requested_quantity": parsed.requested_quantity,
        "quantity_semantics": parsed.quantity_semantics or "UNSPECIFIED",
        "additional_quantity": parsed.additional_quantity,
        "demand_quantity": parsed.demand_quantity,
        "target_total_stock": parsed.target_total_stock,
        "current_stock_stated": parsed.current_stock_stated,
        "minimum_stock_stated": parsed.minimum_stock_stated,
        "deadline": parsed.deadline,
        "department": parsed.department,
        "llm_mode": llm_mode,
    }
    state["intent_details"] = intent_details

    # Route-specific state configuration
    if parsed.intent == "clarification_required":
        state["status"] = "NEEDS_CLARIFICATION"
        state["needs_clarification"] = True
        state["clarification_question"] = parsed.clarification_question or "Could you please specify which product and what quantity you need to procure?"
        state["route_taken"] = "clarification"
        decision_text = f"CLARIFICATION NEEDED: {state['clarification_question']}"
        trace_status = "NEEDS_CLARIFICATION"

    elif parsed.intent == "out_of_scope":
        state["status"] = "FAILED"
        state["needs_clarification"] = False
        state["route_taken"] = "out_of_scope"
        state["error_message"] = f"Request classified as OUT OF SCOPE: {parsed.reasoning}"
        decision_text = f"REJECTED (Out of Scope): {parsed.reasoning}"
        trace_status = "FAILED"

    elif parsed.intent in ["inventory_query", "supplier_query", "budget_query", "purchase_order_query", "risk_query", "general_business_query"]:
        state["status"] = "RUNNING"
        state["needs_clarification"] = False
        state["route_taken"] = parsed.intent
        decision_text = f"READ-ONLY INTENT ROUTED: Classified as '{parsed.intent}'. Routing directly to {parsed.intent.split('_')[0].title()} domain tool without triggering procurement or PO creation."
        trace_status = "SUCCESS"

    else:  # procurement_request
        state["status"] = "RUNNING"
        state["needs_clarification"] = False
        state["route_taken"] = "procurement_flow"
        deadline_str = f" (Deadline: {parsed.deadline})" if parsed.deadline else ""
        qty_str = f" (Requested: {parsed.requested_quantity} units)" if parsed.requested_quantity else ""
        decision_text = f"PROCUREMENT INTENT CONFIRMED: Proceeding with sourcing analysis for '{parsed.product}'{qty_str}{deadline_str}. Initiating inventory stock verification."
        trace_status = "SUCCESS"

    trace: AgentTrace = {
        "agent_name": "Manager Agent",
        "status": trace_status,
        "llm_mode": llm_mode,
        "input_data": {"business_event": event_text},
        "decision": decision_text,
        "tools_used": ["intent_router"],
        "tool_data": {
            "intent": parsed.intent,
            "confidence": parsed.confidence,
            "product": parsed.product,
            "requested_quantity": parsed.requested_quantity,
            "deadline": parsed.deadline,
        },
        "evidence": {
            "intent": parsed.intent,
            "reasoning": parsed.reasoning,
            "entities": {
                "product": parsed.product,
                "requested_quantity": parsed.requested_quantity,
                "current_stock": parsed.current_stock_stated,
                "minimum_stock": parsed.minimum_stock_stated,
                "deadline": parsed.deadline,
                "department": parsed.department,
            }
        },
        "output_data": {
            "intent": parsed.intent,
            "route_taken": state.get("route_taken"),
            "status": state["status"]
        }
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Manager Agent - Intent Router]\nIntent: {parsed.intent.upper()}\nDecision: {decision_text}")
    return state

def _deterministic_intent_classifier(text: str, err: Optional[str] = None) -> IntentOutput:
    """Safe, honest deterministic rule-based intent classifier fallback."""
    t = text.lower().strip()

    # 1. Out of scope detection
    out_of_scope_keywords = [
        "meeting", "schedule", "calendar", "interview", "flight", "hotel",
        "weather", "birthday", "party", "coffee", "lunch", "dinner", "vacation",
        "hr review", "performance review", "1-on-1", "all-hands", "town hall",
        "townhall", "attend", "conference", "webinar", "seminar", "workshop"
    ]
    if any(k in t for k in out_of_scope_keywords) and not any(p in t for p in ["laptop", "server", "mouse", "stock", "procure", "order", "buy"]):
        return IntentOutput(
            intent="out_of_scope",
            confidence=0.95,
            business_objective="Non-procurement corporate or personal request.",
            reasoning="Request contains out-of-scope tasks unrelated to procurement or inventory.",
            decision="Out of scope request detected. Workflow halted."
        )

    has_procurement_clue = any(k in t for k in [
        "laptop", "server", "mouse", "stock", "procure", "order", "buy", "purchase",
        "inventory", "supplier", "vendor", "budget", "quote", "rivet", "stand",
        "monitor", "keyboard", "units", "quantity", "replenish", "shortfall", "po-",
        "threshold", "warehouse", "cost", "price", "approval", "policy"
    ])
    if not has_procurement_clue:
        return IntentOutput(
            intent="out_of_scope",
            confidence=0.90,
            business_objective="Non-procurement corporate or personal request.",
            reasoning="Request does not contain any procurement, inventory, supplier, or product entities.",
            decision="Out of scope request detected. Workflow halted."
        )

    # 2. Inventory Query (read-only questions)
    if re.search(r"\b(how many|check inventory|in stock|stock level|units in stock|inventory count|where is|what is the stock|stock of)\b", t) and not re.search(r"\b(dropped to|fallen to|minimum required is|order\b|buy\b|procure\b|purchase\b|needs? \d+)\b", t):
        product = _extract_product(text)
        if re.search(r"\b(safety threshold|reach the safety|reach safety|reach minimum|reach the minimum|to reach safety|safety stock)\b", t, re.IGNORECASE):
            sub_intent = "safety_threshold_replenishment"
            obj = f"Calculate units of {product or 'items'} needed to reach the safety threshold."
            reason = "User is querying additional units needed to reach the minimum safety stock threshold."
        elif re.search(r"\b(meet.*demand|satisfy.*demand|to meet IT|to satisfy)\b", t, re.IGNORECASE):
            sub_intent = "demand_shortfall"
            obj = f"Calculate units of {product or 'items'} needed to satisfy stated departmental demand."
            reason = "User is querying additional units needed to meet operational demand."
        elif re.search(r"\b(shortfall analysis|stock shortfall|deficit analysis)\b", t, re.IGNORECASE):
            sub_intent = "general_shortfall_analysis"
            obj = f"Analyze stock shortfall for {product or 'items'}."
            reason = "User is requesting general stock shortfall analysis."
        else:
            sub_intent = "current_count"
            obj = f"Query inventory stock count for {product or 'catalog items'}."
            reason = "User is querying current on-hand inventory stock level without requesting a purchase."

        return IntentOutput(
            intent="inventory_query",
            inventory_sub_intent=sub_intent,
            confidence=0.95,
            product=product,
            business_objective=obj,
            reasoning=reason,
            decision=f"Route directly to Inventory Tool for stock inspection ({sub_intent})."
        )

    # 3. Supplier Query (read-only)
    if re.search(r"\b(who are the suppliers|supplier|suppliers|vendor|vendors|quotes|quote|pricing from|lead time)\b", t) and not re.search(r"\b(order|buy|procure|purchase)\b", t):
        product = _extract_product(text)
        return IntentOutput(
            intent="supplier_query",
            confidence=0.95,
            product=product,
            business_objective=f"Retrieve approved suppliers and quotes for {product or 'procurement items'}.",
            reasoning="User is querying vendor profiles and price quotes without issuing a purchase request.",
            decision="Route directly to Supplier Tool for quote retrieval."
        )

    # 4. Budget Query (read-only)
    if re.search(r"\b(how much budget|available budget|remaining budget|fiscal budget|budget limit|funds left|budget status)\b", t) and not re.search(r"\b(order|buy|procure|purchase)\b", t):
        return IntentOutput(
            intent="budget_query",
            confidence=0.98,
            business_objective="Inspect fiscal operational budget and remaining balance.",
            reasoning="User is asking about budgetary balances and spending caps.",
            decision="Route directly to Finance Tool for budget retrieval."
        )

    # 5. Purchase Order Query (read-only)
    if re.search(r"\b(purchase order|purchase orders|po status|recent pos|order status|status of po)\b", t) and not re.search(r"\b(create po|issue po|new order)\b", t):
        po_match = re.search(r"(PO-[\w-]+)", text, re.IGNORECASE)
        po_id = po_match.group(1) if po_match else None
        return IntentOutput(
            intent="purchase_order_query",
            confidence=0.95,
            business_objective="Retrieve purchase order status and history.",
            reasoning=f"User is inquiring about existing purchase orders (PO: {po_id or 'all'}).",
            decision="Route directly to Procurement Database for PO status lookup."
        )

    # 6. Risk Query (read-only)
    if re.search(r"\b(risk policy|approval rules|compliance policy|approval limit|mandatory approval)\b", t):
        return IntentOutput(
            intent="risk_query",
            confidence=0.92,
            business_objective="Inquire about enterprise compliance and human approval thresholds.",
            reasoning="User is inquiring about corporate risk governance.",
            decision="Route to Risk Engine policy explanation."
        )

    # 7. Ambiguous / Missing information (Clarification Required)
    vague_phrases = ["stuff", "supplies", "items", "things", "equipment", "hardware", "office stuff"]
    product = _extract_product(text)
    if any(v in t for v in vague_phrases) and not product and not re.search(r"\b(dropped to|fallen to|minimum required)\b", t):
        return IntentOutput(
            intent="clarification_required",
            confidence=0.90,
            clarification_question="Which specific product and quantity does your department require?",
            business_objective="Procurement intent detected but missing specific product catalog details.",
            reasoning="User stated intent to procure items but did not name the specific product or quantity.",
            decision="Request clarification for product name and volume."
        )

    # 8. Procurement Request (Default for action-oriented requests and stock alerts)
    qty_semantics = "UNSPECIFIED"
    add_qty = None
    dem_qty = None
    tgt_stock = None
    req_qty = None

    # Check for additional quantity ("more", "additional", "extra")
    m_more = re.search(r"(\d+)\s+more\b", text, re.IGNORECASE)
    if not m_more:
        m_more = re.search(r"\b(?:need|needs|require|buy|order|procure)\s+(\d+)\s+more\b", text, re.IGNORECASE)
    if not m_more:
        m_more = re.search(r"\b(?:additional|extra)\s+(\d+)\b", text, re.IGNORECASE)
    if not m_more:
        m_more = re.search(r"(\d+)\s+(?:additional|extra)\b", text, re.IGNORECASE)

    if m_more:
        qty_semantics = "ADDITIONAL_QUANTITY"
        add_qty = int(m_more.group(1))
        req_qty = add_qty
    else:
        # Check for target stock ("reach a total of", "bring total stock to", "reach 30", "reach a safety threshold of 30")
        m_tgt = re.search(r"\b(?:reach|bring|reach a|reach the)\s+(?:safety threshold of|safety threshold to|threshold of|total of|target of|total stock of)\s+(\d+)\b", text, re.IGNORECASE)
        if not m_tgt:
            m_tgt = re.search(r"\b(?:reach a total of|bring total stock to|reach target of|reach total stock of)\s+(\d+)\b", text, re.IGNORECASE)
        if m_tgt:
            qty_semantics = "TARGET_STOCK"
            tgt_stock = int(m_tgt.group(1))
            req_qty = tgt_stock
        else:
            # Check for total demand ("8 laptops in total", "in total", "total", "department requires X")
            m_tot = re.search(r"(\d+)\s+(?:[\w-]+\s+)?(?:in total|total|altogether)\b", text, re.IGNORECASE)
            if not m_tot:
                m_tot = re.search(r"\b(?:total of|in total)\s+(\d+)\b", text, re.IGNORECASE)
            if not m_tot:
                m_tot = re.search(r"\b(?:department requires|department needs|requires|demands)\s+(\d+)", text, re.IGNORECASE)
            if m_tot:
                qty_semantics = "TOTAL_DEMAND"
                dem_qty = int(m_tot.group(1))
                req_qty = dem_qty
            else:
                req_qty = _extract_quantity(text)
                if req_qty is not None:
                    if re.search(r"\b(?:department needs|requires|demands|needs? \d+ by)\b", text, re.IGNORECASE):
                        qty_semantics = "TOTAL_DEMAND"
                        dem_qty = req_qty

    curr_stock = _extract_current_stock(text)
    min_stock = _extract_minimum_stock(text)
    deadline = _extract_deadline(text)
    dept = _extract_department(text)

    return IntentOutput(
        intent="procurement_request",
        confidence=0.92,
        product=product or "General Equipment",
        quantity_semantics=qty_semantics,
        additional_quantity=add_qty,
        demand_quantity=dem_qty,
        target_total_stock=tgt_stock,
        requested_quantity=req_qty,
        current_stock_stated=curr_stock,
        minimum_stock_stated=min_stock,
        deadline=deadline,
        department=dept,
        business_objective=f"Procure required items for {product or 'inventory'}.",
        reasoning=f"Valid procurement intent ({qty_semantics}) identified for '{product or 'items'}'.",
        decision=f"Initiate multi-agent procurement workflow with quantity preservation."
    )

def _extract_product(text: str) -> Optional[str]:
    known_products = [
        "Industrial Server Rack",
        "Server Rack",
        "Laptop Stand",
        "Wireless Mouse",
        "Industrial Rivets",
        "Laptops",
        "Laptop",
    ]
    for p in known_products:
        if re.search(r"\b" + re.escape(p) + r"\b", text, re.IGNORECASE):
            return p
    # Generic product extraction pattern
    m = re.search(r"(?:for|of|on|order|procure|buy)\s+([A-Za-z0-9\s\-]+?)(?:\s+(?:left|stock|inventory|units|needed|for|by|urgently|\.|\,|$))", text, re.IGNORECASE)
    if m:
        cand = m.group(1).strip()
        if len(cand) > 2 and cand.lower() not in ["the", "some", "our", "all", "more"]:
            return cand.title()
    return None

def _extract_quantity(text: str) -> Optional[int]:
    has_demand = bool(re.search(r"\b(needs?|require|need|demands?|order|procure|buy|purchase)\b", text, re.IGNORECASE))
    if not has_demand and re.search(r"\b(dropped to|fallen to|minimum required)\b", text, re.IGNORECASE):
        return None
    patterns = [
        r"(?:purchase:?|order:?|procure:?)\s*(\d+)",
        r"(?:needs?|require|need|demands?)\s+(\d+)",
        r"(?:order|procure|buy)\s+(\d+)",
        r"(\d+)\s+(?:enterprise\s+)?(?:units|items|pieces|laptops|racks|stands|mice|rivets)",
        r"(\d+)\s+(?:units|items|pieces|laptops|racks|stands|mice)?\s*(?:by|next week|needed|required|immediately)",
        r"(?:quantity of|volume of)\s+(\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None

def _extract_current_stock(text: str) -> Optional[int]:
    patterns = [
        r"(?:only|have|current stock is|stock is|stock has fallen to|inventory has dropped to)\s+(\d+)",
        r"(\d+)\s+(?:units|items|laptops)?\s*(?:left|remain|on hand|in stock)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None

def _extract_minimum_stock(text: str) -> Optional[int]:
    patterns = [
        r"(?:minimum required is|minimum required stock is|safety minimum is|threshold is)\s+(\d+)",
        r"(?:minimum|safety stock of)\s+(\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None

def _extract_deadline(text: str) -> Optional[str]:
    patterns = [
        r"\b(by next week|next week|tomorrow|by tomorrow|asap|urgently|immediately|by friday|by monday|by end of week)\b",
        r"\b(within \d+ days?)\b"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

def _extract_department(text: str) -> Optional[str]:
    m = re.search(r"\b(it department|it|software engineering|marketing|finance|operations|engineering)\b", text, re.IGNORECASE)
    if m:
        return m.group(1).title()
    return None
