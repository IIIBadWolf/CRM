# pandas_model.py
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
import pandas as pd

class PandasModel(QAbstractTableModel):
    def __init__(self, df=None, parent=None):
        super().__init__(parent)
        self._df = df.reset_index(drop=True) if df is not None else pd.DataFrame()

    def rowCount(self, parent=QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QModelIndex()):
        return 0 if self._df.empty else len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            val = self._df.iat[index.row(), index.column()]
            if pd.isna(val):
                return ""
            return str(val)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        else:
            return str(section + 1)
