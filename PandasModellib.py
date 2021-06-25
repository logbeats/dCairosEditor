from PyQt5 import QtCore

import pandas as pd


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self._data = df.copy()
        self.bolds = dict()

    def toDataFrame(self):
        return self._data.copy()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                try:
                    return self._data.columns.tolist()[section]
                except (IndexError,):
                    return QtCore.QVariant()
            elif role == QtCore.Qt.FontRole:
                return self.bolds.get(section, QtCore.QVariant())
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                try:
                    # return self.df.index.tolist()
                    return self._data.index.tolist()[section]
                except (IndexError,):
                    return QtCore.QVariant()
        return QtCore.QVariant()

    def setFont(self, section, font):
        self.bolds[section] = font
        self.headerDataChanged.emit(QtCore.Qt.Horizontal, 0, self.columnCount())

    def data(self, index, role=QtCore.Qt.DisplayRole):
    #    if role != QtCore.Qt.DisplayRole:
    #        return QtCore.QVariant()

    #    if not index.isValid():
    #        return QtCore.QVariant()

    #    return QtCore.QVariant(str(self._data.iloc[index.row(), index.column()]))
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
            elif role == QtCore.Qt.TextAlignmentRole:
                return QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif role == QtCore.Qt.EditRole:
                return str(self._data.values[index.row()][index.column()])

        return None

    def setData(self, index, value, role):
        row = self._data.index[index.row()]
        col = self._data.columns[index.column()]
        if not index.isValid():
            return False
        if role != QtCore.Qt.EditRole:
            return False
        row = index.row()
        if row < 0 or row >= len(self._data.values):
            return False
        column = index.column()
        if column < 0 or column >= self._data.columns.size:
            return False
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._data[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._data.set_value(row, col, value)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._data.columns)

    def sort(self, column, order):
        colname = self._data.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._data.sort_values(colname, ascending=order ==
                             QtCore.Qt.AscendingOrder, inplace=True)
        self._data.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role != QtCore.Qt.EditRole:
            return False
        row = index.row()
        if row < 0 or row >= len(self._data.values):
            return False
        column = index.column()
        if column < 0 or column >= self._data.columns.size:
            return False
        self._data.values[row][column] = value
        self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        flags = super(self.__class__, self).flags(index)
        flags |= QtCore.Qt.ItemIsEditable
        flags |= QtCore.Qt.ItemIsSelectable
        flags |= QtCore.Qt.ItemIsEnabled
        flags |= QtCore.Qt.ItemIsDragEnabled
        flags |= QtCore.Qt.ItemIsDropEnabled
        return flags
