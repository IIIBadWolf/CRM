# logic_products.py
import re
from db import add_my_product, get_all_products, update_my_product, get_connection
import pandas as pd

def ensure_code_column():
    # схема уже содержит столбец code
    return

def normalize_name(s: str) -> str:
    if s is None:
        return ""
    s = str(s).lower()
    s = re.sub(r'[^0-9a-zа-яё\.,\-]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def import_products_from_df(df: pd.DataFrame, replace_all: bool = False):
    """
    df: columns 'code', 'name'
    Behavior:
      - if code exists in DB => update code field (do not change my_name)
      - if code missing, attempt match by normalized name -> update code if empty (do not change my_name)
      - else create new product with name+code
    """
    existing = get_all_products()
    existing_by_code = { (r['code'] or '').strip(): r for r in existing if r['code']}
    existing_by_name = { normalize_name(r['my_name']): r for r in existing}
    added = updated = 0
    for _, row in df.iterrows():
        code = str(row.get('code','')).strip()
        name = str(row.get('name','')).strip()
        if code and code in existing_by_code:
            pid = existing_by_code[code]['id']
            update_my_product(pid, code=code)
            updated += 1
        else:
            nname = normalize_name(name)
            if nname in existing_by_name:
                pid = existing_by_name[nname]['id']
                if code:
                    update_my_product(pid, code=code)
                updated += 1
            else:
                add_my_product(name, code=code)
                added += 1
    return {'added': added, 'updated': updated, 'deduped': 0}

def dedupe_my_products_by_code_and_name():
    """
    Удаляем дубли: оставляем запись с наименьшим id.
    Переназначаем mappings.
    Возвращаем отчёт.
    """
    conn = get_connection()
    cur = conn.cursor()
    report = {'removed':0, 'reassigned':0}
    # дубли по коду
    cur.execute("SELECT code, COUNT(*) as cnt FROM my_products WHERE code IS NOT NULL AND code <> '' GROUP BY code HAVING cnt>1")
    for row in cur.fetchall():
        code = row['code']
        cur.execute("SELECT id FROM my_products WHERE code = ? ORDER BY id ASC", (code,))
        ids = [r['id'] for r in cur.fetchall()]
        keep = ids[0]; remove = ids[1:]
        for rid in remove:
            cur.execute("UPDATE product_mappings SET my_product_id = ? WHERE my_product_id = ?", (keep, rid))
            cur.execute("DELETE FROM my_products WHERE id = ?", (rid,))
            report['removed'] += 1
            report['reassigned'] += 1
    # дубли по нормализованному имени (без кода)
    cur.execute("SELECT id, my_name FROM my_products WHERE code IS NULL OR code = '' ORDER BY id ASC")
    rows = cur.fetchall()
    name_map = {}
    for r in rows:
        nid = r['id']; nm = normalize_name(r['my_name'])
        if nm in name_map:
            keep = name_map[nm]
            cur.execute("UPDATE product_mappings SET my_product_id = ? WHERE my_product_id = ?", (keep, nid))
            cur.execute("DELETE FROM my_products WHERE id = ?", (nid,))
            report['removed'] += 1; report['reassigned'] += 1
        else:
            name_map[nm] = nid
    conn.commit(); conn.close()
    return report
