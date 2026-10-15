import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import psycopg2
import psycopg2.extras

# Determine database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/aieos")
SQLITE_PATH = Path(__file__).resolve().parent.parent / "aieos.db"

_USE_POSTGRES = True

def get_connection():
    """
    Returns an open DB connection.
    Attempts PostgreSQL first; if unreachable, falls back gracefully to SQLite.
    """
    global _USE_POSTGRES
    if _USE_POSTGRES:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn, "POSTGRES"
        except Exception:
            _USE_POSTGRES = False
    
    # SQLite fallback
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn, "SQLITE"

def init_db():
    """Initializes tables and seeds initial data across all agent domains."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Inventory Domain (Inventory Agent)
        if engine == "POSTGRES":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id SERIAL PRIMARY KEY,
                    product VARCHAR(255) UNIQUE NOT NULL,
                    current_stock INTEGER NOT NULL DEFAULT 0,
                    minimum_stock INTEGER NOT NULL DEFAULT 10,
                    location VARCHAR(255) NOT NULL DEFAULT 'General Storage',
                    unit_cost_estimate NUMERIC(10, 2) DEFAULT 0.0,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    product VARCHAR(255) NOT NULL,
                    quantity_change INTEGER NOT NULL,
                    reason VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product TEXT UNIQUE NOT NULL,
                    current_stock INTEGER NOT NULL DEFAULT 0,
                    minimum_stock INTEGER NOT NULL DEFAULT 10,
                    location TEXT NOT NULL DEFAULT 'General Storage',
                    unit_cost_estimate REAL DEFAULT 0.0,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product TEXT NOT NULL,
                    quantity_change INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

        # 2. Suppliers Domain (Procurement Agent)
        if engine == "POSTGRES":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    rating NUMERIC(3, 2) NOT NULL DEFAULT 4.5,
                    reliability_score NUMERIC(3, 2) NOT NULL DEFAULT 0.95,
                    contact_email VARCHAR(255)
                );
                CREATE TABLE IF NOT EXISTS supplier_quotes (
                    id SERIAL PRIMARY KEY,
                    supplier_name VARCHAR(255) NOT NULL,
                    product VARCHAR(255) NOT NULL,
                    unit_price INTEGER NOT NULL,
                    delivery_days INTEGER NOT NULL DEFAULT 2,
                    in_stock BOOLEAN NOT NULL DEFAULT TRUE,
                    rating NUMERIC(3, 2) NOT NULL DEFAULT 4.5
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    rating REAL NOT NULL DEFAULT 4.5,
                    reliability_score REAL NOT NULL DEFAULT 0.95,
                    contact_email TEXT
                );
                CREATE TABLE IF NOT EXISTS supplier_quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_name TEXT NOT NULL,
                    product TEXT NOT NULL,
                    unit_price INTEGER NOT NULL,
                    delivery_days INTEGER NOT NULL DEFAULT 2,
                    in_stock INTEGER NOT NULL DEFAULT 1,
                    rating REAL NOT NULL DEFAULT 4.5
                );
            """)

        # 3. Finance Domain (Finance Agent)
        if engine == "POSTGRES":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS finance_budgets (
                    id SERIAL PRIMARY KEY,
                    fiscal_period VARCHAR(50) UNIQUE NOT NULL,
                    total_budget INTEGER NOT NULL DEFAULT 100000,
                    spent_budget INTEGER NOT NULL DEFAULT 0,
                    hard_limit INTEGER NOT NULL DEFAULT 100000,
                    currency VARCHAR(10) NOT NULL DEFAULT 'INR'
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS finance_budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fiscal_period TEXT UNIQUE NOT NULL,
                    total_budget INTEGER NOT NULL DEFAULT 100000,
                    spent_budget INTEGER NOT NULL DEFAULT 0,
                    hard_limit INTEGER NOT NULL DEFAULT 100000,
                    currency TEXT NOT NULL DEFAULT 'INR'
                );
            """)

        # 4. Procurement & Orders Domain (Execution Agent)
        if engine == "POSTGRES":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id SERIAL PRIMARY KEY,
                    po_id VARCHAR(100) UNIQUE NOT NULL,
                    thread_id VARCHAR(100),
                    supplier VARCHAR(255) NOT NULL,
                    product VARCHAR(255) NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    total_cost INTEGER NOT NULL,
                    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
                    status VARCHAR(50) NOT NULL DEFAULT 'CREATED',
                    approved_by VARCHAR(100) DEFAULT 'Human Supervisor',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id TEXT UNIQUE NOT NULL,
                    thread_id TEXT,
                    supplier TEXT NOT NULL,
                    product TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price INTEGER NOT NULL,
                    total_cost INTEGER NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'INR',
                    status TEXT NOT NULL DEFAULT 'CREATED',
                    approved_by TEXT DEFAULT 'Human Supervisor',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

        # 5. Audit Domain (Audit Agent)
        if engine == "POSTGRES":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(100),
                    agent_name VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    llm_mode VARCHAR(50) NOT NULL,
                    decision TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        else:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    llm_mode TEXT NOT NULL,
                    decision TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)

        conn.commit()

        # Seed initial catalog items if empty
        _seed_data(conn, engine)
        
    finally:
        conn.close()

def _seed_data(conn, engine):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM inventory_items;")
    count = cur.fetchone()[0]
    if count == 0:
        # Seed inventory
        items = [
            ("Laptop Stand", 12, 50, "Warehouse A-12", 850.0),
            ("Wireless Mouse", 5, 20, "Warehouse A-04", 1450.0),
            ("Server Rack", 2, 15, "Data Center Logistics DC-1", 6000.0),
            ("Industrial Server Rack", 2, 20, "Enterprise Storage DC-2", 6500.0),
            ("Laptops", 2, 30, "General Storage IT-Bay", 1200.0),
            ("Industrial Rivets", 50, 200, "Warehouse B-08", 25.0),
        ]
        param = "%s" if engine == "POSTGRES" else "?"
        for it in items:
            cur.execute(
                f"INSERT INTO inventory_items (product, current_stock, minimum_stock, location, unit_cost_estimate) VALUES ({param}, {param}, {param}, {param}, {param})",
                it
            )
        
        # Seed suppliers and quotes
        quotes = [
            ("ABC Supplies", "Laptop Stand", 850, 2, True, 4.8),
            ("XYZ Traders", "Laptop Stand", 900, 1, True, 4.5),
            ("Global Tech", "Wireless Mouse", 1450, 2, True, 4.7),
            ("Tech Parts Inc.", "Wireless Mouse", 1500, 3, True, 4.6),
            ("Enterprise IT", "Server Rack", 6000, 3, True, 4.9),
            ("RackMasters", "Server Rack", 6200, 2, True, 4.6),
            ("MegaInfra Solutions", "Industrial Server Rack", 6500, 5, True, 4.8),
            ("Titan Heavy IT", "Industrial Server Rack", 6800, 4, True, 4.7),
            ("Premier Vendor Alliance", "Laptops", 1200, 3, True, 4.5),
            ("Rapid Supply Direct", "Laptops", 1350, 1, True, 4.2),
            ("Zenith Systems", "Laptops", 1400, 2, True, 4.6),
            ("Apex Industrial Fasteners", "Industrial Rivets", 25, 2, True, 4.8),
            ("Global Rivet Corp", "Industrial Rivets", 28, 4, True, 4.5),
        ]
        for q in quotes:
            cur.execute(
                f"INSERT INTO supplier_quotes (supplier_name, product, unit_price, delivery_days, in_stock, rating) VALUES ({param}, {param}, {param}, {param}, {param}, {param})",
                (q[0], q[1], q[2], q[3], q[4] if engine == "POSTGRES" else (1 if q[4] else 0), q[5])
            )

        # Seed budget
        cur.execute(
            f"INSERT INTO finance_budgets (fiscal_period, total_budget, spent_budget, hard_limit, currency) VALUES ({param}, {param}, {param}, {param}, {param})",
            ("FY-2026-Q4", 100000, 0, 100000, "INR")
        )

        conn.commit()
    else:
        # If supplier_quotes already seeded, ensure 3rd quote for Laptops exists
        cur.execute("SELECT COUNT(*) FROM supplier_quotes WHERE supplier_name = 'Zenith Systems' AND LOWER(product) = 'laptops';")
        if cur.fetchone()[0] == 0:
            param = "%s" if engine == "POSTGRES" else "?"
            cur.execute(
                f"INSERT INTO supplier_quotes (supplier_name, product, unit_price, delivery_days, in_stock, rating) VALUES ({param}, {param}, {param}, {param}, {param}, {param})",
                ("Zenith Systems", "Laptops", 1400, 2, True if engine == "POSTGRES" else 1, 4.6)
            )
            conn.commit()

def reset_db_state():
    """Resets the spent budget to 0 and restores default inventory stock for test/runtime isolation."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute("UPDATE finance_budgets SET spent_budget = 0;")
        # Reset inventory counts to their defaults
        items = [
            ("Laptop Stand", 12),
            ("Wireless Mouse", 5),
            ("Server Rack", 2),
            ("Industrial Server Rack", 2),
            ("Laptops", 2),
            ("Industrial Rivets", 50),
        ]
        for prod, stock in items:
            cur.execute(f"UPDATE inventory_items SET current_stock = {param} WHERE LOWER(product) = LOWER({param})", (stock, prod))
        conn.commit()
    finally:
        conn.close()

# ─── AGENT DOMAIN ACCESSORS ──────────────────────────────────────────────────

# 1. Inventory Agent Domain Operations
def get_inventory_record(product_query: str) -> Optional[Dict[str, Any]]:
    """Retrieves an inventory record for a product using case-insensitive partial match."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        p = product_query.strip().lower()
        param = "%s" if engine == "POSTGRES" else "?"
        # Try exact match first, then ILIKE / LIKE
        cur.execute(f"SELECT product, current_stock, minimum_stock, location, unit_cost_estimate FROM inventory_items WHERE LOWER(product) = {param}", (p,))
        row = cur.fetchone()
        if not row:
            # Try fuzzy/contains match
            like_param = f"%{p}%"
            cur.execute(f"SELECT product, current_stock, minimum_stock, location, unit_cost_estimate FROM inventory_items WHERE LOWER(product) LIKE {param} LIMIT 1", (like_param,))
            row = cur.fetchone()
        
        if row:
            return {
                "product": row[0],
                "current_stock": row[1],
                "minimum_stock": row[2],
                "location": row[3],
                "unit_cost_estimate": float(row[4] or 0.0),
                "data_source": f"{engine}::inventory_items"
            }
        return None
    finally:
        conn.close()

def list_all_inventory() -> List[Dict[str, Any]]:
    """Lists all catalog items in inventory."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT product, current_stock, minimum_stock, location, unit_cost_estimate FROM inventory_items ORDER BY product")
        rows = cur.fetchall()
        return [
            {
                "product": r[0],
                "current_stock": r[1],
                "minimum_stock": r[2],
                "location": r[3],
                "unit_cost_estimate": float(r[4] or 0.0),
                "data_source": f"{engine}::inventory_items"
            }
            for r in rows
        ]
    finally:
        conn.close()

def record_stock_movement(product: str, quantity_change: int, reason: str):
    """Updates current stock and writes a movement log."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(f"UPDATE inventory_items SET current_stock = current_stock + {param} WHERE LOWER(product) = LOWER({param})", (quantity_change, product))
        cur.execute(f"INSERT INTO stock_movements (product, quantity_change, reason) VALUES ({param}, {param}, {param})", (product, quantity_change, reason))
        conn.commit()
    finally:
        conn.close()

# 2. Supplier Domain Operations (Procurement Agent)
def get_supplier_quotes_for_product(product: str) -> List[Dict[str, Any]]:
    """Retrieves real supplier quotes from database for product."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        p = product.strip().lower()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(
            f"SELECT supplier_name, product, unit_price, delivery_days, in_stock, rating FROM supplier_quotes WHERE LOWER(product) = {param} OR LOWER(product) LIKE {param} ORDER BY unit_price ASC",
            (p, f"%{p}%")
        )
        rows = cur.fetchall()
        if rows:
            return [
                {
                    "name": r[0],
                    "product": r[1],
                    "unit_price": r[2],
                    "delivery_days": r[3],
                    "in_stock": bool(r[4]),
                    "rating": float(r[5]),
                    "reliability_score": round(float(r[5]) / 5.0, 2),
                    "currency": "INR",
                    "data_source": f"{engine}::supplier_quotes"
                }
                for r in rows
            ]
        # Default dynamic market fallback if product is new
        return [
            {"name": "Premier Vendor Alliance", "product": product, "unit_price": 1200, "delivery_days": 3, "in_stock": True, "rating": 4.5, "data_source": f"{engine}::market_benchmark"},
            {"name": "Rapid Supply Direct", "product": product, "unit_price": 1350, "delivery_days": 1, "in_stock": True, "rating": 4.2, "data_source": f"{engine}::market_benchmark"}
        ]
    finally:
        conn.close()

def list_all_suppliers() -> List[Dict[str, Any]]:
    """Lists distinct suppliers and active quotes."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT supplier_name, product, unit_price, delivery_days, rating FROM supplier_quotes ORDER BY supplier_name")
        rows = cur.fetchall()
        return [
            {
                "supplier_name": r[0],
                "product": r[1],
                "unit_price": r[2],
                "delivery_days": r[3],
                "rating": float(r[4]),
                "data_source": f"{engine}::supplier_quotes"
            }
            for r in rows
        ]
    finally:
        conn.close()

# 3. Finance Domain Operations (Finance Agent)
def get_finance_budget_status() -> Dict[str, Any]:
    """Retrieves current fiscal budget records from database."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT fiscal_period, total_budget, spent_budget, hard_limit, currency FROM finance_budgets LIMIT 1")
        row = cur.fetchone()
        if row:
            total = row[1]
            spent = row[2]
            hard_limit = row[3]
            return {
                "fiscal_period": row[0],
                "total_budget": total,
                "spent_budget": spent,
                "available_budget": max(0, total - spent),
                "hard_limit": hard_limit,
                "currency": row[4],
                "data_source": f"{engine}::finance_budgets"
            }
        return {
            "fiscal_period": "FY-2026-Q4",
            "total_budget": 100000,
            "spent_budget": 0,
            "available_budget": 100000,
            "hard_limit": 100000,
            "currency": "INR",
            "data_source": "default_policy"
        }
    finally:
        conn.close()

def record_budget_expenditure(amount: int):
    """Records spending against the fiscal budget."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(f"UPDATE finance_budgets SET spent_budget = spent_budget + {param}", (amount,))
        conn.commit()
    finally:
        conn.close()

# 4. Procurement & Orders Domain Operations (Execution Agent)
def insert_purchase_order(po_id: str, thread_id: str, supplier: str, product: str, quantity: int, unit_price: int, total_cost: int, status: str = "CREATED") -> Dict[str, Any]:
    """Persists an authorized purchase order into the database."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(
            f"""
            INSERT INTO purchase_orders (po_id, thread_id, supplier, product, quantity, unit_price, total_cost, currency, status, approved_by)
            VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, 'INR', {param}, 'Human Supervisor')
            """,
            (po_id, thread_id, supplier, product, quantity, unit_price, total_cost, status)
        )
        conn.commit()
        return {
            "po_id": po_id,
            "thread_id": thread_id,
            "supplier": supplier,
            "product": product,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_cost": total_cost,
            "currency": "INR",
            "status": status,
            "data_source": f"{engine}::purchase_orders",
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    finally:
        conn.close()

def get_purchase_order_by_id(po_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a purchase order by PO reference."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(f"SELECT po_id, thread_id, supplier, product, quantity, unit_price, total_cost, currency, status, approved_by, created_at FROM purchase_orders WHERE po_id = {param}", (po_id.strip(),))
        row = cur.fetchone()
        if row:
            return {
                "po_id": row[0],
                "thread_id": row[1],
                "supplier": row[2],
                "product": row[3],
                "quantity": row[4],
                "unit_price": row[5],
                "total_cost": row[6],
                "currency": row[7],
                "status": row[8],
                "approved_by": row[9],
                "created_at": str(row[10]),
                "data_source": f"{engine}::purchase_orders"
            }
        return None
    finally:
        conn.close()

def list_recent_purchase_orders(limit: int = 10) -> List[Dict[str, Any]]:
    """Lists recent purchase orders from database."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(f"SELECT po_id, thread_id, supplier, product, quantity, unit_price, total_cost, currency, status, approved_by, created_at FROM purchase_orders ORDER BY id DESC LIMIT {param}", (limit,))
        rows = cur.fetchall()
        return [
            {
                "po_id": r[0],
                "thread_id": r[1],
                "supplier": r[2],
                "product": r[3],
                "quantity": r[4],
                "unit_price": r[5],
                "total_cost": r[6],
                "currency": r[7],
                "status": r[8],
                "approved_by": r[9],
                "created_at": str(r[10]),
                "data_source": f"{engine}::purchase_orders"
            }
            for r in rows
        ]
    finally:
        conn.close()

# 5. Audit Domain Operations (Audit Agent)
def insert_audit_entry(thread_id: str, agent_name: str, status: str, llm_mode: str, decision: str):
    """Records an audit log entry in the audit database."""
    conn, engine = get_connection()
    try:
        cur = conn.cursor()
        param = "%s" if engine == "POSTGRES" else "?"
        cur.execute(
            f"INSERT INTO audit_logs (thread_id, agent_name, status, llm_mode, decision) VALUES ({param}, {param}, {param}, {param}, {param})",
            (thread_id, agent_name, status, llm_mode, decision)
        )
        conn.commit()
    finally:
        conn.close()
