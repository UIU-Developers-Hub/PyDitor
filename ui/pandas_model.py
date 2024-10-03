#E:\UDH\Compiler\ui\pandas_model.py

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt

from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QTextCharFormat, QColor, QFont
from .syntax_highlighter import PythonSyntaxHighlighte
class PandasModel(QAbstractTableModel):
    def __init__(self, dataframe):
        super().__init__()
        self._dataframe = dataframe

    def rowCount(self, parent=None):
        return len(self._dataframe)

    def columnCount(self, parent=None):
        return len(self._dataframe.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # Use Qt.ItemDataRole.DisplayRole
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:  # Change here
                return str(self._dataframe.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:  # Change here
            if orientation == Qt.Orientation.Horizontal:
                return self._dataframe.columns[section]
            else:
                return self._dataframe.index[section]
        return None
