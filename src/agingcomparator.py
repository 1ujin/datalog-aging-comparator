#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : agingcomparator.py
@Time   : 2023年05月10日
@Desc   : 老炼前后数据比较器
"""

import pdb
import ctypes
import os
import re
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory, QListWidget, QListWidgetItem, QStyledItemDelegate, QGroupBox, QDateEdit, QTimeEdit, QGridLayout, QShortcut, QAbstractItemView, QComboBox, QCheckBox, QTreeWidgetItemIterator, QPlainTextEdit, QStackedLayout, QStackedWidget, QBoxLayout, QToolButton
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence, QIntValidator
from PyQt5.QtCore import Qt, QModelIndex, QSize, QRect, QPropertyAnimation, QSequentialAnimationGroup, pyqtSlot, QMetaObject
if sys.platform == 'win32':
    from PyQt5.QtWinExtras import QWinTaskbarButton

import resource
import util
from testnametree import TestNameTree
from filelistbox import FileListBox
from movablepushbutton import MovablePushButton

class AgingComparator(QMainWindow):
    """docstring for TestNameTree
    测试项树状列表
    """

    def __init__(self, parent=None):
        super(AgingComparator, self).__init__(parent)
        self.parent = parent
        # 剪贴板
        self.clipboard = QApplication.clipboard()
        # self.resize(908, 600)
        # self.setMinimumSize(908, 600)
        self.setWindowTitle("Data Log 老炼前后数据比较工具（适用于J750EX-HD）")
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
            QGroupBox { font-family: \"微软雅黑\" } \
            QListWidget { font-family: \"微软雅黑\"; font-size: 18px; } \
            QTreeWidget { height: 28px; font-family: \"微软雅黑\"; font-size: 18px; } \
            QTreeWidget::branch:has-siblings:!adjoins-item { border-image: url(\":/images/branch-vline.png\") 0; } \
            QTreeWidget::branch:has-siblings:adjoins-item { border-image: url(\":/images/branch-more.png\") 0; } \
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item { border-image: url(\":/images/branch-end.png\") 0; } \
            QTreeWidget::branch:closed:has-children { border-image: none; image: url(\":/images/branch-closed.png\"); } \
            QTreeWidget::branch::open::has-children { border-image: none; image: url(\":/images/branch-opened.png\"); } \
            QCheckBox { height: 28px; font-family: \"微软雅黑\"; margin-left: 10px; } \
            QPlainTextEdit { font-family: \"微软雅黑\"; font-size: 18px; }')
        self.initUI()

    def showEvent(self, evt):
        if sys.platform == 'win32':
            self.taskbar_button = QWinTaskbarButton()
            self.taskbar_progress = self.taskbar_button.progress()
            self.taskbar_progress.show()
            self.taskbar_button.setWindow(self.windowHandle())

    def initUI(self):
        center = QWidget(self)
        
        tab = QTabWidget(center)
        self.testname_tree = TestNameTree(tab)
        self.testname_tree.Signal_Has_Checked.connect(self.switchRunButtion)
        tab.setStyleSheet('QTabWidget:pane { padding: 0px; }')
        tab.setTabPosition(QTabWidget.West)
        tab.addTab(self.testname_tree, '导入测试项')
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.textChanged.connect(self.textChangedHandle)
        self.text_edit.setPlaceholderText('请输入要对比的测试项名称，以逗号隔开，例：\n测试项A Pin1，测试项A Pin2，测试项B Pin3')
        # self.text_edit.setFont(QFont('微软雅黑', 10))
        tab.addTab(self.text_edit, '手动填写测试项')

        self.file_list_before_aging = FileListBox(self)
        self.file_list_before_aging.Signal_Row_Count.connect(self.switchRunButtion)
        # self.file_list_after_aging = FileListBox(self)
        # self.file_list_after_aging.Signal_Row_Count.connect(self.switchRunButtion)
        
        file_list_layout = QHBoxLayout()
        file_list_layout.setContentsMargins(0, 0, 0, 0)
        file_list_layout.addWidget(self.file_list_before_aging)
        # file_list_layout.addWidget(self.file_list_after_aging)

        # run_widget = QWidget(self)
        self.run_btn = MovablePushButton()
        self.run_btn.setToolTip('对比并导出Excel文件')
        self.run_btn.setIconSize(QSize(32, 32))
        self.run_btn.setIcon(QIcon(':/images/export-excel2.png'))
        self.run_btn.setStyleSheet('\
            QPushButton{ \
                border-radius: 35px; \
                width: 70px; \
                height: 70px; \
                background-color: LimeGreen; \
            } \
            QPushButton:enabled:hover{ \
                background-color: lightgreen; \
            } \
            QPushButton:enabled:pressed{ \
                background-color: green; \
            }')
        self.run_btn.clicked.connect(self.file_list_before_aging.exportExcel)
        # self.run_btn.hide()
        
        self.geometry_animation = QPropertyAnimation(self.run_btn, b'geometry')
        self.geometry_animation.setDuration(300)
        self.visible_animation = QPropertyAnimation(self.run_btn, b'visible')
        self.visible_animation.setDuration(1)
        self.visible_animation.setStartValue(True)
        self.visible_animation.setEndValue(False)

        right_layout = QGridLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addLayout(file_list_layout, 0, 0, 9, 16)
        right_layout.addWidget(self.run_btn, 7, 14, alignment=Qt.AlignRight|Qt.AlignBottom)

        main_layout = QHBoxLayout(center)
        main_layout.addWidget(tab, stretch=0)
        main_layout.addLayout(right_layout, stretch=1)
        
        self.setCentralWidget(center)

    def switchRunButtion(self, count):
        return
        if count == 0 or self.runnable() == False:
            if self.run_btn.geometry().y() <= self.geometry().height():
                self.geometry_animation.setStartValue(self.run_btn.geometry())
                self.geometry_animation.setEndValue(QRect(self.run_btn.geometry().x(), self.geometry().height() + 10, self.run_btn.width(), self.run_btn.width()))
                
                self.animation_group = QSequentialAnimationGroup(self)
                self.animation_group.addAnimation(self.geometry_animation)
                self.animation_group.addAnimation(self.visible_animation)
                self.animation_group.start()
        
        elif self.run_btn.geometry().y() > self.geometry().height() or self.run_btn.isVisible() == False:
            self.run_btn.setVisible(True)
            self.geometry_animation.setStartValue(QRect(self.geometry().width() - 150, self.geometry().height(), self.run_btn.width(), self.run_btn.width()))
            self.geometry_animation.setEndValue(QRect(self.geometry().width() - 150, self.geometry().height() - 150, self.run_btn.width(), self.run_btn.width()))
            self.geometry_animation.start()

    def runnable(self):
        if self.file_list_before_aging.file_list.count() == 0:
            return False
        if self.file_list_after_aging.file_list.count() == 0:
            return False
        if len(self.text_edit.toPlainText()) == 0 and not self.testname_tree.isAnySelected():
            return False
        return True

    def compareDatalog(self):
        before_aging = list()
        for row in range(0, self.file_list_before_aging.file_list.count()):
            before_aging.append(self.file_list_before_aging.file_list.item(row).text())
        after_aging = list()
        for row in range(0, self.file_list_after_aging.file_list.count()):
            before_aging.append(self.file_list_after_aging.file_list.item(row).text())
        pass

    def textChangedHandle(self):
        self.switchRunButtion(len(self.sender().toPlainText()))

    def getPinMap(self):
        if self.testname_tree == None:
            return None
        return self.testname_tree.pin_map

    def getRegex(self):
        if self.testname_tree == None:
            return None
        return self.testname_tree.regex

    def getBeginRegex(self):
        if self.testname_tree == None:
            return None
        return self.testname_tree.begin_regex

    def getCheckedPinMap(self):
        if self.testname_tree == None:
            return None
        return self.testname_tree.getCheckedPinMap()


if __name__ == "__main__":
    """ 主方法 """
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("aging_comparator")
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    app = QApplication(sys.argv)
    __main_mindow = AgingComparator()
    __main_mindow.show()
    sys.exit(app.exec_())