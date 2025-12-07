# styles.py
BASE_STYLE = """
QWidget { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #f7f8fb, stop:1 #f1f4fb); font-family: "Segoe UI", Roboto, Arial; }
QLabel { color: #0f172a; font-weight: 600; }
QPushButton { background: #2563eb; color: white; border-radius:10px; padding:8px 12px; border: none; min-height: 34px; }
QPushButton#excel { background: #22c55e; }
QPushButton:hover { opacity: 0.95; }
QListWidget { background: rgba(255,255,255,0.95); border: 1px solid rgba(230,233,242,0.9); border-radius:8px; padding:4px; }
QListWidget::item { padding:8px; }
QListWidget::item:selected { background: rgba(199,215,255,0.85); color: #0b1220; border-radius:6px; }
QTableView { background: rgba(255,255,255,0.98); border: none; border-radius:8px; gridline-color: rgba(0,0,0,0.04); }
QHeaderView::section { background: transparent; padding:8px; font-weight:600; }
QLineEdit { background: rgba(255,255,255,0.98); border: 1px solid rgba(230,233,242,0.95); padding:8px; border-radius:8px; }
QScrollBar:vertical { background: transparent; width:10px; margin:8px 0 8px 0; }
QScrollBar::handle:vertical { background: rgba(0,0,0,0.12); min-height:20px; border-radius:6px; }
QScrollBar::add-line, QScrollBar::sub-line { height:0px; }
QRadioButton::indicator { width:18px; height:18px; border-radius:6px; border: 1px solid #cbd5e1; background: white; }
QRadioButton::indicator:checked { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #34d399, stop:1 #10b981); border: none; }
QCheckBox::indicator { width:18px; height:18px; }
"""
