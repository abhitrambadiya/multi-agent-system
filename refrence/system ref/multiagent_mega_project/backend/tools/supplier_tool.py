from typing import List, Dict, Any, Optional
from database.db import get_supplier_quotes_for_product, list_all_suppliers

def get_suppliers(product: str) -> List[Dict[str, Any]]:
    """Retrieves real supplier quotes from database for a product."""
    normalized = product.strip() if product else ""
    return get_supplier_quotes_for_product(normalized)

def query_suppliers_direct(product: Optional[str] = None) -> Dict[str, Any]:
    """
    Read-only tool for supplier queries (e.g. 'Who are the suppliers for Laptop Stand?').
    Never triggers procurement or PO creation.
    """
    if product and product.strip():
        quotes = get_supplier_quotes_for_product(product.strip())
        return {
            "found": len(quotes) > 0,
            "product": product,
            "quotes": quotes,
            "suppliers": quotes,
            "summary": f"Found {len(quotes)} approved supplier quote(s) for '{product}'."
        }
    else:
        all_s = list_all_suppliers()
        return {
            "found": True,
            "suppliers": all_s,
            "total": len(all_s),
            "summary": f"Retrieved {len(all_s)} supplier records from approved vendor registry."
        }
