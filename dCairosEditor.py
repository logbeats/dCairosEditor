import sys
import os
import numpy as np
import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
from PandasModellib import PandasModel
from PyQt5.QtWidgets import QWidget, QTableView, QLineEdit, QPushButton, QButtonGroup, QHBoxLayout, QGridLayout
from PyQt5.QtWidgets import QVBoxLayout, QFileDialog, QApplication, QDesktopWidget, QComboBox, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QRegExp, QSortFilterProxyModel, QModelIndex


class CustomProxyModel(QSortFilterProxyModel):
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
            regex = QRegExp(expresion, Qt.CaseInsensitive, QRegExp.RegExp)
            if regex.indexIn(text) == -1:
                return False
        return True


class dCairosEditor(QWidget):
    def __init__(self, parent=None):
        super(dCairosEditor, self).__init__()
        self.setWindowTitle('dCairosEditor')
        self.center()
        self.tableView = QTableView()
        self.label = QLabel()
        self.label.setText("Filter")
        self.lineEdit = QLineEdit()
        self.comboBox = QComboBox()

        self.gridLayout = QGridLayout()
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.lineEdit, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.comboBox, 0, 2, 1, 1)

        self.tableView.clicked.connect(self.viewClicked)
        self.tableView.setStyleSheet("QTableView{gridline-color: black}")

        self.basedir = os.path.abspath(os.path.dirname(__file__))
        self.fileName = os.path.join(self.basedir, 'csv', 'BaseLine', 'IIS.csv')
        
        self.header = pd.read_csv(self.fileName).loc[0].tolist()
        df = pd.read_csv(self.fileName, header=1)

        self.model = PandasModel(df)
        self.proxy = CustomProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.tableView.setModel(self.proxy)
        self.tableView.resizeColumnsToContents()

        self.comboBox.clear()
        self.comboBox.addItems(["{0}".format(col) for col in self.model._data.columns])
        self.lineEdit.textChanged.connect(self.on_lineEdit_textChanged)
        self.comboBox.currentIndexChanged.connect(self.on_comboBox_currentIndexChanged)

        self.tableView.resizeColumnsToContents()  # 컬럼 전체 자동 사이즈 조절
        self.tableView.resizeRowsToContents()  # 행 전체 자동 사이즈 조절

        self.tableView.setAlternatingRowColors(True)
        self.selectRow = self.model.rowCount(QModelIndex())

        self.filters = "CSV files (*.csv)"

        self.fileName = None

        self.buttonOpen = QPushButton('Open', self)
        self.buttonSave = QPushButton('Save', self)
        self.buttonAdd = QPushButton('add', self)
        self.buttonDel = QPushButton('Del', self)

        self.group = QButtonGroup()
        self.group.addButton(self.buttonOpen)
        self.group.addButton(self.buttonSave)
        self.group.addButton(self.buttonAdd)
        self.group.addButton(self.buttonDel)

        self.buttonOpen.clicked.connect(self.handleOpen)
        self.buttonSave.clicked.connect(self.handleSave)
        self.buttonAdd.clicked.connect(self.insertRows)
        self.buttonDel.clicked.connect(self.removeRows)

        layout = QHBoxLayout()
        layout.addWidget(self.buttonOpen)
        layout.addWidget(self.buttonSave)
        layout.addWidget(self.buttonAdd)
        layout.addWidget(self.buttonDel)

        Vlayout = QVBoxLayout()
        Vlayout.addLayout(self.gridLayout)
        Vlayout.addWidget(self.tableView)
        Vlayout.addLayout(layout)
        
        self.setLayout(Vlayout)

################################################################################
    def handleSave(self):
        if self.fileName == None or self.fileName == '':
            self.fileName, self.filters = QFileDialog.getSaveFileName(self, filter=self.filters)
        if(self.fileName != ''):
            labels = []
            labels.append(self.header)
            for row in range(self.model.rowCount(QModelIndex())):
                rowdata = []
                for column in range(self.model.columnCount(QModelIndex())):
                    item = self.model.index(row, column, QModelIndex()).data(Qt.DisplayRole)
                    if item is not None:
                       rowdata.append(item)
                    else:
                       rowdata.append('')
                labels.append(rowdata)
            df = pd.DataFrame(labels)
            df.to_csv(self.fileName, mode='w', index=False)

            return True
        else:
            return False

################################################################################
    def handleOpen(self):
        self.fileName, self.filterName = QFileDialog.getOpenFileName(self)

        if self.fileName != '':
            self.header = pd.read_csv(self.fileName).loc[0].tolist()
            df = pd.read_csv(self.fileName, header=1)
            self.model = None
            self.model = PandasModel(df)
            self.proxy = CustomProxyModel(self)
            self.proxy.setSourceModel(self.model)
            self.tableView.setModel(self.proxy)

            self.tableView.resizeColumnsToContents()  # 컬럼 전체 자동 사이즈 조절
            self.tableView.resizeRowsToContents()  # 행 전체 자동 사이즈 조절
            self.fileName = ''
            self.lineEdit.clear()
            self.comboBox.clear()
            self.comboBox.addItems(["{0}".format(col) for col in self.model._data.columns])
            
            return True
        else:
            return False

################################################################################
    def insertRows(self, position, rows=1, index=QModelIndex()):
        self.selectRow = self.model.rowCount(QModelIndex())
        self.model.beginInsertRows(QModelIndex(), position, position + rows - 1)
        self.model._data.loc[self.selectRow] = 'NoData'
        self.model.endInsertRows()

        return True

################################################################################
    def removeRows(self, position, rows=1, index=QModelIndex()):
        self.selectRow = self.model.rowCount(QModelIndex())
        self.model.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        if self.selectRow-1 >= 0:
            self.model._data.drop([self.selectRow-1], inplace=True)
            self.model._data.reset_index(drop=True, inplace=True)
            self.model.endRemoveRows()

            return True
        else:
            return False

################################################################################
    def viewClicked(self, indexClicked):
        print('indexClicked() row: %s  column: %s' %
              (indexClicked.row(), indexClicked.column()))
        self.selectRow = indexClicked.row()

################################################################################
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
###############################################################################
    @QtCore.pyqtSlot(int)
    def on_signalMapper_mapped(self, i):
        stringAction = self.signalMapper.mapping(i).text()
        filterColumn = self.logicalIndex
        self.proxy.setFilter(stringAction, filterColumn)
        font = QFont()
        font.setBold(True)
        self.model.setFont(filterColumn, font)

    @QtCore.pyqtSlot(str)
    def on_lineEdit_textChanged(self, text):
        self.proxy.setFilter(text, self.proxy.filterKeyColumn())

    @QtCore.pyqtSlot(int)
    def on_comboBox_currentIndexChanged(self, index):
        self.proxy.setFilterKeyColumn(index)
###############################################################################
if __name__ == "__main__":  # Main Application
    app = QApplication(sys.argv)
    CairosEditor = dCairosEditor()
    CairosEditor.show()
    CairosEditor.resize(1200, 800)
    sys.exit(app.exec_())
###############################################################################
