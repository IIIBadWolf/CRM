# ui_main.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QLineEdit, QFileDialog, QMessageBox, QListWidgetItem, QTableView
from PySide6.QtCore import Qt
from pathlib import Path
import pandas as pd
from styles import BASE_STYLE
from db import get_all_products, add_supplier, get_suppliers, get_product_mapping, save_product_mapping, add_supplier_file_history, get_connection, init_db
from logic_products import ensure_code_column, import_products_from_df, dedupe_my_products_by_code_and_name
from logic_import import read_supplier_file, map_columns_by_keywords, clean_supplier_df
from logic_export import build_final_table, save_to_excel
from logic_price import record_price_if_changed
from ui_matcher import ProductMatchingWindow
from ui_supplier_manager import SupplierManagerDialog
from ui_product_info import ProductInfoDialog
from pandas_model import PandasModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_code_column()
        init_db()
        self.setWindowTitle("Importer — Modern")
        self.resize(1250, 780)
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)

        # Top bar
        top = QHBoxLayout()
        btn_open = QPushButton("Открыть Excel/PDF"); btn_open.clicked.connect(self.open_file); top.addWidget(btn_open)
        btn_suppliers = QPushButton("Управление поставщиками"); btn_suppliers.clicked.connect(self.manage_suppliers); top.addWidget(btn_suppliers)
        btn_match = QPushButton("Сопоставление товаров"); btn_match.clicked.connect(self.open_matcher_window); top.addWidget(btn_match)
        self.lbl_info = QLabel("Файл: не выбран"); top.addWidget(self.lbl_info); top.addStretch()
        layout.addLayout(top)

        # Main area
        middle = QHBoxLayout()

        # Left: my products
        left = QVBoxLayout()
        left.addWidget(QLabel("Мои товары:"))
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("Поиск..."); self.search_box.textChanged.connect(self.load_my_products); left.addWidget(self.search_box)
        self.my_products_list = QListWidget(); self.my_products_list.setAlternatingRowColors(True); self.my_products_list.itemDoubleClicked.connect(self.open_product_info_from_item); left.addWidget(self.my_products_list)
        btns = QHBoxLayout()
        btn_import = QPushButton("Импорт моих товаров (Excel)"); btn_import.clicked.connect(self.import_my_products); btns.addWidget(btn_import)
        btn_info = QPushButton("Информация о товаре"); btn_info.clicked.connect(self.open_product_info_selected); btns.addWidget(btn_info)
        left.addLayout(btns)
        middle.addLayout(left,1)

        # Center: preview
        center = QVBoxLayout(); center.addWidget(QLabel("Предпросмотр (Наименование, Цена, шт, Сумма)"))
        self.table = QTableView(); self.table.setAlternatingRowColors(True); center.addWidget(self.table); middle.addLayout(center,3)

        # Right: columns and mapping
        right = QVBoxLayout(); right.addWidget(QLabel("Колонки файла:")); self.columns_list = QListWidget(); self.columns_list.setAlternatingRowColors(True); right.addWidget(self.columns_list)
        btn_map = QPushButton("Настроить мэппинг"); btn_map.clicked.connect(self.open_mapping_dialog); right.addWidget(btn_map); middle.addLayout(right,1)

        layout.addLayout(middle)
        self.btn_export = QPushButton("Сформировать итоговый Excel"); self.btn_export.setProperty("id","excel"); self.btn_export.setStyleSheet("background: #22c55e; color: white; padding:8px; border-radius:8px;"); self.btn_export.clicked.connect(self.generate_final); layout.addWidget(self.btn_export)
        self.setStyleSheet(BASE_STYLE)

        self.current_df = pd.DataFrame(); self.current_processed_df = pd.DataFrame(); self.current_supplier_id = None
        self.load_my_products()

    def load_my_products(self):
        self.my_products_list.clear(); q=self.search_box.text().strip().lower()
        for r in get_all_products():
            code = r['code'] if "code" in r.keys() and r['code'] else ''
            name = r['my_name']
            if q=="" or q in name.lower() or (code and q in str(code).lower()):
                item = QListWidgetItem(f"{r['id']}: {name}" + (f" [{code}]" if code else "")); item.setData(Qt.UserRole, r['id']); self.my_products_list.addItem(item)

    def import_my_products(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите Excel с кодами", str(Path.home()), "Excel Files (*.xlsx *.xls)")
        if not path: return
        try:
            df = pd.read_excel(path, dtype=str)
        except Exception as e:
            QMessageBox.critical(self,"Ошибка", str(e)); return
        cols_lower = [str(c).lower() for c in df.columns]; col_code=None; col_name=None
        for i,c in enumerate(cols_lower):
            if any(k in c for k in ("код","code","артикул","sku","id")) and col_code is None: col_code = df.columns[i]
            if any(k in c for k in ("наимен","name","товар")) and col_name is None: col_name = df.columns[i]
        if not col_code or not col_name:
            QMessageBox.warning(self,"Ошибка","Файл должен содержать колонки Код и Наименование."); return
        df2 = df[[col_code, col_name]].rename(columns={col_code:"code", col_name:"name"}).dropna(subset=["code","name"])
        res = import_products_from_df(df2, replace_all=False)
        QMessageBox.information(self,"Импорт", f"Добавлено: {res['added']}, Обновлено: {res['updated']}")
        self.load_my_products()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self,"Выберите файл поставщика", str(Path.home()), "Excel Files (*.xlsx *.xls);;PDF Files (*.pdf)")
        if not path: return
        self.current_path = path; self.lbl_info.setText(f"Файл: {Path(path).name}")
        try:
            df = read_supplier_file(path)
        except Exception as e:
            QMessageBox.critical(self,"Ошибка чтения", str(e)); return
        df.columns = [str(c).strip() for c in df.columns]; self.current_df = df.copy(); self.columns_list.clear()
        for c in df.columns: self.columns_list.addItem(c)
        suppliers = get_suppliers()
        from PySide6.QtWidgets import QInputDialog
        items = ["<Создать нового>"] + [f"{s['id']}: {s['name']}" for s in suppliers]
        item, ok = QInputDialog.getItem(self,"Поставщик","Выберите поставщика:", items, 0, False)
        if not ok: return
        if item=="<Создать нового>":
            name, ok2 = QInputDialog.getText(self,"Новый поставщик","Имя:")
            if not ok2 or not name.strip(): return
            sid = add_supplier(name.strip()); self.current_supplier_id = sid
        else:
            self.current_supplier_id = int(item.split(":")[0])
        add_supplier_file_history(self.current_supplier_id, Path(path).name, list(df.columns))
        mapping = map_columns_by_keywords(df)
        proc = pd.DataFrame()
        for file_col, logical in mapping.items():
            if file_col in df.columns and logical in ("name","qty","price","sum"):
                proc[logical] = df[file_col]
        proc = clean_supplier_df(proc)
        for c in ("qty","price","sum"):
            if c in proc.columns:
                proc[c] = proc[c].astype(str).str.replace('\xa0','').str.replace(' ','')
                proc[c] = proc[c].str.replace(r'[^\d\.,\-]','',regex=True).str.replace(',','.')
                proc[c] = pd.to_numeric(proc[c], errors='coerce').fillna(0)
            else:
                proc[c] = 0.0
        preview = proc.copy(); rename_map={}
        if 'name' in preview.columns: rename_map['name'] = 'Наименование'
        if 'price' in preview.columns: rename_map['price'] = 'Цена'
        if 'qty' in preview.columns: rename_map['qty'] = 'шт'
        if 'sum' in preview.columns: rename_map['sum'] = 'Сумма'
        preview = preview.rename(columns=rename_map)
        self.current_processed_df = proc.reset_index(drop=True)
        self.table.setModel(PandasModel(preview.head(200))); self.table.resizeColumnsToContents()
        supplier_names = self.current_processed_df['name'].dropna().astype(str).str.strip().unique() if 'name' in self.current_processed_df.columns else []
        mapped = sum(1 for n in supplier_names if get_product_mapping(self.current_supplier_id, n))
        unmapped = len(supplier_names) - mapped
        msg = f"Уникальных товаров: {len(supplier_names)}\nСопоставлено: {mapped}\nНе сопоставлено: {unmapped}"
        if unmapped > 0:
            ans = QMessageBox.question(self,"Статус сопоставления", msg + "\n\nОткрыть окно сопоставления сейчас?")
            if ans == QMessageBox.Yes: self.open_matcher_window()
        else:
            QMessageBox.information(self,"Статус", msg)

    def open_mapping_dialog(self):
        QMessageBox.information(self,"Мэппинг","Используйте окно 'Сопоставление товаров' для точного мэппинга.")

    def open_matcher_window(self):
        if self.current_supplier_id is None:
            QMessageBox.warning(self,"Ошибка","Сначала откройте файл и выберите поставщика."); return
        supplier_products = self.current_processed_df['name'].dropna().astype(str).unique().tolist() if 'name' in self.current_processed_df.columns else []
        dlg = ProductMatchingWindow(self, self.current_supplier_id, supplier_products); dlg.exec()
        self.load_my_products()
        if not self.current_processed_df.empty:
            preview = self.current_processed_df.copy(); rename_map={}
            if 'name' in preview.columns: rename_map['name']='Наименование'
            if 'price' in preview.columns: rename_map['price']='Цена'
            if 'qty' in preview.columns: rename_map['qty']='шт'
            if 'sum' in preview.columns: rename_map['sum']='Сумма'
            preview = preview.rename(columns=rename_map)
            self.table.setModel(PandasModel(preview.head(200)))

    def manage_suppliers(self):
        dlg = SupplierManagerDialog(self); dlg.exec(); self.load_my_products()

    def open_product_info_from_item(self, item):
        pid = item.data(Qt.UserRole); dlg = ProductInfoDialog(pid, self); dlg.exec()

    def open_product_info_selected(self):
        it = self.my_products_list.currentItem()
        if not it: QMessageBox.warning(self,"Ошибка","Сначала выберите товар."); return
        pid = it.data(Qt.UserRole); dlg = ProductInfoDialog(pid, self); dlg.exec()

    def generate_final(self):
        if self.current_processed_df is None or self.current_processed_df.empty:
            QMessageBox.warning(self,"Ошибка","Нет данных для экспорта."); return
        df_final, price_updates = build_final_table(self.current_processed_df, self.current_supplier_id, get_product_mapping, lambda: get_all_products())
        path, _ = QFileDialog.getSaveFileName(self,"Сохранить итоговый файл","itog.xlsx","Excel Files (*.xlsx)")
        if not path: return
        save_to_excel(df_final, path)
        # update last_price and price history
        for pid, price in price_updates:
            try:
                record_price_if_changed(pid, price)
                conn = get_connection(); cur = conn.cursor(); cur.execute("UPDATE my_products SET last_price = ? WHERE id = ?", (price, pid)); conn.commit(); conn.close()
            except Exception:
                pass
        QMessageBox.information(self,"Готово", f"Файл сохранён: {path}")
