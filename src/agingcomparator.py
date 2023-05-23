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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QPushButton, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QMessageBox, QFileDialog, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStyleFactory, QListWidget, QListWidgetItem, QStyledItemDelegate, QGroupBox, QDateEdit, QTimeEdit, QGridLayout, QShortcut, QAbstractItemView, QComboBox, QCheckBox, QTreeWidgetItemIterator, QPlainTextEdit, QStackedLayout, QStackedWidget, QBoxLayout, QToolButton, QSpacerItem, QSplitter
from PyQt5.QtGui import QIcon, QFont, QPixmap, QKeySequence, QIntValidator
from PyQt5.QtCore import Qt, QModelIndex, QSize, QRect, QPropertyAnimation, QSequentialAnimationGroup, pyqtSlot, QMetaObject
if sys.platform == 'win32':
    from PyQt5.QtWinExtras import QWinTaskbarButton

import resource
import util
from testnametree import TestNameTree
from filelistbox import FileListBox
from movablepushbutton import MovablePushButton
from table import Table

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
            self.taskbar_button = QWinTaskbarButton(self)
            self.taskbar_progress = self.taskbar_button.progress()
            self.taskbar_progress.show()
            self.taskbar_button.setWindow(self.windowHandle())

    def initUI(self):
        center = QSplitter(self)
        center.setChildrenCollapsible(False)
        center.setStyleSheet('QSplitter { margin: 11px }')
        
        tab = QTabWidget(center)
        self.testname_tree = TestNameTree(tab)
        self.testname_tree.Signal_Has_Checked.connect(self.switchCompareButtion)
        tab.setStyleSheet('QTabWidget:pane { padding: 0px; }')
        tab.setTabPosition(QTabWidget.West)
        tab.addTab(self.testname_tree, '导入测试项')
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.textChanged.connect(self.textChangedHandle)
        self.text_edit.setPlaceholderText('请输入要对比的测试项名称，以逗号隔开，例：\n测试项A Pin1，测试项A Pin2，测试项B Pin3')
        # self.text_edit.setFont(QFont('微软雅黑', 10))
        tab.addTab(self.text_edit, '手动填写测试项')

        self.file_list_before_aging = FileListBox(self)
        self.file_list_before_aging.Signal_Row_Count.connect(self.switchCompareButtion)
        self.file_list_after_aging = FileListBox(self)
        self.file_list_after_aging.Signal_Row_Count.connect(self.switchCompareButtion)

        self.table = Table(self)

        # run_widget = QWidget(self)
        self.compare_btn = MovablePushButton()
        self.compare_btn.setToolTip('对比并展示表格')
        self.compare_btn.setIconSize(QSize(32, 32))
        self.compare_btn.setIcon(QIcon(':/images/export-excel2.png'))
        self.compare_btn.setIcon(QIcon(':/images/compare.png'))
        self.compare_btn.setStyleSheet('\
            QPushButton { \
                border-radius: 35px; \
                width: 70px; \
                height: 70px; \
                background-color: LimeGreen; \
            } \
            QPushButton:enabled:hover { \
                background-color: lightgreen; \
            } \
            QPushButton:enabled:pressed { \
                background-color: green; \
            }')
        self.compare_btn.clicked.connect(self.compareDatalog)
        self.compare_btn.hide()

        self.excel_btn = MovablePushButton()
        self.excel_btn.setToolTip('导出并打开Excel文件')
        self.excel_btn.setIconSize(QSize(32, 32))
        self.excel_btn.setIcon(QIcon(':/images/export-excel2.png'))
        self.excel_btn.setStyleSheet('\
            QPushButton { \
                border-radius: 35px; \
                width: 70px; \
                height: 70px; \
                background-color: LimeGreen; \
            } \
            QPushButton:enabled:hover { \
                background-color: lightgreen; \
            } \
            QPushButton:enabled:pressed { \
                background-color: green; \
            }')
        self.excel_btn.clicked.connect(self.exportAndOpenExcel)
        self.excel_btn.hide()
        
        self.geometry_animation = QPropertyAnimation(self.compare_btn, b'geometry')
        self.geometry_animation.setDuration(300)
        self.visible_animation = QPropertyAnimation(self.compare_btn, b'visible')
        self.visible_animation.setDuration(1)
        self.visible_animation.setStartValue(True)
        self.visible_animation.setEndValue(False)

        right = QWidget(center)
        self.right_layout = QGridLayout(right)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.addWidget(self.file_list_before_aging, 0, 0, 9, 8)
        self.right_layout.addWidget(self.file_list_after_aging, 0, 8, 9, 8)
        self.right_layout.addWidget(self.compare_btn, 7, 14, alignment=Qt.AlignRight|Qt.AlignBottom)

        table_btn_layout = QHBoxLayout()
        back_btn = QPushButton('返回')
        back_btn.clicked.connect(self.backToFileList)
        export_btn = QPushButton('导出')
        export_btn.clicked.connect(self.exportExcel)
        table_btn_layout.addWidget(back_btn)
        table_btn_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        table_btn_layout.addWidget(export_btn)

        self.table_layout_widget = QWidget(self)
        table_layout = QVBoxLayout(self.table_layout_widget)
        table_layout.setContentsMargins(12, 12, 0, 0)
        table_layout.addLayout(table_btn_layout)
        table_layout.addWidget(self.table)
        self.right_layout.addWidget(self.table_layout_widget, 0, 0, 9, 16)
        self.table_layout_widget.hide()

        center.addWidget(tab)
        center.setStretchFactor(0, 0)
        center.addWidget(right)
        center.setStretchFactor(1, 1)

        self.setCentralWidget(center)

    def switchCompareButtion(self, count):
        if count == 0 or self.comparable() == False:
            if self.compare_btn.geometry().y() <= self.geometry().height():
                self.geometry_animation.setStartValue(self.compare_btn.geometry())
                self.geometry_animation.setEndValue(QRect(self.compare_btn.geometry().x(), self.geometry().height() + 10, self.compare_btn.width(), self.compare_btn.width()))
                
                self.animation_group = QSequentialAnimationGroup(self)
                self.animation_group.addAnimation(self.geometry_animation)
                self.animation_group.addAnimation(self.visible_animation)
                self.animation_group.start()
        
        elif self.compare_btn.geometry().y() > self.geometry().height() or self.compare_btn.isVisible() == False:
            self.compare_btn.setVisible(True)
            self.geometry_animation.setStartValue(QRect(self.geometry().width() - 150, self.geometry().height(), self.compare_btn.width(), self.compare_btn.width()))
            self.geometry_animation.setEndValue(QRect(self.geometry().width() - 150, self.geometry().height() - 150, self.compare_btn.width(), self.compare_btn.width()))
            self.geometry_animation.start()

    def comparable(self):
        if self.file_list_before_aging.file_list.count() == 0:
            return False
        if self.file_list_after_aging.file_list.count() == 0:
            return False
        if len(self.text_edit.toPlainText()) == 0 and not self.testname_tree.isAnySelected():
            return False
        return True

    def compareDatalog(self):
        quit_reply = None
        hasResult = self.table.rowCount() != 0
        if hasResult:
            quit_msgbox = QMessageBox(QMessageBox.Question, "查看对比结果", "是否重新对比并生成结果？")
            quit_msgbox.setWindowIcon(self.logo)
            quit_yesbtn = quit_msgbox.addButton("重新生成", QMessageBox.YesRole)
            quit_nobtn = quit_msgbox.addButton("显示上次结果", QMessageBox.NoRole)
            quit_cancelbtn = quit_msgbox.addButton("取消", QMessageBox.RejectRole)
            quit_msgbox.setDefaultButton(quit_cancelbtn)
            quit_reply = quit_msgbox.exec()

        if quit_reply == 2:
            return
        
        if not hasResult or quit_reply == 0:
            before_aging = list()
            for row in range(0, self.file_list_before_aging.file_list.count()):
                before_aging.append(self.file_list_before_aging.file_list.item(row).text())
            after_aging = list()
            for row in range(0, self.file_list_after_aging.file_list.count()):
                before_aging.append(self.file_list_after_aging.file_list.item(row).text())
            self.table.fillTable(self.file_list_before_aging.getPathList(), self.file_list_after_aging.getPathList(), self.getCheckedPinMap(), self.getRegex(), self.getBeginRegex())
        
        if self.table.rowCount() != 0:
            self.switchToTable()

    def switchToTable(self):
        self.compare_btn.hide()
        self.file_list_before_aging.hide()
        self.file_list_after_aging.hide()
        self.table_layout_widget.show()
        self.right_layout.addWidget(self.excel_btn, 7, 14, alignment=Qt.AlignRight|Qt.AlignBottom)
        self.excel_btn.setGeometry(self.geometry().width() - 150, self.geometry().height() - 150, self.excel_btn.width(), self.excel_btn.height())
        self.excel_btn.show()

    def textChangedHandle(self):
        self.switchCompareButtion(len(self.sender().toPlainText()))

    def switchExcelButtion(self, count):
        pass

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

    def backToFileList(self):
        self.excel_btn.hide()
        self.right_layout.removeWidget(self.excel_btn)
        self.table_layout_widget.hide()
        self.file_list_before_aging.show()
        self.file_list_after_aging.show()
        self.compare_btn.setGeometry(self.geometry().width() - 150, self.geometry().height() - 150, self.compare_btn.width(), self.compare_btn.height())
        self.compare_btn.show()

    def exportExcel(self):
        return self.table.exportExcel()

    def exportAndOpenExcel(self):
        filename = self.exportExcel()
        try:
            if filename and os.path.exists(filename):
                if sys.platform == 'win32':
                    os.startfile(filename)
                elif sys.platform == 'linux':
                    os.system('xdg-open ' + filename)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    """ 主方法 """
    if sys.platform == 'win32':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("aging_comparator")
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    app = QApplication(sys.argv)
    __main_mindow = AgingComparator()
    # __main_mindow.show()
    __main_mindow.showMaximized()
    sys.exit(app.exec_())