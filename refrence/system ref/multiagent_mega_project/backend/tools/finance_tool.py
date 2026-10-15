from typing import Dict, Any
from database.db import get_finance_budget_status

def check_budget(amount: int) -> Dict[str, Any]:
    """
    Validates requested expenditure against authorized corporate budget limits from database.
    Hard limit is ₹100,000. Any purchase > ₹100,000 is rejected immediately.
    """
    db_budget = get_finance_budget_status()
    available = db_budget["available_budget"]
    hard_limit = db_budget["hard_limit"]
    
    # Policy: Order must not exceed available budget AND must not exceed corporate hard limit of ₹100,000
    is_approved = (amount <= available) and (amount <= hard_limit)
    
    return {
        "fiscal_period": db_budget.get("fiscal_period", "FY-2026-Q4"),
        "total_budget": db_budget.get("total_budget", 100000),
        "available_budget": available,
        "purchase_amount": amount,
        "remaining_budget": max(0, available - amount) if is_approved else available,
        "over_budget_by": max(0, amount - min(available, hard_limit)),
        "hard_limit": hard_limit,
        "status": "APPROVED" if is_approved else "REJECTED",
        "data_source": db_budget.get("data_source", "finance_budgets")
    }

def query_budget_direct() -> Dict[str, Any]:
    """
    Read-only tool for budget queries (e.g. 'How much budget is left?').
    Never triggers procurement or PO creation.
    """
    db_budget = get_finance_budget_status()
    return {
        "fiscal_period": db_budget["fiscal_period"],
        "total_budget": db_budget["total_budget"],
        "spent_budget": db_budget["spent_budget"],
        "available_budget": db_budget["available_budget"],
        "hard_limit": db_budget["hard_limit"],
        "currency": db_budget["currency"],
        "data_source": db_budget["data_source"],
        "summary": f"Authorized fiscal budget for {db_budget['fiscal_period']} is ₹{db_budget['total_budget']:,}. Spent to date: ₹{db_budget['spent_budget']:,}. Current available budget: ₹{db_budget['available_budget']:,} (Hard ceiling: ₹{db_budget['hard_limit']:,})."
    }
