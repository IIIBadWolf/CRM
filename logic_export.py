# logic_export.py
import pandas as pd
from db import get_product_mapping, get_all_products

def build_final_table(proc_df, supplier_id, product_mapping_fn, products_fn):
    """
    proc_df: dataframe with columns 'name','qty','price','sum' (internal)
    Returns df_final (Код, Наименование, Количество, Закупочная цена), price_updates list (my_id, avg_price)
    """
    df = proc_df.copy()
    df['name'] = df.get('name', '')
    rows = []
    for _, r in df.iterrows():
        sname = str(r.get('name','')).strip()
        qty = float(r.get('qty', 0) or 0)
        price = float(r.get('price', 0) or 0)
        my_id = product_mapping_fn(supplier_id, sname)
        rows.append({'supplier_name': sname, 'qty': qty, 'price': price, 'my_id': my_id})
    agg = {}
    for r in rows:
        key = r['my_id'] if r['my_id'] is not None else ('__unmapped__:'+r['supplier_name'])
        rec = agg.get(key, {'qty':0.0, 'cost':0.0, 'names':[]})
        rec['qty'] += r['qty']
        rec['cost'] += r['qty'] * r['price']
        rec['names'].append(r['supplier_name'])
        agg[key] = rec
    products = {p['id']: p for p in products_fn()}
    final_rows = []
    price_updates = []
    for key, rec in agg.items():
        if isinstance(key, int):
            my_id = key
            p = products.get(my_id)
            name = p['my_name'] if p else ''
            code = p['code'] if p and 'code' in p.keys() else ''
        else:
            my_id = None
            name = rec['names'][0] if rec['names'] else ''
            code = ''
        total_qty = rec['qty']
        avg_price = (rec['cost'] / total_qty) if total_qty > 0 else 0.0
        avg_price = round(avg_price, 2)
        if my_id is not None:
            price_updates.append((my_id, avg_price))
        final_rows.append({'Код': code, 'Наименование': name if name else key, 'Количество': total_qty, 'Закупочная цена': avg_price})
    out_df = pd.DataFrame(final_rows)
    return out_df, price_updates

def save_to_excel(df, path):
    df.to_excel(path, index=False)
