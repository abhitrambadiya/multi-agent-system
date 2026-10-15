import uuid
from typing import Dict, Any, Optional
from database.db import insert_purchase_order, get_purchase_order_by_id, list_recent_purchase_orders, record_stock_movement, record_budget_expenditure

def execute_purchase(
    supplier: str,
    product: str,
    quantity: int,
    cost: int,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates and persists a simulated purchase order in the database.
    Updates inventory stock movement and finance budget expenditure.
    """
    po_id = f"PO-2026-{str(uuid.uuid4())[:8].upper()}"
    unit_price = int(cost / quantity) if quantity > 0 else 0
    
    # 1. Persist purchase order into database
    record = insert_purchase_order(
        po_id=po_id,
        thread_id=thread_id or "direct_exec",
        supplier=supplier,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        total_cost=cost,
        status="CREATED"
    )
    
    # 2. Update stock movement in inventory database
    try:
        record_stock_movement(product, quantity, f"PO fulfillment: {po_id}")
    except Exception:
        pass
        
    # 3. Update budget expenditure in finance database
    try:
        record_budget_expenditure(cost)
    except Exception:
        pass
        
    return record

def query_purchase_orders_direct(po_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Read-only tool for purchase order queries (e.g. 'Show recent POs' or 'Status of PO-123').
    Never creates new purchase orders.
    """
    if po_id and po_id.strip():
        rec = get_purchase_order_by_id(po_id.strip())
        if rec:
            return {
                "found": True,
                "order": rec,
                "summary": f"Purchase Order {rec['po_id']} for {rec['quantity']} units of '{rec['product']}' with {rec['supplier']} is {rec['status']} (Total: ₹{rec['total_cost']:,})."
            }
        return {
            "found": False,
            "po_id": po_id,
            "summary": f"No purchase order found matching identifier '{po_id}'."
        }
    else:
        orders = list_recent_purchase_orders(10)
        return {
            "found": True,
            "orders": orders,
            "total": len(orders),
            "summary": f"Retrieved {len(orders)} recent purchase order(s) from database."
        }
