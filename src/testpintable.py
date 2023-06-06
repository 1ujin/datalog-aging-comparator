#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : table.py
@Time   : 2023年05月23日
@Desc   : 手动填写测试项组件
"""

import pdb
import sys
from collections import OrderedDict
from decimal import Decimal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QTableWidget
from PyQt5.QtGui import QIcon, QPixmap

import resource
import util
from formatdialog import FormatDialog

BEGIN_REGEX = r'\ (Number[^A-Z]*)(Site[^A-Z]*)(Result[^A-Z]*)(Test\ Name[^A-Z]*)(Pin[^A-Z]*)(Channel[^A-Z]*)(Low[^A-Z]*)(Measured[^A-Z]*)(High[^A-Z]*)(Force[^A-Z]*)(Loc[^A-Z]*)\n'
TEST_NAME_PIN_REGEX = r'\ (.{11})(.{6})(.{9})(.{26})(.{12})(.{10})(.{15})(.{15})(.{15})(.{15})(.{3})\s+'

class TestPinTable(QWidget):
    """docstring for TestPinTable"""
    def __init__(self, parent=None):
        super(TestPinTable, self).__init__()
        self.parent = parent
        self.begin_regex = BEGIN_REGEX
        self.regex = TEST_NAME_PIN_REGEX
        self.setStyleSheet('\
            QPushButton { font-family: \"微软雅黑\"; max-width: 50px; }')
        self.initUI()

    def initUI(self):
        btn_layout = QHBoxLayout()
        btn_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        add_btn = QPushButton('添加', self)
        add_btn.clicked.connect(self.addRow)
        btn_layout.addWidget(add_btn)
        del_btn = QPushButton('删除', self)
        del_btn.clicked.connect(self.delRow)
        btn_layout.addWidget(del_btn)
        clear_btn = QPushButton('清空', self)
        clear_btn.clicked.connect(self.clearAll)
        btn_layout.addWidget(clear_btn)
        set_btn = QPushButton('设置', self)
        set_btn.clicked.connect(self.setWidth)
        btn_layout.addWidget(set_btn)

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(['Test Name', 'Pin', '下限（uA/uV）', '上限（uA/uV）'])

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.table)

        main_layout.setContentsMargins(0, 12, 0, 0)
        btn_layout.setContentsMargins(8, 0, 12, 0)

    def addRow(self):
        self.table.insertRow(self.table.rowCount());

    def delRow(self):
        ranges = self.table.selectedRanges()
        ranges.reverse()
        for rows in ranges:
            bottom = rows.bottomRow()
            top = rows.topRow()
            for row in range(bottom, top - 1, -1):
                self.table.removeRow(row)

    def clearAll(self):
        self.table.setRowCount(0)

    def setWidth(self):
        """ 打开配置对话框并导入测试项 """
        dialog = FormatDialog(self)
        dialog.resize(dialog.width(), dialog.height())
        dialog.exec()

    def getPinMap(self):
        pin_map = OrderedDict()
        try:
            for row in range(0, self.table.rowCount()):
                testname = self.table.item(row, 0)
                pinname = self.table.item(row, 1)
                if testname:
                    testname = testname.text().strip()
                else:
                    continue
                if len(testname) == 0:
                    continue
                if pinname:
                    pinname = pinname.text().strip()
                else:
                    continue
                if len(pinname) == 0:
                    continue
                if not pin_map.get(testname):
                    pin_map[testname] = OrderedDict()
                pin_map.get(testname)[pinname] = OrderedDict()
                lower_bound = self.table.item(row, 2)
                if lower_bound != None:
                    lower_bound = lower_bound.text()
                    if len(lower_bound) > 0:
                        if util.isnumber(lower_bound):
                            pin_map.get(testname)['__lower_bound'] = Decimal(lower_bound)
                        else:
                            raise Exception('%s下限必须为数字' % testname)
                upper_bound = self.table.item(row, 3)
                if upper_bound != None:
                    upper_bound = upper_bound.text()
                    if len(upper_bound) > 0:
                        if util.isnumber(upper_bound):
                            pin_map.get(testname)['__upper_bound'] = Decimal(upper_bound)
                        else:
                            raise Exception('%s上限必须为数字' % testname)
        except Exception as e:
            raise e
        return pin_map

if __name__ == "__main__":
    """ 主方法 """
    app = QApplication(sys.argv)
    __ = TestPinTable()
    __.showMaximized()
    sys.exit(app.exec_())