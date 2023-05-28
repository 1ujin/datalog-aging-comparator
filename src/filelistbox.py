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
from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QStyleFactory, QStyledItemDelegate, QTreeWidgetItemIterator, QFrame, QListWidget, QListWidgetItem, QAbstractItemView, QSpacerItem, QSizePolicy, QFileDialog, QMenu, QAction, QTableWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize

import resource
import util
from table import Table

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
            QListWidget { font-family: \"微软雅黑\"; font-size: 18px; }')
        self.initUI()

    def initUI(self):
        self.folder_list = QListWidget(self)
        self.folder_list.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.folder_list.itemDoubleClicked.connect(lambda item: self.open(item.text()))
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested[QPoint].connect(self.listContextMenuEvent)

        folder_btn = QPushButton('添加路径', self)
        folder_btn.clicked.connect(self.openDir)
        file_btn = QPushButton('添加文件', self)
        file_btn.clicked.connect(self.openFile)
        del_btn = QPushButton('删除', self)
        del_btn.clicked.connect(self.deletePath)
        clr_btn = QPushButton('清空', self)
        clr_btn.clicked.connect(self.clearPath)
        
        folder_btn_layout = QHBoxLayout()
        folder_btn_layout.addWidget(folder_btn)
        folder_btn_layout.addWidget(file_btn)
        folder_btn_layout.addWidget(del_btn)
        folder_btn_layout.addWidget(clr_btn)
        folder_btn_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # folder_btn_layout.addWidget(extract_btn)
        # folder_btn_layout.addWidget(export_btn)

        self.file_list = QListWidget(self)
        self.file_list.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.file_list.itemDoubleClicked.connect(lambda item: self.open(item.text()))
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested[QPoint].connect(self.listContextMenuEvent)
        self.file_list.hide()

        expand_btn = QPushButton(self)
        expand_btn.setToolTip('展开所有文件夹并剔除文件')
        expand_btn.clicked.connect(self.expandAllFile)
        # expand_btn.setStyleSheet('height: 70px; width: 12px;')
        expand_btn.setStyleSheet('height: 18px; width: 100px;')
        expand_btn.setIconSize(QSize(18, 18))
        expand_btn.setIcon(QIcon(':/images/expand.png'))
        file_btn_layout = QVBoxLayout()
        file_btn_layout.addWidget(expand_btn, alignment=Qt.AlignHCenter)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 0, 0)
        folder_btn_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(folder_btn_layout)
        layout.addWidget(self.folder_list, stretch=1)
        layout.addLayout(file_btn_layout)
        layout.addWidget(self.file_list, stretch=3)

    def openDir(self):
        """ 打开选择路径对话框 """
        dir_name = QFileDialog.getExistingDirectory(self, '选择路径')
        if dir_name == '':
            return
        if dir_name not in self.dir_set:
            self.dir_set.add(dir_name)
            QListWidgetItem(dir_name, self.folder_list)
        self.Signal_Row_Count.emit(self.folder_list.count() + self.file_list.count())

    def openFile(self):
        """ 打开文件多选对话框 """
        file_list = set(QFileDialog.getOpenFileNames(self, '选择文件', filter='All Files (*.*);;Text Files (*.txt)', initialFilter='Text Files (*.txt)')[0])
        if len(file_list) == 0:
            return
        for file in file_list:
            if file not in self.file_set:
                self.file_set.add(file)
                QListWidgetItem(file, self.folder_list)
        self.Signal_Row_Count.emit(self.folder_list.count() + self.file_list.count())

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
        self.Signal_Row_Count.emit(self.folder_list.count() + self.file_list.count())

    def clearPath(self):
        """ 清空所有路径 """
        self.dir_set.clear()
        self.file_set.clear()
        self.folder_list.clear()
        self.file_list.clear()
        self.file_list.hide()
        # self.table.hide()
        self.Signal_Row_Count.emit(self.folder_list.count() + self.file_list.count())

    def expandAllFile(self):
        if self.folder_list.count() == 0:
            return
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
        self.Signal_Row_Count.emit(self.folder_list.count() + self.file_list.count())

    def getPathList(self):
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
        return path_list

    def open(self, path):
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


if __name__ == "__main__":
    """ 主方法 """
    QApplication.setStyle(QStyleFactory.create('Fusion'))
    app = QApplication(sys.argv)
    __box = FileListBox()
    __box.show()
    sys.exit(app.exec_())