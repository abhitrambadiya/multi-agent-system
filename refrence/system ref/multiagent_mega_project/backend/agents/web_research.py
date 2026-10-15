"""
AI-EOS Web Research Agent
Discovers public online product offers for price comparison against PostgreSQL supplier quotes.
Adheres to enterprise procurement rules and web crawling safety policies.
"""
from typing import Dict, Any, List, Optional
from graph.state import WorkflowState, AgentTrace
from tools.web_research_tool import discover_online_offers
from llm_utils import invoke_llm_structured
from pydantic import BaseModel, Field

class WebResearchOutput(BaseModel):
    findings_summary: str = Field(description="Summary of online listings found, price spread, and delivery feasibility")
    marketplace_insight: str = Field(description="Actionable comparison insight between public online market and internal catalog")

def web_research_node(state: WorkflowState) -> WorkflowState:
    # Skip if previous nodes failed or need clarification
    if state.get("status") in ["FAILED", "NEEDS_CLARIFICATION"]:
        return state

    # Conditional skip check: User requested internal suppliers only or research disabled
    if state.get("web_research_enabled") is False:
        decision_text = "WEB RESEARCH SKIPPED: Internal suppliers requested or web research disabled for this query."
        state["web_research_status"] = "SKIPPED"
        state["web_research_summary"] = decision_text
        state["web_offers"] = []
        trace: AgentTrace = {
            "agent_name": "Web Research Agent",
            "status": "SUCCESS",
            "llm_mode": "DETERMINISTIC_FALLBACK",
            "input_data": {"reason": "User restricted search to internal suppliers only"},
            "decision": decision_text,
            "tools_used": [],
            "tool_data": None,
            "evidence": {"web_research_enabled": False},
            "output_data": {"status": "SKIPPED", "offers_found": 0}
        }
        state["agent_traces"].append(trace)
        state["audit_log"].append(f"[Web Research Agent]\n{decision_text}")
        return state

    product = state.get("product")
    if not product or product.lower() in ["unknown", "none", "items"]:
        decision_text = "WEB RESEARCH SKIPPED: Product specifications too ambiguous to execute targeted web price comparison."
        state["web_research_status"] = "SKIPPED"
        state["web_research_summary"] = decision_text
        state["web_offers"] = []
        trace: AgentTrace = {
            "agent_name": "Web Research Agent",
            "status": "SUCCESS",
            "llm_mode": "DETERMINISTIC_FALLBACK",
            "input_data": {"product": product},
            "decision": decision_text,
            "tools_used": [],
            "tool_data": None,
            "evidence": {"ambiguous_product": True},
            "output_data": {"status": "SKIPPED", "offers_found": 0}
        }
        state["agent_traces"].append(trace)
        state["audit_log"].append(f"[Web Research Agent]\n{decision_text}")
        return state

    qty = state.get("quantity_to_order") or state.get("final_order_quantity") or 1
    deadline = state.get("deadline")
    budget_cap = 100000.0

    # Discover and normalize online offers
    research_result = discover_online_offers(
        product=product,
        quantity=qty,
        budget_constraints=budget_cap,
        required_delivery_date=deadline,
        location="India"
    )

    offers = research_result.get("offers", [])
    state["web_offers"] = offers
    state["web_research_status"] = research_result.get("status", "COMPLETED")
    state["web_research_summary"] = research_result.get("summary", "")

    # LLM analysis / synthesis if LLM available
    llm_mode = "DETERMINISTIC_FALLBACK"
    if offers:
        system_prompt = (
            "You are an enterprise Web Research Agent for AI-EOS. Summarize public marketplace offers found "
            "and compare price ranges against corporate expectations. Keep reasons objective and evidence-backed."
        )
        user_prompt = (
            f"Product: {product}. Quantity: {qty}. Budget Cap: ₹{budget_cap:,}. "
            f"Online offers found: {offers}."
        )
        llm_res, mode, _ = invoke_llm_structured(system_prompt, user_prompt, WebResearchOutput)
        if llm_res:
            llm_mode = "LIVE_LLM"
            decision_text = f"MARKETPLACE INTELLIGENCE: {llm_res.findings_summary} {llm_res.marketplace_insight}"
        else:
            valid_prices = [o['unit_price'] for o in offers if o.get('unit_price')]
            min_price_str = f"₹{min(valid_prices):,}/unit" if valid_prices else "Prices unverified"
            decision_text = (
                f"MARKETPLACE INTELLIGENCE: Discovered {len(offers)} public online offer(s) for '{product}' "
                f"across platforms: {', '.join(set(o['source_name'] for o in offers))}. "
                f"Lowest online price: {min_price_str}. "
                f"Retaining data with explicit verification markers."
            )
    else:
        decision_text = (
            f"WEB RESEARCH NOTICE: No verified online offers found matching '{product}'. "
            f"Retaining internal PostgreSQL supplier catalog."
        )

    trace: AgentTrace = {
        "agent_name": "Web Research Agent",
        "status": "SUCCESS",
        "llm_mode": llm_mode,
        "input_data": {
            "product": product,
            "quantity": qty,
            "budget_cap": budget_cap,
            "deadline": deadline,
            "sources_queried": research_result.get("sources_queried", [])
        },
        "decision": decision_text,
        "tools_used": ["web_crawler::public_retailer_feeds", "search::public_web"],
        "tool_data": {
            "offers_count": len(offers),
            "sources": research_result.get("sources_queried", []),
            "retrieved_at": research_result.get("retrieved_at")
        },
        "evidence": {
            "offers_evaluated": [
                {
                    "source": o.get("source_name"),
                    "model": o.get("model"),
                    "unit_price": o.get("unit_price"),
                    "total_cost": o.get("total_cost"),
                    "delivery_days": o.get("delivery_days"),
                    "verification": o.get("verification_status"),
                    "url": o.get("url")
                }
                for o in offers
            ]
        },
        "output_data": {
            "status": state["web_research_status"],
            "offers_count": len(offers),
            "summary": state["web_research_summary"]
        }
    }
    state["agent_traces"].append(trace)
    state["audit_log"].append(f"[Web Research Agent]\n{decision_text}")

    return state
