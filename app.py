# app.py
import sys
from PySide6.QtWidgets import QApplication
from db import init_db, rotate_backups
from ui_main import MainWindow

def main():
    rotate_backups()      # ротация backup перед любыми изменениями
    init_db()             # создаём таблицы, если их нет
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
