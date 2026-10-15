from typing import Optional, Dict, Any, List
from database.db import get_inventory_record, list_all_inventory, record_stock_movement

def check_inventory(
    product: str,
    supplied_current: Optional[int] = None,
    supplied_minimum: Optional[int] = None,
    requested_quantity: Optional[int] = None,
    quantity_semantics: Optional[str] = "UNSPECIFIED",
    additional_quantity: Optional[int] = None,
    demand_quantity: Optional[int] = None,
    target_total_stock: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieves real inventory from database and calculates:
    - current_stock: actual units available in warehouse
    - minimum_stock_level: safety threshold from inventory policy
    - demand_shortfall: additional units required to satisfy immediate requested demand
    - replenishment_quantity: units needed to restore safety stock max(0, min_stock - current_stock)
    - quantity_to_order: primary quantity to order for immediate demand or replenishment
    """
    normalized_product = product.strip() if product else "Unknown"
    db_item = get_inventory_record(normalized_product)
    
    if db_item:
        resolved_product = db_item["product"]
        location = db_item["location"]
        db_current = db_item["current_stock"]
        db_min = db_item["minimum_stock"]
        unit_cost = db_item["unit_cost_estimate"]
        data_source = db_item["data_source"]
    else:
        resolved_product = normalized_product
        location = "General Storage"
        db_current = 10
        db_min = 30
        unit_cost = 1000.0
        data_source = "database::catalog_fallback"

    current = supplied_current if (supplied_current is not None and supplied_current >= 0) else db_current
    minimum = supplied_minimum if (supplied_minimum is not None and supplied_minimum > 0) else db_min
    
    # Calculate replenishment quantity to restore minimum safety threshold
    replenishment_quantity = max(0, minimum - current)

    # Calculate demand shortfall based on explicit quantity semantics
    if quantity_semantics == "ADDITIONAL_QUANTITY" or (additional_quantity is not None and additional_quantity > 0):
        # User requested additional/more units (e.g. "need 8 more" -> order 8 additional units)
        add_val = additional_quantity if additional_quantity is not None else (requested_quantity or 0)
        demand_shortfall = add_val
        quantity_to_order = add_val
    elif quantity_semantics == "TARGET_STOCK" or (target_total_stock is not None and target_total_stock > 0):
        # User requested to reach target total stock level
        tgt_val = target_total_stock if target_total_stock is not None else (requested_quantity or 0)
        demand_shortfall = max(0, tgt_val - current)
        quantity_to_order = demand_shortfall
    elif quantity_semantics == "TOTAL_DEMAND" or (demand_quantity is not None and demand_quantity > 0):
        # User requested explicit total demand (e.g. "needs 8 in total" when 12 on hand -> 0 needed; "needs 20 in total" -> 8 needed)
        tot_val = demand_quantity if demand_quantity is not None else (requested_quantity or 0)
        demand_shortfall = max(0, tot_val - current)
        quantity_to_order = demand_shortfall
    elif requested_quantity is not None and requested_quantity > 0:
        # Standard demand shortfall
        demand_shortfall = max(0, requested_quantity - current)
        quantity_to_order = demand_shortfall
    else:
        # General restock / replenishment request without explicit demand
        demand_shortfall = None
        quantity_to_order = replenishment_quantity

    status = "LOW_STOCK" if current < minimum else "SUFFICIENT_STOCK"
    
    return {
        "product": resolved_product,
        "current_stock": current,
        "required_stock": minimum,
        "minimum_stock_level": minimum,
        "requested_quantity": requested_quantity,
        "demand_shortfall": demand_shortfall,
        "replenishment_quantity": replenishment_quantity,
        "quantity_to_order": quantity_to_order,
        "unit_cost_estimate": unit_cost,
        "status": status,
        "location": location,
        "data_source": data_source,
    }

def query_inventory_direct(
    product: Optional[str] = None,
    sub_intent: Optional[str] = "current_count",
    stated_demand: Optional[int] = None
) -> Dict[str, Any]:
    """
    Read-only tool for inventory queries.
    Distinguishes:
    - current_count: Returns actual on-hand stock count.
    - safety_threshold_replenishment: Returns additional units needed as max(0, safety_threshold - current_stock).
    - demand_shortfall: Returns additional units needed to meet stated demand as max(0, stated_demand - current_stock).
    - general_shortfall_analysis: Returns both current stock, threshold, and safety deficit.
    Never triggers procurement or PO creation.
    """
    if product and product.strip():
        item = get_inventory_record(product.strip())
        if item:
            current_stock = item["current_stock"]
            minimum_stock = item["minimum_stock"]
            safety_deficit = max(0, minimum_stock - current_stock)

            if sub_intent == "safety_threshold_replenishment":
                summary = (
                    f"To reach the configured safety threshold of {minimum_stock} units for {item['product']}, "
                    f"{safety_deficit} additional unit(s) are needed "
                    f"(Current usable stock: {current_stock} units, Safety threshold: {minimum_stock} units at {item['location']})."
                )
                return {
                    "status": "SUCCESS",
                    "found": True,
                    "product": item["product"],
                    "sub_intent": "safety_threshold_replenishment",
                    "current_stock": current_stock,
                    "minimum_stock": minimum_stock,
                    "safety_threshold": minimum_stock,
                    "units_needed": safety_deficit,
                    "units_needed_for_safety": safety_deficit,
                    "additional_units_required": safety_deficit,
                    "location": item["location"],
                    "data_source": item["data_source"],
                    "summary": summary
                }
            elif sub_intent == "demand_shortfall":
                demand = stated_demand or 0
                shortfall = max(0, demand - current_stock)
                summary = (
                    f"To satisfy the stated demand of {demand} units for {item['product']}, "
                    f"{shortfall} additional unit(s) are needed "
                    f"(Current usable stock: {current_stock} units, Safety threshold: {minimum_stock} units at {item['location']})."
                )
                return {
                    "status": "SUCCESS",
                    "found": True,
                    "product": item["product"],
                    "sub_intent": "demand_shortfall",
                    "current_stock": current_stock,
                    "minimum_stock": minimum_stock,
                    "stated_demand": demand,
                    "units_needed": shortfall,
                    "demand_shortfall": shortfall,
                    "additional_units_required": shortfall,
                    "location": item["location"],
                    "data_source": item["data_source"],
                    "summary": summary
                }
            elif sub_intent == "general_shortfall_analysis":
                summary = (
                    f"Stock analysis for {item['product']}: {current_stock} units available vs safety threshold of {minimum_stock}. "
                    f"{'Safety deficit of ' + str(safety_deficit) + ' units.' if safety_deficit > 0 else 'Stock is above safety threshold.'}"
                )
                return {
                    "status": "SUCCESS",
                    "found": True,
                    "product": item["product"],
                    "sub_intent": "general_shortfall_analysis",
                    "current_stock": current_stock,
                    "minimum_stock": minimum_stock,
                    "safety_threshold": minimum_stock,
                    "units_needed_for_safety": safety_deficit,
                    "additional_units_required": safety_deficit,
                    "location": item["location"],
                    "data_source": item["data_source"],
                    "summary": summary
                }
            else:
                # Default: current_count
                return {
                    "status": "SUCCESS",
                    "found": True,
                    "product": item["product"],
                    "sub_intent": "current_count",
                    "current_stock": current_stock,
                    "minimum_stock": minimum_stock,
                    "location": item["location"],
                    "data_source": item["data_source"],
                    "summary": f"There are {current_stock} units of {item['product']} in stock at {item['location']} (safety threshold: {minimum_stock})."
                }
        else:
            return {
                "status": "NOT_FOUND",
                "found": False,
                "product": product,
                "sub_intent": sub_intent,
                "current_stock": 0,
                "summary": f"No inventory record found for '{product}' in warehouse catalog."
            }
    else:
        all_items = list_all_inventory()
        return {
            "found": True,
            "items": all_items,
            "total_skus": len(all_items),
            "summary": f"Catalog contains {len(all_items)} active inventory items across facilities."
        }
