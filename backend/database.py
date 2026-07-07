import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "price_comparator.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            canonical_name TEXT,
            image TEXT,
            description TEXT,
            category TEXT,
            brand TEXT,
            product_link TEXT,
            source_name TEXT,
            price REAL,
            old_price REAL,
            currency TEXT DEFAULT '$',
            price_raw TEXT,
            rating REAL,
            reviews_count INTEGER,
            tag TEXT,
            delivery TEXT,
            snippet TEXT,
            scraped_at TEXT,
            raw TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            product_data TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            target_price REAL NOT NULL,
            condition TEXT NOT NULL DEFAULT 'below',
            current_price REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            store_name TEXT,
            price REAL NOT NULL,
            recorded_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_query TEXT NOT NULL,
            result_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()


# --- Products ---

def save_products(products: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for p in products:
        raw_json = json.dumps(p.get("raw")) if p.get("raw") else None
        cursor.execute("""
            INSERT OR REPLACE INTO products
            (id, name, canonical_name, image, description, category, brand,
             product_link, source_name, price, old_price, currency, price_raw,
             rating, reviews_count, tag, delivery, snippet, scraped_at, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p.get("id"), p.get("name"), p.get("canonical_name"),
            p.get("image"), p.get("description"), p.get("category"),
            p.get("brand"), p.get("product_link"), p.get("source_name"),
            p.get("price"), p.get("old_price"), p.get("currency", "$"),
            p.get("price_raw"), p.get("rating"), p.get("reviews_count"),
            p.get("tag"), p.get("delivery"), p.get("snippet"),
            p.get("scraped_at"), raw_json,
        ))

        # Save to price history
        if p.get("price"):
            cursor.execute("""
                INSERT INTO price_history (product_id, store_name, price, recorded_at)
                VALUES (?, ?, ?, ?)
            """, (
                p.get("id"), p.get("source_name"), p.get("price"),
                p.get("scraped_at", datetime.now().isoformat()),
            ))

    conn.commit()
    conn.close()


def get_product(product_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("raw"):
            d["raw"] = json.loads(d["raw"])
        return d
    return None


def get_products(filters: dict | None = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM products WHERE 1=1"
    params: list = []

    if filters:
        if filters.get("category"):
            query += " AND category = ?"
            params.append(filters["category"])
        if filters.get("brand"):
            query += " AND brand = ?"
            params.append(filters["brand"])
        if filters.get("minPrice") is not None:
            query += " AND price >= ?"
            params.append(filters["minPrice"])
        if filters.get("maxPrice") is not None:
            query += " AND price <= ?"
            params.append(filters["maxPrice"])

    query += " ORDER BY created_at DESC LIMIT 100"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("raw"):
            d["raw"] = json.loads(d["raw"])
        results.append(d)
    return results


def search_products_db(query: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? OR canonical_name LIKE ? ORDER BY created_at DESC LIMIT 5",
        (f"%{query}%", f"%{query}%"),
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("raw"):
            d["raw"] = json.loads(d["raw"])
        results.append(d)
    return results


# --- Favorites ---

def get_favorites() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM favorites ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    results = []
    for row in rows:
        d = dict(row)
        if d.get("product_data"):
            d["product_data"] = json.loads(d["product_data"])
        results.append(d)
    return results


def add_favorite(product_id: str, product_data: dict) -> dict:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO favorites (product_id, product_data) VALUES (?, ?)",
        (product_id, json.dumps(product_data)),
    )
    fav_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM favorites WHERE id = ?", (fav_id,)).fetchone()
    conn.close()
    d = dict(row)
    if d.get("product_data"):
        d["product_data"] = json.loads(d["product_data"])
    return d


def remove_favorite(product_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM favorites WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()


def count_favorites() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM favorites").fetchone()
    conn.close()
    return row["cnt"]


# --- Alerts ---

def get_alerts() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_alert(alert_data: dict) -> dict:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO alerts (product_id, product_name, target_price, condition, current_price, is_active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            alert_data.get("product_id"),
            alert_data.get("product_name"),
            alert_data.get("target_price"),
            alert_data.get("condition", "below"),
            alert_data.get("current_price", 0),
            1 if alert_data.get("is_active", True) else 0,
        ),
    )
    alert_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    conn.close()
    d = dict(row)
    d["is_active"] = bool(d["is_active"])
    return d


def update_alert(alert_id: int, updates: dict) -> dict | None:
    conn = get_connection()
    set_clauses = []
    params = []

    if "is_active" in updates:
        set_clauses.append("is_active = ?")
        params.append(1 if updates["is_active"] else 0)
    if "target_price" in updates:
        set_clauses.append("target_price = ?")
        params.append(updates["target_price"])
    if "condition" in updates:
        set_clauses.append("condition = ?")
        params.append(updates["condition"])

    set_clauses.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(alert_id)

    conn.execute(
        f"UPDATE alerts SET {', '.join(set_clauses)} WHERE id = ?",
        params,
    )
    conn.commit()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["is_active"] = bool(d["is_active"])
        return d
    return None


def delete_alert(alert_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


def count_alerts() -> tuple[int, int]:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone()["cnt"]
    active = conn.execute(
        "SELECT COUNT(*) as cnt FROM alerts WHERE is_active = 1"
    ).fetchone()["cnt"]
    conn.close()
    return total, active


# --- Price History ---

def get_price_history(product_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM price_history WHERE product_id = ? ORDER BY recorded_at ASC",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Search History ---

def save_search(query: str, result_count: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO search_history (search_query, result_count) VALUES (?, ?)",
        (query, result_count),
    )
    conn.commit()
    conn.close()
