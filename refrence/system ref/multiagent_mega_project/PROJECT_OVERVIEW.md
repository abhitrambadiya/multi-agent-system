# AI-EOS MVP: Autonomous Multi-Agent Supply Chain & Procurement Workforce

## 1. Overview & Concept
**AI-EOS (AI Enterprise Operating System)** is an autonomous multi-agent decision and execution engine for enterprise supply chain and procurement workflows. 

Traditional enterprise resource planning (ERP) systems require manual human intervention across multiple departments whenever inventory falls below safety thresholds. AI-EOS automates this end-to-end lifecycle while enforcing strict corporate governance:
1. Ingesting **unstructured, natural language business events** (e.g., *"Server Rack stock has fallen to 2 units. The minimum required stock is 15 units."*).
2. Delegating specialized tasks across a **collaborative workforce of AI agents** (inventory assessment, vendor quote comparison, financial budgeting, and risk analysis).
3. Enforcing enterprise compliance via a **MANDATORY Human-in-the-Loop (HITL)** approval gate for **EVERY** purchase order, regardless of transaction amount.
4. Autonomously creating verifiable purchase orders **only upon verified human approval**.
5. Blocking budget-overflow transactions before the approval gate without human override.
6. Providing full transparency with real-time agent reasoning traces, multi-quote comparisons, pre-approval breakdowns, and an immutable audit log.

---

## 2. System Architecture & Tech Stack

```
                              [ Natural Language Business Event ]
                                               │
                                               ▼
                              [ React + Vite Frontend Dashboard ]
                                               │  HTTP REST (Axios)
                                               ▼
                                   [ FastAPI Backend Server ]
                                               │
                                               ▼
                                 [ LangGraph Stateful Graph ]
                                               │
                ┌──────────────────────────────┴──────────────────────────────┐
                │                                                             │
        1. Manager Agent (Validates event & extracts data)            Workflow State Checkpointing
                │                                                     (LangGraph MemorySaver)
                ├─────────────────────────────────────────────┐               │
                │ (Valid Event)                               │ (Invalid)     │
                ▼                                             ▼               │
        2. Inventory Agent (check_inventory)             7. Audit Logger      │
                ▼                                             ▼               │
        3. Procurement Agent (get_suppliers)                [ END ]           │
                ▼                                                             │
        4. Finance Agent (check_budget)                                       │
                ▼                                                             │
        5. Risk Engine (Total Spend & Risk Classification)                    │
                │                                                             │
                ├─────────────────────────────────────────────┬───────────────┤
                │ (All Valid Purchases <= ₹100,000)           │ ("BLOCKED")   │
                ▼                                             ▼               │
       [ Human Approval Node ] (MANDATORY HITL)        7. Audit Logger        │
       (Execution Paused at Checkpoint)                       ▼               │
                │                                           [ END ]           │
        ┌───────┴───────┐                                                     │
        │ APPROVE       │ REJECT                                              │
        ▼               ▼                                                     │
 6. Execution Agent  [ Bypassed ]                                             │
 (execute_purchase)     │                                                     │
        ▼               │                                                     │
 7. Audit Logger ◄──────┘                                                     │
        ▼                                                                     │
      [ END ] ◄───────────────────────────────────────────────────────────────┘
```

### Technology Breakdown
- **Orchestration & State Machine:** [LangGraph](https://github.com/langchain-ai/langgraph) (`StateGraph`, conditional edges, `MemorySaver` thread checkpointing, `interrupt_before=["human_approval"]`).
- **Backend API:** [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic v2](https://docs.pydantic.dev/).
- **LLM Engine:** [LangChain](https://www.langchain.com/) + `langchain-openai` (`ChatOpenAI` / `gpt-4o-mini`) using structured outputs with honest deterministic fallback handlers when offline or unconfigured.
- **Frontend Dashboard:** [React 19](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS v4](https://tailwindcss.com/), [Lucide-react](https://lucide.dev/).

---

## 3. Workflow State Schema

The entire workflow executes over a typed, centralized state:

```python
class AgentTrace(TypedDict):
    agent_name: str
    status: str  # "SUCCESS", "PAUSED", "REJECTED", "BLOCKED", "FAILED"
    llm_mode: str  # "LIVE_LLM", "DETERMINISTIC_FALLBACK"
    input_data: Dict[str, Any]
    decision: str
    tools_used: List[str]
    tool_data: Optional[Dict[str, Any]]
    evidence: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]

class WorkflowState(TypedDict):
    business_event: str
    status: str  # "RUNNING", "COMPLETED", "PAUSED_FOR_APPROVAL", "REJECTED", "BLOCKED", "FAILED"
    error_message: Optional[str]
    llm_mode: Optional[str]  # "LIVE_LLM" or "DETERMINISTIC_FALLBACK"
    product: Optional[str]
    current_stock: Optional[int]
    minimum_stock: Optional[int]
    business_objective: Optional[str]
    
    inventory_result: Optional[dict]
    procurement_result: Optional[dict]
    finance_result: Optional[dict]
    risk_result: Optional[dict]
    approval_status: Optional[str]
    approved_transaction: Optional[dict]
    execution_result: Optional[dict]
    
    agent_traces: List[AgentTrace]
    audit_log: List[str]
```

---

## 4. Mandatory Human-in-the-Loop Governance & Execution Guards

### Mandatory Approval for ALL Purchases
1. **Universal Approval Gate:** Low-risk (< ₹50,000) and High-risk ($\ge$ ₹50,000) transactions **both pause at the human approval gate**. The ₹50,000 threshold classifies the risk tier, but never bypasses supervisor authorization.
2. **Hard Budget Cap (₹100,000):** If an order exceeds available departmental budget, it is flagged as `BLOCKED` and routed directly to audit. No human approval controls are shown, and approval requests submitted to the API are rejected with HTTP 400.
3. **Multi-Condition Execution Guards:** In `backend/agents/execution.py`, the purchase tool will **only** execute if:
   - Order passes budget and policy validation (`cost <= 100000`, `risk_level != "BLOCKED"`).
   - Approval status is explicitly `APPROVED`.
   - The approved supplier, product, quantity, and total cost match the executed transaction.
   - The transaction has not already been executed (preventing duplicate POs).

---

## 5. Agents and Tools Specification

### Agents (`backend/agents/`)

| Agent | File | Purpose | Logic & Behavior |
| :--- | :--- | :--- | :--- |
| **Manager Agent** | `backend/agents/manager.py` | Event Interpretation & Validation | Parses natural language events, validates actionable replenishment requests, extracts target product and stock levels without inventing data, and halts invalid events. |
| **Inventory Agent** | `backend/agents/inventory.py` | Stock Analysis | Invokes `check_inventory`, reconciles warehouse stock against safety minimums, and computes shortfall: $\max(0, \text{required} - \text{current})$. |
| **Procurement Agent** | `backend/agents/procurement.py` | Sourcing & Vendor Evaluation | Queries `get_suppliers`, evaluates multi-attribute quotes (price, delivery lead time, rating), selects optimal vendor, and computes total acquisition cost. |
| **Finance Agent** | `backend/agents/finance.py` | Budget Validation | Calls `check_budget` to verify order total against the departmental ₹100,000 fiscal cap and calculates remaining headroom or deficit. |
| **Risk Engine** | `backend/agents/risk.py` | Governance & Policy Engine | Classifies spend tier (`LOW` vs `HIGH`), blocks transactions exceeding ₹100k, and pauses **ALL** valid transactions for human approval. |
| **Execution Agent** | `backend/agents/execution.py` | Guarded Order Placement | Enforces strict validation guards: verifies approval, matching parameters, and lack of duplicate POs before invoking `execute_purchase`. |
| **Audit Logger** | `backend/agents/audit.py` | Trace Finalization | Seals the append-only audit trail and compiles the final ledger status. |

---

## 6. Business Test Scenarios

The system natively handles all business scenarios:

1. **Case A: Low Risk (< ₹50,000) — Mandatory Approval**
   - *Input:* "Laptop Stand inventory has dropped to 12. Minimum required is 50."
   - *Behavior:* Shortfall 38 units @ ₹850 = ₹32,300. Pauses at checkpoint awaiting Human Approval.
   - *Approve:* Supervisor approves $\rightarrow$ PO issued (`PO-2026-XXXXXXXX`). Status: `COMPLETED`.
   - *Reject:* Supervisor rejects $\rightarrow$ PO execution skipped. Status: `REJECTED`.
2. **Case B: High Risk (>= ₹50,000, <= ₹100,000) — Mandatory Approval**
   - *Input:* "Server Rack stock has fallen to 2 units. The minimum required stock is 15 units."
   - *Behavior:* Shortfall 13 units @ ₹6,000 = ₹78,000. Pauses at checkpoint awaiting Human Approval.
   - *Approve:* Supervisor approves $\rightarrow$ PO issued. Status: `COMPLETED`.
   - *Reject:* Supervisor rejects $\rightarrow$ PO execution skipped. Status: `REJECTED`.
3. **Case C: Insufficient Budget (> ₹100,000) — Blocked Before Gate**
   - *Input:* "Industrial Server Rack stock has fallen to 2 units. The minimum required is 20 units."
   - *Behavior:* Shortfall 18 units @ ₹6,500 = ₹1,17,000. Exceeds ₹100k cap.
   - *Outcome:* Policy blocks transaction immediately. Status: `BLOCKED`. Approval gate bypassed; no PO can be created.
4. **Case D: Invalid Business Event**
   - *Input:* "All team members should attend the company town hall tomorrow at 3 PM."
   - *Outcome:* Manager agent rejects event. Status: `FAILED`. No PO created.

---

## 7. How to Run Locally

### Backend
```bash
cd backend
source venv/bin/activate

# (Optional: set OPENAI_API_KEY for live GPT-4o-mini structured reasoning)
# export OPENAI_API_KEY="sk-..."

python main.py
# Backend runs on http://localhost:8000
```

### Running Automated Tests
```bash
PYTHONPATH=backend backend/venv/bin/pytest backend/test_workflows.py backend/test_api_endpoints.py -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Dashboard runs on http://localhost:5173
```
