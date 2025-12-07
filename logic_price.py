# logic_price.py
from db import add_price_history, get_price_history_for_product

def record_price_if_changed(product_id, new_price):
    history = get_price_history_for_product(product_id)
    last_price = history[0]['price'] if history else None
    if last_price is None or float(new_price) != float(last_price):
        add_price_history(product_id, new_price)
