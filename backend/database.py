import json
import os
import sqlite3
from datetime import datetime
from typing import Any


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SQLITE_DB_PATH = os.getenv(
    "SQLITE_DB_PATH",
    os.path.join(os.path.dirname(__file__), "price_comparator.db"),
)
IS_POSTGRES = bool(DATABASE_URL and not DATABASE_URL.startswith("sqlite"))
PLACEHOLDER = "%s" if IS_POSTGRES else "?"


def _postgres_url() -> str:
    if DATABASE_URL.startswith("postgres://"):
        return DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return DATABASE_URL


def get_connection():
    if IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(_postgres_url(), row_factory=dict_row)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _row_to_dict(row: Any) -> dict | None:
    if row is None:
        return None
    return dict(row)


def _decode_json_fields(row: dict | None, fields: tuple[str, ...]) -> dict | None:
    if not row:
        return row
    for field in fields:
        if row.get(field) and isinstance(row[field], str):
            row[field] = json.loads(row[field])
    return row


def _json(value: Any) -> str | None:
    return json.dumps(value, ensure_ascii=False) if value is not None else None


def _bool(value: Any) -> bool | int:
    return bool(value) if IS_POSTGRES else int(bool(value))


def _execute_many(cursor, sql: str, rows: list[tuple]):
    if rows:
        cursor.executemany(sql, rows)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if IS_POSTGRES:
        statements = [
            """
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
                price DOUBLE PRECISION,
                old_price DOUBLE PRECISION,
                currency TEXT DEFAULT '$',
                price_raw TEXT,
                rating DOUBLE PRECISION,
                reviews_count INTEGER,
                tag TEXT,
                delivery TEXT,
                snippet TEXT,
                scraped_at TEXT,
                raw TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL,
                product_data TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                target_price DOUBLE PRECISION NOT NULL,
                condition TEXT NOT NULL DEFAULT 'below',
                current_price DOUBLE PRECISION DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_name TEXT,
                price DOUBLE PRECISION NOT NULL,
                recorded_at TEXT DEFAULT (NOW()::TEXT)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                search_query TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                dataset_name TEXT,
                dataset_source TEXT,
                model_type TEXT NOT NULL,
                random_seed INTEGER,
                hyperparameters TEXT,
                rmse DOUBLE PRECISION,
                mae DOUBLE PRECISION,
                mape DOUBLE PRECISION,
                r2 DOUBLE PRECISION,
                loss DOUBLE PRECISION,
                training_time DOUBLE PRECISION,
                model_path TEXT,
                history_path TEXT,
                scaler_path TEXT,
                metadata_path TEXT,
                report_html_path TEXT,
                report_pdf_path TEXT,
                is_best BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS best_models (
                id SERIAL PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                rmse DOUBLE PRECISION NOT NULL,
                mae DOUBLE PRECISION NOT NULL,
                mape DOUBLE PRECISION,
                r2 DOUBLE PRECISION NOT NULL,
                validation_status TEXT DEFAULT 'pending',
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_products_created_at ON products (created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products (name)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history (product_id, recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (is_active)",
        ]
    else:
        statements = [
            """
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
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                product_data TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """,
            """
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
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                store_name TEXT,
                price REAL NOT NULL,
                recorded_at TEXT DEFAULT (datetime('now'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_query TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                created_at TEXT DEFAULT (datetime('now')),
                dataset_name TEXT,
                dataset_source TEXT,
                model_type TEXT NOT NULL,
                random_seed INTEGER,
                hyperparameters TEXT,
                rmse REAL,
                mae REAL,
                mape REAL,
                r2 REAL,
                loss REAL,
                training_time REAL,
                model_path TEXT,
                history_path TEXT,
                scaler_path TEXT,
                metadata_path TEXT,
                report_html_path TEXT,
                report_pdf_path TEXT,
                is_best INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS best_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                rmse REAL NOT NULL,
                mae REAL NOT NULL,
                mape REAL,
                r2 REAL NOT NULL,
                validation_status TEXT DEFAULT 'pending',
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_products_created_at ON products (created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products (name)",
            "CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history (product_id, recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts (is_active)",
        ]

    for statement in statements:
        cursor.execute(statement)

    conn.commit()
    conn.close()


# --- Products & Favorites ---
def save_products(products: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()

    columns = (
        "id, name, canonical_name, image, description, category, brand, "
        "product_link, source_name, price, old_price, currency, price_raw, "
        "rating, reviews_count, tag, delivery, snippet, scraped_at, raw"
    )
    values_sql = ", ".join([PLACEHOLDER] * 20)

    if IS_POSTGRES:
        product_sql = f"""
            INSERT INTO products ({columns})
            VALUES ({values_sql})
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                canonical_name = EXCLUDED.canonical_name,
                image = EXCLUDED.image,
                description = EXCLUDED.description,
                category = EXCLUDED.category,
                brand = EXCLUDED.brand,
                product_link = EXCLUDED.product_link,
                source_name = EXCLUDED.source_name,
                price = EXCLUDED.price,
                old_price = EXCLUDED.old_price,
                currency = EXCLUDED.currency,
                price_raw = EXCLUDED.price_raw,
                rating = EXCLUDED.rating,
                reviews_count = EXCLUDED.reviews_count,
                tag = EXCLUDED.tag,
                delivery = EXCLUDED.delivery,
                snippet = EXCLUDED.snippet,
                scraped_at = EXCLUDED.scraped_at,
                raw = EXCLUDED.raw
        """
    else:
        product_sql = f"""
            INSERT OR REPLACE INTO products ({columns})
            VALUES ({values_sql})
        """

    history_sql = f"""
        INSERT INTO price_history (product_id, store_name, price, recorded_at)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
    """

    product_rows = []
    history_rows = []
    for product in products:
        raw_json = _json(product.get("raw"))
        product_rows.append((
            product.get("id"),
            product.get("name"),
            product.get("canonical_name"),
            product.get("image"),
            product.get("description"),
            product.get("category"),
            product.get("brand"),
            product.get("product_link"),
            product.get("source_name"),
            product.get("price"),
            product.get("old_price"),
            product.get("currency", "$"),
            product.get("price_raw"),
            product.get("rating"),
            product.get("reviews_count"),
            product.get("tag"),
            product.get("delivery"),
            product.get("snippet"),
            product.get("scraped_at"),
            raw_json,
        ))

        if product.get("price"):
            history_rows.append((
                product.get("id"),
                product.get("source_name"),
                product.get("price"),
                product.get("scraped_at", datetime.now().isoformat()),
            ))

    _execute_many(cursor, product_sql, product_rows)
    _execute_many(cursor, history_sql, history_rows)
    conn.commit()
    conn.close()


def get_product(product_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        f"SELECT * FROM products WHERE id = {PLACEHOLDER}",
        (product_id,),
    ).fetchone()
    conn.close()
    return _decode_json_fields(_row_to_dict(row), ("raw",))


def get_products(filters: dict | None = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM products WHERE 1=1"
    params: list = []

    if filters:
        if filters.get("category"):
            query += f" AND category = {PLACEHOLDER}"
            params.append(filters["category"])
        if filters.get("brand"):
            query += f" AND brand = {PLACEHOLDER}"
            params.append(filters["brand"])
        if filters.get("minPrice") is not None:
            query += f" AND price >= {PLACEHOLDER}"
            params.append(filters["minPrice"])
        if filters.get("maxPrice") is not None:
            query += f" AND price <= {PLACEHOLDER}"
            params.append(filters["maxPrice"])

    query += " ORDER BY created_at DESC LIMIT 100"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [
        _decode_json_fields(_row_to_dict(row), ("raw",))
        for row in rows
    ]


def search_products_db(query: str) -> list[dict]:
    conn = get_connection()
    like_operator = "ILIKE" if IS_POSTGRES else "LIKE"
    rows = conn.execute(
        f"""
        SELECT *
        FROM products
        WHERE name {like_operator} {PLACEHOLDER}
           OR canonical_name {like_operator} {PLACEHOLDER}
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (f"%{query}%", f"%{query}%"),
    ).fetchall()
    conn.close()
    return [
        _decode_json_fields(_row_to_dict(row), ("raw",))
        for row in rows
    ]


def get_favorites() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM favorites ORDER BY created_at DESC").fetchall()
    conn.close()
    return [
        _decode_json_fields(_row_to_dict(row), ("product_data",))
        for row in rows
    ]


def add_favorite(product_id: str, product_data: dict) -> dict:
    conn = get_connection()
    if IS_POSTGRES:
        row = conn.execute(
            f"""
            INSERT INTO favorites (product_id, product_data)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER})
            RETURNING *
            """,
            (product_id, _json(product_data)),
        ).fetchone()
        conn.commit()
        conn.close()
        return _decode_json_fields(_row_to_dict(row), ("product_data",))

    cursor = conn.execute(
        f"INSERT INTO favorites (product_id, product_data) VALUES ({PLACEHOLDER}, {PLACEHOLDER})",
        (product_id, _json(product_data)),
    )
    fav_id = cursor.lastrowid
    conn.commit()
    row = conn.execute(
        f"SELECT * FROM favorites WHERE id = {PLACEHOLDER}",
        (fav_id,),
    ).fetchone()
    conn.close()
    return _decode_json_fields(_row_to_dict(row), ("product_data",))


def remove_favorite(product_id: str):
    conn = get_connection()
    conn.execute(
        f"DELETE FROM favorites WHERE product_id = {PLACEHOLDER}",
        (product_id,),
    )
    conn.commit()
    conn.close()


def count_favorites() -> int:
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM favorites").fetchone()
    conn.close()
    return int(_row_to_dict(row)["cnt"])


# --- Alerts ---
def get_alerts() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC").fetchall()
    conn.close()
    results = []
    for row in rows:
        item = _row_to_dict(row)
        item["is_active"] = bool(item["is_active"])
        results.append(item)
    return results


def add_alert(alert_data: dict) -> dict:
    conn = get_connection()
    values = (
        alert_data.get("product_id"),
        alert_data.get("product_name"),
        alert_data.get("target_price"),
        alert_data.get("condition", "below"),
        alert_data.get("current_price", 0),
        _bool(alert_data.get("is_active", True)),
    )

    if IS_POSTGRES:
        row = conn.execute(
            f"""
            INSERT INTO alerts (product_id, product_name, target_price, condition, current_price, is_active)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
            RETURNING *
            """,
            values,
        ).fetchone()
        conn.commit()
        conn.close()
    else:
        cursor = conn.execute(
            f"""
            INSERT INTO alerts (product_id, product_name, target_price, condition, current_price, is_active)
            VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
            """,
            values,
        )
        alert_id = cursor.lastrowid
        conn.commit()
        row = conn.execute(
            f"SELECT * FROM alerts WHERE id = {PLACEHOLDER}",
            (alert_id,),
        ).fetchone()
        conn.close()

    item = _row_to_dict(row)
    item["is_active"] = bool(item["is_active"])
    return item


def update_alert(alert_id: int, updates: dict) -> dict | None:
    conn = get_connection()
    set_clauses = []
    params = []

    if "is_active" in updates:
        set_clauses.append(f"is_active = {PLACEHOLDER}")
        params.append(_bool(updates["is_active"]))
    if "target_price" in updates:
        set_clauses.append(f"target_price = {PLACEHOLDER}")
        params.append(updates["target_price"])
    if "condition" in updates:
        set_clauses.append(f"condition = {PLACEHOLDER}")
        params.append(updates["condition"])

    set_clauses.append(f"updated_at = {PLACEHOLDER}")
    params.append(datetime.now().isoformat())
    params.append(alert_id)

    conn.execute(
        f"UPDATE alerts SET {', '.join(set_clauses)} WHERE id = {PLACEHOLDER}",
        params,
    )
    conn.commit()
    row = conn.execute(
        f"SELECT * FROM alerts WHERE id = {PLACEHOLDER}",
        (alert_id,),
    ).fetchone()
    conn.close()

    item = _row_to_dict(row)
    if item:
        item["is_active"] = bool(item["is_active"])
    return item


def delete_alert(alert_id: int):
    conn = get_connection()
    conn.execute(
        f"DELETE FROM alerts WHERE id = {PLACEHOLDER}",
        (alert_id,),
    )
    conn.commit()
    conn.close()


def count_alerts() -> tuple[int, int]:
    conn = get_connection()
    total = _row_to_dict(conn.execute("SELECT COUNT(*) as cnt FROM alerts").fetchone())["cnt"]
    active_filter = "is_active = TRUE" if IS_POSTGRES else "is_active = 1"
    active = _row_to_dict(
        conn.execute(f"SELECT COUNT(*) as cnt FROM alerts WHERE {active_filter}").fetchone()
    )["cnt"]
    conn.close()
    return int(total), int(active)


# --- Price History ---
def get_price_history(product_id: str) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        f"""
        SELECT *
        FROM price_history
        WHERE product_id = {PLACEHOLDER}
        ORDER BY recorded_at ASC
        """,
        (product_id,),
    ).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def save_search(query: str, result_count: int):
    conn = get_connection()
    conn.execute(
        f"INSERT INTO search_history (search_query, result_count) VALUES ({PLACEHOLDER}, {PLACEHOLDER})",
        (query, result_count),
    )
    conn.commit()
    conn.close()


# --- Experiments & Best Models ---
def save_experiment(experiment: dict) -> str:
    import uuid
    experiment_id = str(uuid.uuid4())
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        INSERT INTO experiments
        (id, created_at, dataset_name, dataset_source, model_type, random_seed,
         hyperparameters, rmse, mae, mape, r2, loss, training_time,
         model_path, history_path, scaler_path, metadata_path, report_html_path, report_pdf_path, is_best)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER},
                {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER},
                {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER},
                {PLACEHOLDER}, {PLACEHOLDER})
        """,
        (
            experiment_id,
            experiment.get("created_at", datetime.now().isoformat()),
            experiment.get("dataset_name"),
            experiment.get("dataset_source"),
            experiment.get("model_type"),
            experiment.get("random_seed"),
            _json(experiment.get("hyperparameters")),
            experiment.get("rmse"),
            experiment.get("mae"),
            experiment.get("mape"),
            experiment.get("r2"),
            experiment.get("loss"),
            experiment.get("training_time"),
            experiment.get("model_path"),
            experiment.get("history_path"),
            experiment.get("scaler_path"),
            experiment.get("metadata_path"),
            experiment.get("report_html_path"),
            experiment.get("report_pdf_path"),
            _bool(experiment.get("is_best", False)),
        ),
    )

    conn.commit()
    conn.close()
    return experiment_id


def get_experiments() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
    rows = cursor.fetchall()

    experiments = []
    for row in rows:
        exp = _row_to_dict(row)
        if exp:
            exp = _decode_json_fields(exp, ("hyperparameters",))
            if "is_best" in exp:
                exp["is_best"] = bool(exp["is_best"])
            experiments.append(exp)

    conn.close()
    return experiments


def get_experiment(experiment_id: str) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM experiments WHERE id = {PLACEHOLDER}", (experiment_id,))
    row = cursor.fetchone()

    if row:
        exp = _row_to_dict(row)
        exp = _decode_json_fields(exp, ("hyperparameters",))
        if "is_best" in exp:
            exp["is_best"] = bool(exp["is_best"])
        conn.close()
        return exp
    conn.close()
    return None


def get_best_model() -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT bm.*, e.* FROM best_models bm
        JOIN experiments e ON bm.experiment_id = e.id
        ORDER BY bm.created_at DESC
        LIMIT 1
        """
    )
    row = cursor.fetchone()

    if row:
        model = _row_to_dict(row)
        model = _decode_json_fields(model, ("hyperparameters",))
        if "is_best" in model:
            model["is_best"] = bool(model["is_best"])
        conn.close()
        return model
    conn.close()
    return None


def save_best_model(experiment_id: str, model_data: dict) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # Reset all other best model flags
    cursor.execute(f"UPDATE experiments SET is_best = {PLACEHOLDER}", (_bool(False),))

    # Mark current experiment as best
    cursor.execute(
        f"UPDATE experiments SET is_best = {PLACEHOLDER} WHERE id = {PLACEHOLDER}",
        (_bool(True), experiment_id),
    )

    # Insert into best_models
    cursor.execute(
        f"""
        INSERT INTO best_models
        (experiment_id, model_name, model_type, rmse, mae, mape, r2, validation_status)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        """,
        (
            experiment_id,
            model_data.get("model_name"),
            model_data.get("model_type"),
            model_data.get("rmse"),
            model_data.get("mae"),
            model_data.get("mape"),
            model_data.get("r2"),
            model_data.get("validation_status", "pending"),
        ),
    )

    conn.commit()
    conn.close()


def get_best_models_history() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT bm.*, e.model_type, e.created_at as exp_created_at, e.rmse, e.mae, e.r2
        FROM best_models bm
        JOIN experiments e ON bm.experiment_id = e.id
        ORDER BY bm.created_at DESC
        """
    )

    rows = cursor.fetchall()
    history = []
    for i, row in enumerate(rows):
        item = _row_to_dict(row)
        if item:
            # Assign version (v1.0, v0.9, etc.)
            item["version"] = f"v{len(rows)-i:.1f}"
            # Status: first is "Activo", others "Archivado"
            item["status"] = "Activo" if i == 0 else "Archivado"
            history.append(item)

    conn.close()
    return history
