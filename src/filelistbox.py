#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : filelistbox.py
@Time   : 2023年05月11日
@Desc   : 文件夹文件选择列表框组件
"""

import pdb
import os
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QStyleFactory, QStyledItemDelegate, QTreeWidgetItemIterator, QFrame, QListWidget, QListWidgetItem, QAbstractItemView, QSpacerItem, QSizePolicy, QFileDialog, QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QCursor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize

import resource
import util

MIN_SIZE = -sys.maxsize - 1

class FileListBox(QWidget):
    """docstring for FileListBox"""
    
    Signal_Row_Count = pyqtSignal(int)

    def __init__(self, parent=None):
        super(FileListBox, self).__init__()
        self.clipboard = QApplication.clipboard()
        self.parent = parent
        self.dir_set = set()
        self.file_set = set()
        # self.setMinimumHeight(800)
        # self.resize(908, 600)
        # self.setMinimumSize(908, 600)
        self.setWindowTitle("文件夹文件选择列表")
        self.logo = QIcon(QPixmap(':/images/logo.png').copy(2, 0, 50, 50))
        self.setWindowIcon(self.logo)
        self.setStyleSheet('\
            QPushButton { font-family: \"微软雅黑\"; } \
            QLabel { height: 28px;  font-family: \"微软雅黑\" } \
            QToolBoxButton { min-width: 150px; min-height: 30px; font-size: 28 } \
            QToolBox::tab { height: 28px; font-family: \"微软雅黑\"; font-size: 28 } \
            QToolBox * { margin: 0px } \
            QToolBar#right_bar { border: none } \
            QToolBar#right_bar QPushButton { width: auto; background-color: green; font-size: 25px } \
            QScrollArea { border: none } \
            QGroupBox { font-family: \"微软雅黑\" } \
            QTreeWidget { height: 28px; font-family: \"微软雅黑\"; font-size: 18px; } \
            QTreeWidget::branch:has-siblings:!adjoins-item { border-image: url(\":/images/branch-vline.png\") 0; } \
            QTreeWidget::branch:has-siblings:adjoins-item { border-image: url(\":/images/branch-more.png\") 0; } \
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item { border-image: url(\":/images/branch-end.png\") 0; } \
            QTreeWidget::branch:closed:has-children { border-image: none; image: url(\":/images/branch-closed.png\"); } \
            QTreeWidget::branch::open::has-children { border-image: none; image: url(\":/images/branch-opened.png\"); } \
            QCheckBox { height: 28px; font-family: \"微软雅黑\"; font-size: 10; margin-left: 10px; } \
            QLineEdit { height: 28px; font-family: \"微软雅黑\"; font-size: 10; }')
        self.initUI()

    def initUI(self):
        self.folder_list = QListWidget(self)
        self.folder_list.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.folder_list.itemDoubleClicked.connect(lambda item: self.open(item.text()))
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested[QPoint].connect(self.listContextMenuEvent)

        folder_btn = QPushButton('添加路径')
        folder_btn.clicked.connect(self.openDir)
        file_btn = QPushButton('添加文件')
        file_btn.clicked.connect(self.openFile)
        del_btn = QPushButton('删除')
        del_btn.clicked.connect(self.deletePath)
        clr_btn = QPushButton('清空')
        clr_btn.clicked.connect(self.clearPath)
        extract_btn = QPushButton('提取')
        extract_btn.clicked.connect(self.fillTable)
        export_btn = QPushButton('导出')
        export_btn.clicked.connect(self.exportExcel)
        
        folder_btn_layout = QHBoxLayout()
        folder_btn_layout.addWidget(folder_btn)
        folder_btn_layout.addWidget(file_btn)
        folder_btn_layout.addWidget(del_btn)
        folder_btn_layout.addWidget(clr_btn)
        folder_btn_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        folder_btn_layout.addWidget(extract_btn)
        folder_btn_layout.addWidget(export_btn)

        self.file_list = QListWidget(self)
        self.file_list.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.file_list.itemDoubleClicked.connect(lambda item: self.open(item.text()))
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested[QPoint].connect(self.listContextMenuEvent)
        self.file_list.hide()

        self.table = QTableWidget(0, 0, self)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.hide()

        expand_btn = QPushButton()
        expand_btn.setToolTip('展开所有文件夹并剔除文件')
        expand_btn.clicked.connect(self.expandAllFile)
        expand_btn.setStyleSheet('height: 70px; width: 12px;')
        expand_btn.setIconSize(QSize(12, 12))
        expand_btn.setIcon(QIcon(':/images/expand-right.png'))
        file_btn_layout = QVBoxLayout()
        file_btn_layout.addWidget(expand_btn, alignment=Qt.AlignHCenter)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.folder_list)
        top_layout.addLayout(file_btn_layout)
        top_layout.addWidget(self.file_list)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(6)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 0, 0)
        # folder_btn_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(folder_btn_layout)
        # layout.addWidget(self.folder_list, stretch=1)
        layout.addLayout(top_layout, stretch=1)
        # layout.addLayout(file_btn_layout)
        # layout.addWidget(self.file_list, stretch=3)
        layout.addWidget(self.table, stretch=3)

    def openDir(self):
        """ 打开选择路径对话框 """
        dir_name = QFileDialog.getExistingDirectory(self, '选择路径')
        if dir_name == '':
            return
        if dir_name not in self.dir_set:
            self.dir_set.add(dir_name)
            QListWidgetItem(dir_name, self.folder_list)

    def openFile(self):
        """ 打开文件多选对话框 """
        file_list = set(QFileDialog.getOpenFileNames(self, '选择文件', filter='All Files (*.*);;Text Files (*.txt)', initialFilter='Text Files (*.txt)')[0])
        if len(file_list) == 0:
            return
        for file in file_list:
            if file not in self.file_set:
                self.file_set.add(file)
                QListWidgetItem(file, self.folder_list)

    def deletePath(self):
        """ 删除所选的路径 """
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        for item in self.folder_list.selectedItems():
            text = item.text()
            if text in self.dir_set or text in self.file_set:
                self.dir_set.discard(text)
                self.file_set.discard(text)
            self.folder_list.takeItem(self.folder_list.row(item))
        self.Signal_Row_Count.emit(self.file_list.count())

    def clearPath(self):
        """ 清空所有路径 """
        self.dir_set.clear()
        self.file_set.clear()
        self.folder_list.clear()
        self.file_list.clear()
        self.file_list.hide()
        self.table.hide()
        self.Signal_Row_Count.emit(self.file_list.count())

    def expandAllFile(self):
        path_set = set()
        for row in range(0, self.file_list.count()):
            path_set.add(self.file_list.item(row).text())
        path_set.update(self.file_set)
        for folder in self.dir_set:
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    path_set.add(os.path.join(root, name).replace('\\', '/'))
        path_list = list(path_set)
        path_list.sort(key=lambda x: os.path.basename(x) + os.path.dirname(x))
        self.file_list.clear()
        for path in path_list:
            if os.path.splitext(path)[1].lower() == '.txt':
                QListWidgetItem(path, self.file_list)
        self.file_list.show()
        self.Signal_Row_Count.emit(self.file_list.count())

    def extractDataToDict(self):
        # 所有路径
        path_list = list()
        if self.file_list.count() == 0:
            path_set = set()
            path_set.update(self.file_set)
            for folder in self.dir_set:
                for root, dirs, files in os.walk(folder, topdown=False):
                    for name in files:
                        path_set.add(os.path.join(root, name).replace('\\', '/'))
            path_list.extend(path_set)
        else:
            for row in range(0, self.file_list.count()):
                path_list.append(self.file_list.item(row).text())
        path_list.sort()
        
        # 解析文件名并分类
        path_dict = OrderedDict()
        id_error = list()
        duplicate_error = list()
        temperature_error = list()
        
        for path in path_list:
            # 提取编号
            basename = os.path.basename(path)
            matcher = re.match(r'^([0-9]+)(_(?i)failed)?\.(?i)txt', basename)
            chip_id = None
            if matcher:
                chip_id = matcher.groups()[0]
            else:
                id_error.append(path)
                continue
            if not path_dict.get(chip_id):
                path_dict[chip_id] = dict()
            
            chip_dict = path_dict[chip_id]
            
            # 提取温度
            dirname = os.path.dirname(path)
            if path.upper().find('LAOLIANQIAN') > -1:
                # 老炼前
                if chip_dict.get('before_aging'):
                    duplicate_error.append(path)
                    continue
                chip_dict['before_aging'] = path
            elif path.upper().find('LAOLIANHOU') > -1:
                # 老炼后
                temperature = os.path.basename(dirname)
                matcher = re.match(r'(-55|-40|0|25|85|105|125)', temperature)
                if matcher:
                    temperature = int(matcher.groups()[0])
                else:
                    temperature_error.append(path)
                    continue
                if not chip_dict.get('after_aging'):
                    chip_dict['after_aging'] = dict()
                after_aging_dict = chip_dict['after_aging']
                if after_aging_dict.get(temperature):
                    duplicate_error.append(path)
                else:
                    after_aging_dict[temperature] = path

        compare_dict = OrderedDict()
        pin_map = self.parent.getCheckedPinMap()
        for testname in pin_map.keys():
            compare_dict[testname] = dict()
        regex = self.parent.getRegex()
        begin_regex = self.parent.getBeginRegex()
        for path_item in path_dict.items():
            chip_id = path_item[0]

            # 老炼前
            before_path = path_item[1].get('before_aging')
            if not before_path:
                continue
            # 读取文件
            with open(before_path, 'r') as f:
                line = f.readline()
                while line != None and len(line) > 0:
                    if re.match(begin_regex, line):
                        break
                    line = f.readline()
                line = f.readline()
                while line != None and len(line) > 0:
                    matcher = re.match(regex, line)
                    if matcher:
                        group = matcher.groups()
                        testname = group[3].strip()
                        pinname = group[4].strip()
                        # 匹配测试项
                        testname_dict = pin_map.get(testname)
                        compare_testname_dict = compare_dict.get(testname)
                        if testname_dict != None and compare_testname_dict != None:
                            if compare_testname_dict.get(chip_id) == None:
                                compare_testname_dict[chip_id] = dict()
                            compare_chip_dict = compare_testname_dict.get(chip_id)
                            # 匹配Pin
                            pinname_dict = testname_dict.get(pinname)
                            if pinname_dict != None:
                                if compare_chip_dict.get(pinname) == None:
                                    compare_chip_dict[pinname] = OrderedDict()
                                compare_pin_dict = compare_chip_dict.get(pinname)
                                val = group[7].strip()
                                if val.find('n') > -1:
                                    val = Decimal(val.split(' ')[0])
                                elif val.find('u') > -1:
                                    val = Decimal(val.split(' ')[0]) * 1000
                                elif val.find('m') > -1:
                                    val = Decimal(val.split(' ')[0]) * 1000 * 1000
                                else:
                                    val = Decimal(val.split(' ')[0]) * 1000 * 1000 * 1000
                                compare_pin_dict[MIN_SIZE] = val
                                pinname_dict[MIN_SIZE] = True
                    line = f.readline()
            
            # 老炼后
            after_item = path_item[1].get('after_aging')
            if not after_item:
                continue
            for temperature_item in after_item.items():
                # 循环温度
                after_temperature, after_temperature_path = temperature_item
                # 读取文件
                with open(after_temperature_path, 'r') as f:
                    line = f.readline()
                    while line != None and len(line) > 0:
                        if re.match(begin_regex, line):
                            break
                        line = f.readline()
                    line = f.readline()
                    while line != None and len(line) > 0:
                        matcher = re.match(regex, line)
                        if matcher:
                            group = matcher.groups()
                            testname = group[3].strip()
                            pinname = group[4].strip()
                            # 匹配测试项
                            testname_dict = pin_map.get(testname)
                            if not compare_dict.get(testname):
                                compare_dict[testname] = OrderedDict()
                            compare_testname_dict = compare_dict.get(testname)
                            if testname_dict != None and compare_testname_dict != None:
                                if compare_testname_dict.get(chip_id) == None:
                                    compare_testname_dict[chip_id] = dict()
                                compare_chip_dict = compare_testname_dict.get(chip_id)
                                # 匹配Pin
                                pinname_dict = testname_dict.get(pinname)
                                if pinname_dict != None:
                                    if compare_chip_dict.get(pinname) == None:
                                        compare_chip_dict[pinname] = OrderedDict()
                                    compare_pin_dict = compare_chip_dict.get(pinname)
                                    val = group[7].strip()
                                    if val.find('n') > -1:
                                        val = Decimal(val.split(' ')[0])
                                    elif val.find('u') > -1:
                                        val = Decimal(val.split(' ')[0]) * 1000
                                    elif val.find('m') > -1:
                                        val = Decimal(val.split(' ')[0]) * 1000 * 1000
                                    else:
                                        val = Decimal(val.split(' ')[0]) * 1000 * 1000 * 1000
                                    compare_pin_dict[after_temperature] = val
                                    pinname_dict[after_temperature] = True
                        line = f.readline()
        return (compare_dict, pin_map, path_dict, id_error, temperature_error, duplicate_error)

    def fillTable(self):
        if len(self.parent.getCheckedPinMap()) == 0:
            QMessageBox.warning(self, "提示", "请勾选至少一个测试项！")
            return

        if self.folder_list.count() + self.file_list.count() == 0:
            QMessageBox.warning(self, "提示", "请选择至少一个文件！")
            return
        
        compare_dict, pin_map, path_dict, id_error, temperature_error, duplicate_error = self.extractDataToDict()

        if len(path_dict) == 0:
            QMessageBox.warning(self, "提示", "请选择至少一个有效的Datalog！")
            return

        try:
            self.table.clear()
            self.table.setRowCount(3)
            self.table.setColumnCount(0)
            
            col = 0
            for testname_item in pin_map.items():
                # 循环测试项
                testname, pin_dict = testname_item

                # 表头
                temp_set = set()
                for pin_value in pin_dict.values():
                    temp_set.update(pin_value.keys())
                temp_list = list(temp_set)
                temp_list.sort()
                for i in range(len(temp_set) * 3):
                    self.table.insertColumn(self.table.columnCount())
                current_w = 0
                self.table.setSpan(0, col + current_w, 1, len(temp_set) * 3)
                self.table.setItem(0, col + current_w, self.getTableItem(testname))
                current_w += 2
                self.table.setItem(1, col + current_w, self.getTableItem('老炼前'))
                self.table.setItem(2, col + current_w, self.getTableItem('常温'))
                current_w += 1
                if len(temp_set) > 1:
                    self.table.setSpan(1, col + current_w, 1, (len(temp_set) - 1) * 3)
                    self.table.setItem(1, col + current_w, self.getTableItem('老炼后'))
                    for temp in temp_list[1:]:
                        self.table.setItem(2, col + current_w, self.getTableItem(temp))
                        current_w += 1
                        self.table.setItem(2, col + current_w, self.getTableItem('变化值'))
                        current_w += 1
                        self.table.setItem(2, col + current_w, self.getTableItem('变化百分比'))
                        current_w += 1

                # 测试结果
                compare_testname_dict = compare_dict.get(testname)
                if not compare_testname_dict:
                    continue
                row = 3
                max_w = 0
                for compare_chip_item in compare_testname_dict.items():
                    # 循环芯片
                    chip_id, compare_pin_dict = compare_chip_item
                    current_h = 0
                    for pin_item in pin_dict.items():
                        # 循环Pin
                        current_w = 1
                        pinname, temperature = pin_item
                        if row + current_h >= self.table.rowCount():
                            self.table.insertRow(self.table.rowCount())
                        self.table.setItem(row + current_h, col + current_w, self.getTableItem(pinname))
                        current_w += 1
                        compare_temp_dict = compare_pin_dict.get(pinname)
                        if not compare_temp_dict:
                            continue
                        # Pin
                        if row + current_h >= self.table.rowCount():
                            self.table.insertRow(self.table.rowCount())
                        self.table.setItem(row + current_h, col + current_w, self.getTableItem(pinname))
                        # 老炼前
                        before_val = compare_temp_dict.get(MIN_SIZE)
                        self.table.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(before_val)))
                        current_w += 1
                        for compare_temp_item in compare_temp_dict.items():
                            # 循环温度
                            temperature, test_val = compare_temp_item
                            if temperature != MIN_SIZE:
                                # 老炼后
                                self.table.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(test_val)))
                                current_w += 1
                                diff = test_val - before_val
                                self.table.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(diff)))
                                current_w += 1
                                percent = self.convertDecimal(diff * 100 / before_val).quantize(Decimal("0.00")).normalize()
                                self.table.setItem(row + current_h, col + current_w, self.getTableItem(str(percent) + '%'))
                                current_w += 1
                        max_w = max(max_w, current_w)
                        current_h += 1
                    # 芯片编号
                    self.table.setItem(row, col, self.getTableItem(chip_id, Qt.AlignHCenter|Qt.AlignTop))
                    self.table.setSpan(row, col, current_h, 1)
                    row += current_h
                col += max_w
        
        except Exception as e:
            print(e)
        
        self.table.show()

    def getTableItem(self, text, alignment=Qt.AlignHCenter|Qt.AlignVCenter):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(alignment)
        return item


    def convertDecimal(self, val):
        if val == 0:
            return Decimal(0)
        elif val == val.to_integral():
            val = val.to_integral()
        else:
            val = val.normalize()
        return val

    def open(self, path):
        print(path)
        if os.path.exists(path):
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'linux':
                os.system('xdg-open ' + path)

    def listContextMenuEvent(self, pos):
        sender = self.sender()
        hitIndex = sender.indexAt(pos).row()
        if hitIndex > -1:
            path = sender.currentItem().text()
            menu = QMenu(sender)
            open_file_action = QAction("打开", menu)
            open_file_action.triggered.connect(lambda: self.open(path))
            menu.addAction(open_file_action)
            open_folder_action = QAction("打开所在文件夹", menu)
            open_folder_action.triggered.connect(lambda: self.open(os.path.split(path)[0]))
            menu.addAction(open_folder_action)
            copy_action = QAction("复制路径", menu)
            copy_action.triggered.connect(lambda: self.clipboard.setText(path))
            menu.addAction(copy_action)
            del_action = QAction("删除", menu)
            del_action.triggered.connect(lambda: self.deletePath())
            menu.addAction(del_action)
            menu.exec_(QCursor.pos())

    def exportExcel(self):
        filename = QFileDialog.getSaveFileName(self, '导出表格', filter='Excel Files (*.xlsx *.xls)')[0]
        if filename == '':
            return
        util.exportExcel(self.table, filename)


if __name__ == "__main__":
    """ 主方法 """
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    app = QApplication(sys.argv)
    __box = FileListBox()
    __box.show()
    sys.exit(app.exec_())