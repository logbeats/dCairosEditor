#!/usr/bin/env python
# -*- coding:utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

import pandas as pd


class CustomProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters = dict()

    @property
    def filters(self):
        return self._filters

    def setFilter(self, expresion, column):
        if expresion:
            self.filters[column] = expresion
        elif column in self.filters:
            del self.filters[column]
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for column, expresion in self.filters.items():
            text = self.sourceModel().index(source_row, column, source_parent).data()
            regex = QtCore.QRegExp(
                expresion, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.RegExp
            )
            if regex.indexIn(text) == -1:
                return False
        return True


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()
        self.bolds = dict()

    def toDataFrame(self):
        return self._df.copy()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                try:
                    return self._df.columns.tolist()[section]
                except (IndexError,):
                    return QtCore.QVariant()
            elif role == QtCore.Qt.FontRole:
                return self.bolds.get(section, QtCore.QVariant())
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                try:
                    # return self.df.index.tolist()
                    return self._df.index.tolist()[section]
                except (IndexError,):
                    return QtCore.QVariant()
        return QtCore.QVariant()

    def setFont(self, section, font):
        self.bolds[section] = font
        self.headerDataChanged.emit(
            QtCore.Qt.Horizontal, 0, self.columnCount())

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if not index.isValid():
            return QtCore.QVariant()

        return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending=order ==
                             QtCore.Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class myWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(myWindow, self).__init__(parent)
        self.centralwidget = QtWidgets.QWidget(self)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.view = QtWidgets.QTableView(self.centralwidget)
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.label = QtWidgets.QLabel(self.centralwidget)

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.view, 1, 0, 1, 3)
        self.gridLayout.addWidget(self.comboBox, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.setCentralWidget(self.centralwidget)
        self.label.setText("Regex Filter")

        self.load_sites()
        self.comboBox.addItems(["{0}".format(col)
                                for col in self.model._df.columns])

        self.lineEdit.textChanged.connect(self.on_lineEdit_textChanged)
        self.comboBox.currentIndexChanged.connect(
            self.on_comboBox_currentIndexChanged)

        self.horizontalHeader = self.view.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(
            self.on_view_horizontalHeader_sectionClicked)

    def load_sites(self):

        df = pd.DataFrame({'site_codes': ['01', '02', '03', '04'],
                           'status': ['open', 'open', 'open', 'closed'],
                           'Location': ['east', 'north', 'south', 'east'],
                           'data_quality': ['poor', 'moderate', 'high', 'high']})

        self.model = PandasModel(df)
        self.proxy = CustomProxyModel(self)
        #self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.view.setModel(self.proxy)
        self.view.resizeColumnsToContents()
        print("finished loading sites")

    @QtCore.pyqtSlot(int)
    def on_view_horizontalHeader_sectionClicked(self, logicalIndex):

        self.logicalIndex = logicalIndex
        self.menuValues = QtWidgets.QMenu(self)
        self.signalMapper = QtCore.QSignalMapper(self)
        self.comboBox.blockSignals(True)
        self.comboBox.setCurrentIndex(self.logicalIndex)
        self.comboBox.blockSignals(True)

        valuesUnique = self.model._df.iloc[:, self.logicalIndex].unique()

        actionAll = QtWidgets.QAction("All", self)
        actionAll.triggered.connect(self.on_actionAll_triggered)
        self.menuValues.addAction(actionAll)
        self.menuValues.addSeparator()
        for actionNumber, actionName in enumerate(sorted(list(set(valuesUnique)))):
            action = QtWidgets.QAction(actionName, self)
            self.signalMapper.setMapping(action, actionNumber)
            action.triggered.connect(self.signalMapper.map)
            self.menuValues.addAction(action)
        self.signalMapper.mapped.connect(self.on_signalMapper_mapped)
        headerPos = self.view.mapToGlobal(self.horizontalHeader.pos())
        posY = headerPos.y() + self.horizontalHeader.height()
        posX = headerPos.x() + self.horizontalHeader.sectionPosition(self.logicalIndex)

        self.menuValues.exec_(QtCore.QPoint(posX, posY))

    @QtCore.pyqtSlot()
    def on_actionAll_triggered(self):
        filterColumn = self.logicalIndex
        self.proxy.setFilter("", filterColumn)
        font = QtGui.QFont()
        self.model.setFont(filterColumn, font)

    @QtCore.pyqtSlot(int)
    def on_signalMapper_mapped(self, i):
        stringAction = self.signalMapper.mapping(i).text()
        filterColumn = self.logicalIndex
        self.proxy.setFilter(stringAction, filterColumn)
        font = QtGui.QFont()
        font.setBold(True)
        self.model.setFont(filterColumn, font)

    @QtCore.pyqtSlot(str)
    def on_lineEdit_textChanged(self, text):
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @QtCore.pyqtSlot(int)
    def on_comboBox_currentIndexChanged(self, index):
        self.proxy.setFilterKeyColumn(index)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main = myWindow()
    main.show()
    main.resize(800, 600)
    sys.exit(app.exec_())
