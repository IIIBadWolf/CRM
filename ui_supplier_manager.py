# ui_supplier_manager.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QLineEdit
from PySide6.QtCore import Qt
from db import get_suppliers, add_supplier, rename_supplier, delete_supplier

class SupplierManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управление поставщиками")
        self.resize(520, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Список поставщиков</b>"))
        self.list = QListWidget()
        layout.addWidget(self.list)
        btns = QHBoxLayout()
        btn_add = QPushButton("Добавить"); btn_add.clicked.connect(self.add_supplier); btns.addWidget(btn_add)
        btn_rename = QPushButton("Переименовать"); btn_rename.clicked.connect(self.rename_supplier_clicked); btns.addWidget(btn_rename)
        btn_delete = QPushButton("Удалить"); btn_delete.clicked.connect(self.delete_supplier); btns.addWidget(btn_delete)
        btn_close = QPushButton("Закрыть"); btn_close.clicked.connect(self.close); btns.addWidget(btn_close)
        layout.addLayout(btns)
        self.load_suppliers()

    def load_suppliers(self):
        self.list.clear()
        for s in get_suppliers():
            it = QListWidgetItem(f"{s['id']}: {s['name']}")
            it.setData(Qt.UserRole, s['id'])
            self.list.addItem(it)

    def add_supplier(self):
        name, ok = QInputDialog.getText(self, "Добавить поставщика", "Имя:")
        if not ok or not name.strip(): return
        add_supplier(name.strip()); self.load_suppliers()

    def rename_supplier_clicked(self):
        it = self.list.currentItem()
        if not it:
            QMessageBox.information(self, "Ошибка", "Выберите поставщика"); return
        sid = it.data(Qt.UserRole); old = it.text().split(": ",1)[1]
        new, ok = QInputDialog.getText(self, "Переименовать", "Новое имя:", QLineEdit.Normal, old)
        if not ok or not new.strip(): return
        rename_supplier(sid, new.strip()); self.load_suppliers()

    def delete_supplier(self):
        it = self.list.currentItem()
        if not it:
            QMessageBox.information(self, "Ошибка", "Выберите поставщика"); return
        sid = it.data(Qt.UserRole)
        if QMessageBox.question(self, "Удалить?", "Удалить этого поставщика?") != QMessageBox.Yes: return
        delete_supplier(sid); self.load_suppliers()
