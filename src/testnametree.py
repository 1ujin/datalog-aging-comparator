#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : testnametree.py
@Time   : 2023年05月08日
@Desc   : 测试项树状列表
"""

import pdb
import os
import re
import sys
from collections import OrderedDict
from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QStyleFactory, QStyledItemDelegate, QTreeWidgetItemIterator, QFrame, QSpacerItem, QSizePolicy, QLineEdit, QAbstractItemView
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

import resource
from formatdialog import FormatDialog

TEST_NAME_PIN_REGEX = r'\ (.{11})(.{6})(.{9})(.{26})(.{11})(.{10})((.{15}){4})(.{3})\s+'

class TreeNode(object):
    """docstring for TreeNode"""

    def __init__(self, name: str, values: OrderedDict, children: OrderedDict):
        self.name = name
        self.values = values
        self.children = children

    def __str__(self):
        if self.children == None or len(self.children) == 0:
            return(f'{{ name: {self.name} }}')
        else:
            return(f'{{ name: {self.name}, children: {", ".join([str(child) for child in self.children.values()])} }}')


class UneditableDelegate(QStyledItemDelegate):
    """docstring for FullSizedDelegate
    禁止编辑委派类
    """

    @staticmethod
    def createEditor(parent, option, index):
        """ 忽略编辑，如果有子节点则折叠 """
        if index.child(0, 0).data() is not None:
            item = parent.parent().topLevelItem(index.row())
            item.setExpanded(not item.isExpanded())


class FullSizedDelegate(QStyledItemDelegate):
    """docstring for FullSizedDelegate
    自动调整宽度委派类
    """

    @staticmethod
    def updateEditorGeometry(parent, option, index):
        if index.column() != 5:
            parent.setGeometry(option.rect)


class TestNameTree(QWidget):
    """docstring for TestNameTree
    测试项树状列表
    """

    Signal_Has_Checked = pyqtSignal(int)

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.tree = QTreeWidget()
        self.tree_iterator = None
        self.tree_item_count = 0
        self.pin_map = None
        self.regex = None
        self.begin_regex = None
        # self.setMinimumHeight(800)
        # self.resize(908, 600)
        # self.setMinimumSize(908, 600)
        self.setWindowTitle("测试项树状列表")
        self.logo = QIcon(QPixmap(':/images/logo.png').copy(2, 0, 50, 50))
        self.setWindowIcon(self.logo)
        self.setStyleSheet('\
            QPushButton { font-family: \"微软雅黑\"; max-width: 50px; } \
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
            QTreeWidget::branch::open::has-children { border-image: none; image: url(\":/images/branch-opened.png\"); }')
        self.initUI()

    def initUI(self):
        load_btn = QPushButton('导入')
        load_btn.clicked.connect(self.load)
        select_all_btn = QPushButton('全选')
        select_all_btn.clicked.connect(self.selectAllTreeItem)
        reverse_selected_btn = QPushButton('反选')
        reverse_selected_btn.clicked.connect(self.reverseSelectedTreeItem)
        clear_selected_btn = QPushButton('清空')
        clear_selected_btn.clicked.connect(self.clearSelectedTreeItem)
        expand_btn = QPushButton('展开')
        collapse_btn = QPushButton('折叠')
        search_btn = QPushButton('查找')
        
        btn_layout = QHBoxLayout()
        btn_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(reverse_selected_btn)
        btn_layout.addWidget(clear_selected_btn)
        btn_layout.addWidget(expand_btn)
        btn_layout.addWidget(collapse_btn)
        btn_layout.addWidget(search_btn)
        # btn_layout.setSpacing(0)
        # btn_layout.setContentsMargins(0, 0, 0, 0)

        search_line_edit = QLineEdit()
        search_line_edit.setStyleSheet('font-size: 18px;')
        search_line_edit.setPlaceholderText('请输入关键字')
        search_line_edit.returnPressed.connect(self.searchItemByKeyword)
        prev_item_btn = QPushButton('上一个')
        prev_item_btn.clicked.connect(lambda: self.searchPreviousItemByKeyword(search_line_edit.text()))
        next_item_btn = QPushButton('下一个')
        next_item_btn.clicked.connect(lambda: self.searchNextItemByKeyword(search_line_edit.text()))
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(search_line_edit)
        search_layout.addWidget(prev_item_btn)
        search_layout.addWidget(next_item_btn)

        self.search_frame = QFrame()
        self.search_frame.setLayout(search_layout)
        self.search_frame.hide()
        search_btn.clicked.connect(lambda: self.search_frame.setVisible(not self.search_frame.isVisible()))

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: lightgray")

        # 选项树
        self.tree = QTreeWidget()
        expand_btn.clicked.connect(self.tree.expandAll)
        collapse_btn.clicked.connect(self.tree.collapseAll)
        self.tree.itemClicked.connect(self.treeClickedHandle)
        self.tree.header().setSectionsMovable(False)
        self.tree.setHeaderLabel('Test Name 〉Pin')
        self.tree.setHeaderHidden(True)
        # self.tree.addTopLevelItems([self.generateTreeByDfs(top) for top in self.loadTestName('../../data_log_splitter/data/tar/00100.txt').items()])
        # self.tree.addTopLevelItems([self.generateTreeByDfs(top) for top in self.loadTestName('../data/QFP44_qian.txt').items()])
        # 展开全部
        # self.tree.expandAll()
        # 首列宽度自适应
        self.tree.resizeColumnToContents(0)
        # 自动调整宽度
        self.tree.setItemDelegate(FullSizedDelegate(self.tree))
        # 不可编辑
        self.tree.setItemDelegateForColumn(0, UneditableDelegate(self.tree))
        # self.tree.setStyleSheet('QTreeWidget { border-top: none; }')
        layout = QVBoxLayout()
        # layout.setSpacing(0)
        # layout.setContentsMargins(0, 0, 0, 0)
        # btn_layout.setSpacing(7)
        # btn_layout.setContentsMargins(12, 12, 12, 12)
        layout.setContentsMargins(0, 12, 0, 0)
        btn_layout.setContentsMargins(8, 0, 12, 0)
        search_layout.setContentsMargins(12, 0, 12, 0)
        layout.addLayout(btn_layout)
        # layout.addLayout(search_layout)
        layout.addWidget(self.search_frame)
        # layout.addWidget(line)
        layout.addWidget(self.tree)
        # tab1 = QWidget()
        # tab1.setLayout(layout)
        # tab = QTabWidget()
        # tab.setTabPosition(QTabWidget.West)
        # tab.addTab(tab1, '导入测试项')
        # tab.addTab(QWidget(), '手动填写测试项')
        # self.setCentralWidget(tab)
        self.setLayout(layout)
    
    def load(self):
        """ 打开配置对话框并导入测试项 """
        dialog = FormatDialog(self)
        dialog.Signal_Pin_Dict.connect(self.generateTree)
        dialog.open()
        dialog.resize(dialog.height() / 1.5, dialog.height())
        dialog.exec_()

    def selectAllTreeItem(self):
        """ 全选 """
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.NotChecked)
        while it.value():
            if it.value().childCount() == 0:
                it.value().setCheckState(0, Qt.Checked)
            it.__iadd__(1)

    def reverseSelectedTreeItem(self):
        """ 反选 """
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.All)
        while it.value():
            if it.value().childCount() == 0:
                if it.value().checkState(0) == Qt.Checked:
                    it.value().setCheckState(0, Qt.Unchecked)
                elif it.value().checkState(0) == Qt.Unchecked:
                    it.value().setCheckState(0, Qt.Checked)
            it.__iadd__(1)

    def clearSelectedTreeItem(self):
        """ 清空 """
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while it.value():
            if it.value().childCount() == 0:
                it.value().setCheckState(0, Qt.Unchecked)
            it.__iadd__(1)

    def isAnySelected(self):
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while it.value():
            return True
        return False

    def treeClickedHandle(self, item, column):
        if self.isAnySelected():
            self.Signal_Has_Checked.emit(1)
        else:
            self.Signal_Has_Checked.emit(0)

    def getAllPin(self):
        pin_list = list()
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.All)
        while it.value():
            if it.value().childCount() == 0 and it.value().checkState(0) == Qt.Checked:
                pin = list()
                child = it.value()
                while child:
                    pin.insert(0, child.text(0))
                    child = child.parent()
                pin_list.append(pin)
            it.__iadd__(1)
        return pin_list

    def getCheckedPinMap(self):
        pin_map = OrderedDict()
        it = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.Checked)
        while it.value():
            if it.value().childCount() == 0:
                testname = it.value().parent().text(0)
                pinname = it.value().text(0)
                if not pin_map.get(testname):
                    pin_map[testname] = OrderedDict()
                pin_map.get(testname)[pinname] = OrderedDict()
            it.__iadd__(1)
        return pin_map

    def generateTree(self, pin_map):
        self.pin_map = pin_map
        self.tree.clear()
        self.tree_item_count = 0
        self.tree.addTopLevelItems([self.generateTreeByDfs(top, self.tree) for top in pin_map.items()])

    def searchItemByKeyword(self, keyword=None):
        if not keyword:
            sender = self.sender()
            keyword = sender.text()
        self.searchNextItemByKeyword(keyword)

    def searchPreviousItemByKeyword(self, keyword):
        words = re.split(r'\s+', keyword.strip())
        if not self.tree_iterator or not self.tree_iterator.value():
            self.tree_iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.All)
            for i in range(0, self.tree_item_count - 1):
                self.tree_iterator.__iadd__(1)
        while self.tree_iterator.value():
            text = self.tree_iterator.value().text(0)
            for word in words:
                if text.find(word) > -1:
                    self.tree.scrollToItem(self.tree_iterator.value(), QAbstractItemView.PositionAtTop)
                    self.tree_iterator.value().setSelected(True)
                    self.tree_iterator.__isub__(1)
                    return
            self.tree_iterator.__isub__(1)

    def searchNextItemByKeyword(self, keyword):
        words = re.split(r'\s+', keyword.strip())
        if not self.tree_iterator or not self.tree_iterator.value():
            self.tree_iterator = QTreeWidgetItemIterator(self.tree, QTreeWidgetItemIterator.All)
        while self.tree_iterator.value():
            text = self.tree_iterator.value().text(0)
            for word in words:
                if text.find(word) > -1:
                    self.tree.scrollToItem(self.tree_iterator.value(), QAbstractItemView.PositionAtTop)
                    self.tree_iterator.value().setSelected(True)
                    self.tree_iterator.__iadd__(1)
                    return
            self.tree_iterator.__iadd__(1)

    def generateTreeByDfs(self, values, parent):
        def dfs(values, parent):
            root = QTreeWidgetItem(parent)
            self.tree_item_count += 1
            root.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            root.setText(0, values[0])
            root.setCheckState(0, Qt.Unchecked)
            if values[1]:
                for child in values[1].items():
                    dfs(child, root)
            return root
        return dfs(values, parent)

    @staticmethod
    def loadTestName(filename, regex=None):
        pin_map = OrderedDict()
        current_regex = TEST_NAME_PIN_REGEX
        if regex:
            current_regex = regex
        with open(filename, 'r', encoding='utf-8') as f:
            line = f.readline()
            while line != None and len(line) > 0:
                matcher = re.match(current_regex, line)
                if matcher:
                    groups = matcher.groups()
                    if groups[0].strip().isdigit():
                        testname = groups[3].strip()
                        pin = groups[4].strip()
                        if not pin_map.get(testname):
                            pin_map[testname] = OrderedDict()
                        pin_map.get(testname)[pin] = OrderedDict()
                line = f.readline()
        return pin_map

    @staticmethod
    def getTreeValues(tree):
        def getTreeItemValues(item: QTreeWidgetItem, columns: list) -> OrderedDict:
            if item == None:
                return
            value_map = OrderedDict()
            for v_idx, k in enumerate(columns):
                v = item.text(v_idx)
                value_map[k] = v
            return value_map

        def dfs(root: QTreeWidgetItem, columns: list) -> TreeNode:
            """ 深度优先搜索 """
            if root == None:
                return
            if root.checkState(0) == Qt.Unchecked:
                return
            name = root.text(0)
            values = getTreeItemValues(root, columns)
            children = OrderedDict()
            for i in range(0, root.childCount()):
                child = dfs(root.child(i), columns)
                if child == None:
                    continue
                for root_val_k in values:
                    if root_val_k not in child.values.keys() or child.values[root_val_k] == '':
                        # 子节点继承父节点的值
                        child.values[root_val_k] = values.get(root_val_k)
                children[child.name] = child
            return TreeNode(name, values, children)

        columns = [tree.headerItem().text(x) for x in range(0, tree.header().count())]
        tree_map = OrderedDict()
        for i in range(0, tree.topLevelItemCount()):
            top = tree.topLevelItem(i)
            if top.checkState(0) == Qt.Unchecked:
                continue
            root = dfs(top, columns)
            tree_map[root.name] = root
        return tree_map


if __name__ == "__main__":
    """ 主方法 """
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    app = QApplication(sys.argv)
    __tree = TestNameTree()
    __tree.show()
    sys.exit(app.exec_())