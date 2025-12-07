# styles.py
# Modern UI palette inspired by macOS / Windows 11 glassmorphism
BASE_STYLE = """
QMainWindow, QWidget {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f5f7fb, stop:1 #e8ecf6);
    color: #0f172a;
    font-family: "SF Pro Display", "Segoe UI", Inter, Roboto, Arial;
    font-size: 14px;
}

QLabel {
    color: #0f172a;
    font-weight: 600;
    letter-spacing: 0.2px;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f8bff, stop:1 #2563eb);
    color: white;
    border-radius: 10px;
    padding: 9px 14px;
    border: 1px solid rgba(255,255,255,0.25);
    min-height: 36px;
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.25);
}

QPushButton#excel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d399, stop:1 #10b981);
    box-shadow: 0 10px 24px rgba(16, 185, 129, 0.3);
}

QPushButton:hover { opacity: 0.96; }

QListWidget, QTableView, QLineEdit {
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(203, 213, 225, 0.9);
    border-radius: 12px;
    padding: 6px;
}

QListWidget::item {
    padding: 10px;
    border-radius: 8px;
}

QListWidget::item:selected {
    background: rgba(79, 139, 255, 0.18);
    color: #0f172a;
}

QListWidget::item:hover {
    background: rgba(15, 23, 42, 0.04);
}

QTableView {
    gridline-color: rgba(15, 23, 42, 0.06);
    selection-background-color: rgba(79, 139, 255, 0.18);
    selection-color: #0f172a;
    alternate-background-color: rgba(15, 23, 42, 0.02);
}

QHeaderView::section {
    background: transparent;
    padding: 10px 8px;
    font-weight: 700;
    border: none;
    color: #1e293b;
}

QLineEdit {
    padding: 10px 12px;
    background: rgba(255,255,255,0.9);
    border: 1px solid rgba(203, 213, 225, 0.9);
    border-radius: 12px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 10px 0 10px 0;
}

QScrollBar::handle:vertical {
    background: rgba(15, 23, 42, 0.12);
    min-height: 24px;
    border-radius: 6px;
}

QScrollBar::add-line, QScrollBar::sub-line { height:0px; }

QRadioButton::indicator, QCheckBox::indicator {
    width: 18px; height: 18px;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: white;
}

QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34d399, stop:1 #10b981);
    border: none;
}
"""
