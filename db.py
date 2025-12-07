# db.py
import sqlite3
from pathlib import Path
import shutil
from datetime import datetime
import logging

BASE = Path(__file__).parent
DB_PATH = BASE / "database.db"
BACKUP_DIR = BASE / "backup"
LOG_DIR = BASE / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(filename=str(LOG_DIR/"app.log"), level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

def rotate_backups():
    """Ротация бэкапов: сохраняем копии database.db и оставляем максимум 3."""
    try:
        BACKUP_DIR.mkdir(exist_ok=True)
        if DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest = BACKUP_DIR / f"db_{timestamp}.sqlite"
            shutil.copy2(DB_PATH, dest)
            # удалить старые, оставить 3 последние
            files = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[3:]:
                try:
                    f.unlink()
                except Exception:
                    logging.exception("Не удалось удалить старый бэкап %s", f)
    except Exception:
        logging.exception("rotate_backups failed")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # my_products
    cur.execute("""
        CREATE TABLE IF NOT EXISTS my_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            my_name TEXT NOT NULL,
            code TEXT,
            category TEXT,
            last_price REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # suppliers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            pattern TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # supplier_mappings (columns)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            file_column TEXT NOT NULL,
            logical_column TEXT NOT NULL,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    # supplier_file_history
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_file_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            filename TEXT,
            columns_text TEXT,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
    """)

    # product_mappings (supplier_name -> my_product_id)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS product_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            supplier_name TEXT,
            my_product_id INTEGER,
            UNIQUE(supplier_id, supplier_name)
        )
    """)

    # price_history
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            price REAL NOT NULL,
            FOREIGN KEY(product_id) REFERENCES my_products(id)
        )
    """)

    conn.commit()
    conn.close()

# -------------------------
# my_products helpers
# -------------------------
def add_my_product(name, category="", code=None, last_price=None):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO my_products (my_name, category, code, last_price) VALUES (?, ?, ?, ?)",
                (name, category, code, last_price))
    conn.commit(); conn.close()
    logging.info("Добавлен товар: %s (code=%s)", name, code)

def update_my_product(pid, name=None, code=None, last_price=None):
    conn = get_connection(); cur = conn.cursor()
    if name is not None:
        cur.execute("UPDATE my_products SET my_name = ? WHERE id = ?", (name, pid))
    if code is not None:
        cur.execute("UPDATE my_products SET code = ? WHERE id = ?", (code, pid))
    if last_price is not None:
        cur.execute("UPDATE my_products SET last_price = ? WHERE id = ?", (last_price, pid))
    conn.commit(); conn.close()
    logging.info("Обновлён товар id=%s name=%s code=%s price=%s", pid, name, code, last_price)

def delete_my_product(product_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM my_products WHERE id = ?", (product_id,))
    conn.commit(); conn.close()
    logging.info("Удалён товар id=%s", product_id)

def get_all_products():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM my_products ORDER BY my_name ASC")
    rows = cur.fetchall(); conn.close()
    return rows

# -------------------------
# suppliers helpers
# -------------------------
def add_supplier(name, pattern=None):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO suppliers (name, pattern) VALUES (?, ?)", (name, pattern))
    conn.commit(); sid = cur.lastrowid; conn.close()
    logging.info("Добавлен поставщик: %s (id=%s)", name, sid)
    return sid

def get_suppliers():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers ORDER BY name")
    rows = cur.fetchall(); conn.close()
    return rows

def get_supplier(supplier_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    row = cur.fetchone(); conn.close()
    return row

def rename_supplier(supplier_id, new_name):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("UPDATE suppliers SET name = ? WHERE id = ?", (new_name, supplier_id))
    conn.commit(); conn.close()
    logging.info("Поставщик %s переименован в %s", supplier_id, new_name)

def delete_supplier(supplier_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    conn.commit(); conn.close()
    logging.info("Поставщик %s удалён", supplier_id)

# -------------------------
# supplier_mappings (columns)
# -------------------------
def save_mapping(supplier_id, file_column, logical_column):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT id FROM supplier_mappings WHERE supplier_id = ? AND file_column = ?", (supplier_id, file_column))
    if cur.fetchone():
        cur.execute("UPDATE supplier_mappings SET logical_column = ? WHERE supplier_id = ? AND file_column = ?",
                    (logical_column, supplier_id, file_column))
    else:
        cur.execute("INSERT INTO supplier_mappings (supplier_id, file_column, logical_column) VALUES (?, ?, ?)",
                    (supplier_id, file_column, logical_column))
    conn.commit(); conn.close()
    logging.info("Сохранён mapping: supplier=%s, file_col=%s -> %s", supplier_id, file_column, logical_column)

def get_mappings_for_supplier(supplier_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT file_column, logical_column FROM supplier_mappings WHERE supplier_id = ?", (supplier_id,))
    rows = cur.fetchall(); conn.close()
    return {r["file_column"]: r["logical_column"] for r in rows}

def add_supplier_file_history(supplier_id, filename, columns):
    conn = get_connection(); cur = conn.cursor()
    cols_text = "||".join(columns)
    cur.execute("INSERT INTO supplier_file_history (supplier_id, filename, columns_text) VALUES (?, ?, ?)",
                (supplier_id, filename, cols_text))
    conn.commit(); conn.close()
    logging.info("Добавлена запись истории файла поставщика %s -> %s", supplier_id, filename)

# -------------------------
# product mappings (supplier_name -> my_product_id)
# -------------------------
def get_product_mapping(supplier_id, supplier_name):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT my_product_id FROM product_mappings WHERE supplier_id = ? AND supplier_name = ?", (supplier_id, supplier_name))
    row = cur.fetchone(); conn.close()
    return row["my_product_id"] if row else None

def save_product_mapping(supplier_id, supplier_name, my_product_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO product_mappings (supplier_id, supplier_name, my_product_id) VALUES (?, ?, ?) "
                "ON CONFLICT(supplier_id, supplier_name) DO UPDATE SET my_product_id = excluded.my_product_id",
                (supplier_id, supplier_name, my_product_id))
    conn.commit(); conn.close()
    logging.info("Сохранено сопоставление %s -> %s (supplier %s)", supplier_name, my_product_id, supplier_id)

def get_all_product_mappings_for_supplier(supplier_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT supplier_name, my_product_id FROM product_mappings WHERE supplier_id = ? ORDER BY supplier_name", (supplier_id,))
    rows = cur.fetchall(); conn.close()
    return {r["supplier_name"]: r["my_product_id"] for r in rows}

# -------------------------
# price history
# -------------------------
def add_price_history(product_id, price, date=None):
    conn = get_connection(); cur = conn.cursor()
    if date:
        cur.execute("INSERT INTO price_history (product_id, date, price) VALUES (?, ?, ?)", (product_id, date, price))
    else:
        cur.execute("INSERT INTO price_history (product_id, price) VALUES (?, ?)", (product_id, price))
    conn.commit(); conn.close()
    logging.info("Добавлена запись цены product_id=%s price=%s", product_id, price)

def get_price_history_for_product(product_id):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT date, price FROM price_history WHERE product_id = ? ORDER BY date DESC", (product_id,))
    rows = cur.fetchall(); conn.close()
    return [dict(r) for r in rows]
