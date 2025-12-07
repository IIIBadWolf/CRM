# ui_product_info.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QHBoxLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QCategoryAxis
from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt
from db import get_connection, get_price_history_for_product

class ProductInfoDialog(QDialog):
    def __init__(self, product_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Информация о товаре")
        self.resize(920, 620)
        layout = QVBoxLayout(self)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT id, my_name, code, category, created_at, last_price FROM my_products WHERE id = ?", (product_id,))
        row = cur.fetchone(); conn.close()
        name = row["my_name"] if row and "my_name" in row.keys() else f"#{product_id}"
        code = row["code"] if row and "code" in row.keys() else ""
        created = row["created_at"] if row and "created_at" in row.keys() else ""
        last_price = row["last_price"] if row and "last_price" in row.keys() else None
        header = QLabel(f"<h2>{name}</h2><b>Код:</b> {code} &nbsp;&nbsp; <b>Создан:</b> {created} <br> <b>Последняя цена:</b> {last_price or '-'}")
        header.setTextFormat(Qt.RichText); layout.addWidget(header)
        history = get_price_history_for_product(product_id)
        tbl = QTableWidget(); tbl.setColumnCount(4); tbl.setHorizontalHeaderLabels(["Дата","Цена","Δ от предыдущей","Накопленное Δ"]); tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setRowCount(len(history))
        prev = None; acc = 0.0; diffs=[]
        for i, rec in enumerate(history):
            date = rec.get("date", "") if isinstance(rec, dict) else rec["date"]
            price = float(rec.get("price", 0) if isinstance(rec, dict) else rec["price"])
            if prev is None:
                delta = 0.0
            else:
                delta = round(price - prev, 2)
            acc += delta
            tbl.setItem(i,0, QTableWidgetItem(str(date))); tbl.setItem(i,1, QTableWidgetItem(f"{price:.2f}"))
            item_d = QTableWidgetItem(f"{delta:+.2f}" if prev is not None else "")
            if prev is not None:
                if delta>0: item_d.setForeground(QColor("#059669"))
                elif delta<0: item_d.setForeground(QColor("#dc2626"))
            tbl.setItem(i,2,item_d)
            item_acc = QTableWidgetItem(f"{acc:+.2f}")
            if acc>0: item_acc.setForeground(QColor("#059669"))
            elif acc<0: item_acc.setForeground(QColor("#dc2626"))
            tbl.setItem(i,3,item_acc)
            prev = price; diffs.append(delta)
        layout.addWidget(tbl)
        total_change = sum(d for d in diffs if isinstance(d,(int,float)))
        summary = QLabel(f"<b>Итоговое изменение (сумма всех Δ):</b> {total_change:+.2f}")
        if total_change>0: summary.setStyleSheet("color:#059669;")
        elif total_change<0: summary.setStyleSheet("color:#dc2626;")
        layout.addWidget(summary)
        if history:
            series = QLineSeries(); series.setColor(QColor("#1E88E5")); series.setPen(QPen(QColor("#1E88E5"),2))
            hist_rev = list(reversed(history))
            for idx,rec in enumerate(hist_rev):
                price_val = float(rec.get("price", 0) if isinstance(rec, dict) else rec["price"])
                series.append(idx, price_val)
            chart = QChart(); chart.addSeries(series); chart.setTitle("Динамика цены (старые → новые)")
            axis_x = QCategoryAxis(); axis_x.setLabelsPosition(QCategoryAxis.Center)
            step = max(1, len(hist_rev)//6)
            for i in range(0, len(hist_rev), step):
                d = hist_rev[i].get("date", "") if isinstance(hist_rev[i], dict) else hist_rev[i]["date"]
                axis_x.append(str(d), i)
            last_d = hist_rev[-1].get("date", "") if isinstance(hist_rev[-1], dict) else hist_rev[-1]["date"]
            axis_x.append(str(last_d), len(hist_rev)-1)
            ys = [float(r.get("price",0) if isinstance(r, dict) else r["price"]) for r in hist_rev]
            ymin = min(ys)*0.95 if ys else 0
            ymax = max(ys)*1.05 if ys else 1
            axis_y = QValueAxis(); axis_y.setRange(ymin, ymax)
            chart.addAxis(axis_x, Qt.AlignBottom); chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_x); series.attachAxis(axis_y)
            chart_view = QChartView(chart); chart_view.setRenderHint(QChartView.Antialiasing); layout.addWidget(chart_view)
        btns = QHBoxLayout(); btns.addStretch(); close = QPushButton("Закрыть"); close.clicked.connect(self.accept); btns.addWidget(close); layout.addLayout(btns)
