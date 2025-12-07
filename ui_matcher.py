# ui_matcher.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLineEdit, QLabel, QRadioButton, QButtonGroup, QMessageBox, QListWidgetItem, QSplitter, QWidget, QCheckBox, QDialogButtonBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from db import get_all_products, save_product_mapping, get_all_product_mappings_for_supplier, get_product_mapping
try:
    from rapidfuzz import fuzz
    def similarity(a,b):
        return fuzz.token_set_ratio(str(a), str(b))
except Exception:
    import difflib
    def similarity(a,b):
        return int(difflib.SequenceMatcher(None, str(a), str(b)).ratio()*100)

class AutoConfirmDialog(QDialog):
    def __init__(self, parent, suggestions, my_products):
        super().__init__(parent)
        self.setWindowTitle("Подтвердите автосопоставления")
        self.resize(700,500)
        self.suggestions = suggestions
        self.my_products = {p['id']: p['my_name'] for p in my_products}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите, какие из предложенных соответствий применить:"))
        self.list = QListWidget()
        for sup, mid, score in suggestions:
            txt = f"{sup}  →  {mid}: {self.my_products.get(mid,'?')}  (score {score})"
            it = QListWidgetItem(txt); it.setCheckState(Qt.Checked); self.list.addItem(it)
        layout.addWidget(self.list)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_selected(self):
        res=[]
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.Checked:
                sup, rest = it.text().split("  →  ",1)
                mid = int(rest.split(":")[0])
                res.append((sup, mid))
        return res

class ProductMatchingWindow(QDialog):
    def __init__(self, parent, supplier_id, supplier_products):
        super().__init__(parent)
        self.supplier_id = supplier_id
        self.supplier_products = supplier_products or []
        self.setWindowTitle("Сопоставление товаров")
        self.resize(1140, 760)
        layout = QVBoxLayout(self)
        ctrl = QHBoxLayout()
        self.rb_common = QRadioButton("Общий"); self.rb_my = QRadioButton("Только мои"); self.rb_supplier = QRadioButton("Только поставщика")
        self.rb_common.setChecked(True)
        self.radio_group = QButtonGroup(self); self.radio_group.addButton(self.rb_common); self.radio_group.addButton(self.rb_my); self.radio_group.addButton(self.rb_supplier)
        ctrl.addWidget(self.rb_common); ctrl.addWidget(self.rb_my); ctrl.addWidget(self.rb_supplier); ctrl.addStretch()
        layout.addLayout(ctrl)
        self.search = QLineEdit(); self.search.setPlaceholderText("Поиск..."); self.search.textChanged.connect(self.apply_filter); layout.addWidget(self.search)
        splitter = QSplitter(Qt.Horizontal)
        left_w = QWidget(); left_l = QVBoxLayout(left_w); left_l.addWidget(QLabel("Мои товары")); self.list_my = QListWidget(); self.list_my.setAlternatingRowColors(True); left_l.addWidget(self.list_my); splitter.addWidget(left_w)
        center_w = QWidget(); center_l = QVBoxLayout(center_w); center_l.addStretch(); self.btn_link = QPushButton("Связать →"); self.btn_link.clicked.connect(self.link); center_l.addWidget(self.btn_link); center_l.addStretch(); splitter.addWidget(center_w)
        right_w = QWidget(); right_l = QVBoxLayout(right_w); right_l.addWidget(QLabel("Товары поставщика")); self.list_sup = QListWidget(); self.list_sup.setAlternatingRowColors(True); self.list_sup.setSelectionMode(QListWidget.ExtendedSelection); right_l.addWidget(self.list_sup); splitter.addWidget(right_w)
        layout.addWidget(splitter,6)
        bottom_h = QHBoxLayout()
        self.btn_auto = QPushButton("Автосопоставить (threshold=85)"); self.btn_auto.clicked.connect(self.auto_suggest_and_confirm)
        bottom_h.addWidget(self.btn_auto)
        self.chk_show_mapped = QCheckBox("Показывать сопоставленные"); self.chk_show_mapped.setChecked(True); self.chk_show_mapped.stateChanged.connect(self.apply_filter)
        bottom_h.addWidget(self.chk_show_mapped)
        bottom_h.addStretch()
        layout.addLayout(bottom_h)
        layout.addWidget(QLabel("Все сопоставления для поставщика"))
        self.list_links = QListWidget(); layout.addWidget(self.list_links,2)
        self.load_lists(); self.apply_filter()

    def load_lists(self):
        self.my_products = list(get_all_products())
        self.list_my.clear()
        for p in self.my_products:
            code = p['code'] if "code" in p.keys() and p['code'] else ''
            it = QListWidgetItem(f"{p['id']}: {p['my_name']}" + (f" [{code}]" if code else ""))
            it.setData(Qt.UserRole, p['id']); self.list_my.addItem(it)

        mappings = get_all_product_mappings_for_supplier(self.supplier_id)
        mapped_names = dict(mappings)

        unmatched = [s for s in self.supplier_products if s not in mapped_names]
        matched = [s for s in self.supplier_products if s in mapped_names]

        self.list_sup.clear()
        for s in unmatched + matched:
            it = QListWidgetItem(s)
            is_mapped = s in mapped_names
            it.setData(Qt.UserRole, is_mapped)
            if is_mapped:
                it.setBackground(QColor("#dff7e6"))
                it.setToolTip("Связан с товаром: ID %s" % mapped_names[s])
                it.setText(f"✓ {s}")
            self.list_sup.addItem(it)

        self.list_links.clear()
        for sname, mid in mapped_names.items():
            self.list_links.addItem(f"{sname}  →  {mid}")

    def apply_filter(self):
        q = self.search.text().strip().lower()
        mode = 'common'
        if self.rb_my.isChecked(): mode = 'my'
        elif self.rb_supplier.isChecked(): mode = 'supplier'
        self.list_my.clear()
        for p in self.my_products:
            name = p['my_name']
            code = p['code'] if "code" in p.keys() and p['code'] else ''
            ok = False
            if q == "":
                ok = True
            else:
                if mode in ('common','my') and q in name.lower():
                    ok = True
                if mode in ('common','my') and code and q in str(code).lower():
                    ok = True
            if ok:
                it = QListWidgetItem(f"{p['id']}: {p['my_name']}" + (f" [{code}]" if code else ""))
                it.setData(Qt.UserRole, p['id'])
                self.list_my.addItem(it)

        # supplier list filter + hide mapped if unchecked
        for i in range(self.list_sup.count()-1, -1, -1):
            it = self.list_sup.item(i)
            txt = it.text().lower()
            show = True
            if q != "":
                show = (mode in ('common','supplier') and q in txt)
            # hide mapped if checkbox off
            if not self.chk_show_mapped.isChecked():
                if it.data(Qt.UserRole):
                    show = False
            it.setHidden(not show)

    def auto_suggest(self, threshold=85):
        suggestions = []
        for s in self.supplier_products:
            best = (None, 0)
            for p in self.my_products:
                sc = similarity(s.lower(), p['my_name'].lower())
                if sc > best[1]:
                    best = (p['id'], sc)
            if best[1] >= threshold:
                suggestions.append((s, best[0], best[1]))
        return suggestions

    def auto_suggest_and_confirm(self):
        suggestions = self.auto_suggest(threshold=85)
        if not suggestions:
            QMessageBox.information(self, "Автопоиск", "Подходящих совпадений не найдено.")
            return
        dlg = AutoConfirmDialog(self, suggestions, self.my_products)
        if dlg.exec():
            chosen = dlg.get_selected()
            for sup, mid in chosen:
                save_product_mapping(self.supplier_id, sup, mid)
            QMessageBox.information(self, "Готово", f"Применено {len(chosen)} сопоставлений.")
            self.load_lists()

    def link(self):
        my_item = self.list_my.currentItem()
        if not my_item:
            QMessageBox.warning(self, "Ошибка", "Выберите свой товар слева")
            return
        my_id = int(my_item.data(Qt.UserRole))
        sel = self.list_sup.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Ошибка", "Выберите товары справа")
            return
        for it in sel:
            sup_name = it.text().strip()
            save_product_mapping(self.supplier_id, sup_name, my_id)
        QMessageBox.information(self, "Готово", f"Связано {len(sel)} позиций")
        self.load_lists()
