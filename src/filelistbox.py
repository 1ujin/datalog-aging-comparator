#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : filelistbox.py
@Time   : 2023年05月11日
@Desc   : 文件夹文件选择列表框组件
"""

import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QStyleFactory, QListWidget, \
    QListWidgetItem, QAbstractItemView, QSpacerItem, QSizePolicy, QFileDialog, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QTransform
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize

import resource  # pylint: disable=unused-import

MIN_SIZE = -sys.maxsize - 1


class FileListBox(QWidget):
    """docstring for FileListBox"""

    signal_row_count = pyqtSignal(int)

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
        self.logo = QIcon(QPixmap(":/images/logo.png").copy(2, 0, 50, 50))
        self.setWindowIcon(self.logo)
        self.setStyleSheet("\
            QPushButton { font-family: \"微软雅黑\"; } \
            QListWidget { font-family: \"微软雅黑\"; font-size: 18px; }")
        self.init_ui()

    def init_ui(self):
        self.folder_list = QListWidget(self)
        self.folder_list.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.folder_list.itemDoubleClicked.connect(lambda item: self.open(item.text()))
        self.folder_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_list.customContextMenuRequested[QPoint].connect(self.list_context_menu_event)

        folder_btn = QPushButton("添加路径", self)
        folder_btn.clicked.connect(self.open_dir)
        file_btn = QPushButton("添加文件", self)
        file_btn.clicked.connect(self.open_file)
        del_btn = QPushButton("删除", self)
        del_btn.clicked.connect(self.delete_path)
        clr_btn = QPushButton("清空", self)
        clr_btn.clicked.connect(self.clear_path)

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
        self.file_list.customContextMenuRequested[QPoint].connect(self.list_context_menu_event)
        self.file_list.hide()

        self.expand_btn = QPushButton(self)
        self.expand_btn.setToolTip("展开所有文件夹并剔除文件")
        self.expand_btn.clicked.connect(self.expand_all_file)
        # self.expand_btn.setStyleSheet("height: 70px; width: 12px;")
        self.expand_btn.setStyleSheet("height: 18px; width: 100px;")
        self.expand_btn.setIconSize(QSize(18, 18))
        pixmap = QPixmap(":/images/expand.png")
        transform = QTransform()
        transform.rotate(180)
        pixmap = pixmap.transformed(transform)
        self.expand_btn.setIcon(QIcon(pixmap))

        file_btn_layout = QVBoxLayout()
        file_btn_layout.addWidget(self.expand_btn, alignment=Qt.AlignHCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 0, 0)
        folder_btn_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(folder_btn_layout)
        layout.addWidget(self.folder_list, stretch=1)
        layout.addLayout(file_btn_layout)
        layout.addWidget(self.file_list, stretch=3)

    def open_dir(self):
        """ 打开选择路径对话框 """
        dir_name = QFileDialog.getExistingDirectory(self, "选择路径")
        if dir_name == "":
            return
        if dir_name not in self.dir_set:
            self.dir_set.add(dir_name)
            QListWidgetItem(dir_name, self.folder_list)
        self.signal_row_count.emit(self.folder_list.count() + self.file_list.count())

    def open_file(self):
        """ 打开文件多选对话框 """
        file_list = set(QFileDialog.getOpenFileNames(self, "选择文件", filter="All Files (*.*);;Text Files (*.txt)",
                                                     initialFilter="Text Files (*.txt)")[0])
        if len(file_list) == 0:
            return
        for file in file_list:
            if file not in self.file_set:
                self.file_set.add(file)
                QListWidgetItem(file, self.folder_list)
        self.signal_row_count.emit(self.folder_list.count() + self.file_list.count())

    def delete_path(self):
        """ 删除所选的路径 """
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))
        for item in self.folder_list.selectedItems():
            text = item.text()
            if text in self.dir_set or text in self.file_set:
                self.dir_set.discard(text)
                self.file_set.discard(text)
            self.folder_list.takeItem(self.folder_list.row(item))
        self.signal_row_count.emit(self.folder_list.count() + self.file_list.count())

    def clear_path(self):
        """ 清空所有路径 """
        self.dir_set.clear()
        self.file_set.clear()
        self.folder_list.clear()
        self.file_list.clear()
        self.file_list.hide()
        # self.table.hide()
        self.signal_row_count.emit(self.folder_list.count() + self.file_list.count())

    def expand_all_file(self):
        if not self.file_list.isHidden():
            icon = self.expand_btn.icon()
            pixmap = icon.pixmap(self.expand_btn.iconSize())
            transform = QTransform()
            transform.rotate(180)
            pixmap = pixmap.transformed(transform)
            icon.addPixmap(pixmap)
            self.expand_btn.setIcon(icon)
            self.file_list.hide()
            return
        if self.folder_list.count() == 0:
            return
        path_set = set()
        for row in range(0, self.file_list.count()):
            path_set.add(self.file_list.item(row).text())
        path_set.update(self.file_set)
        for folder in self.dir_set:
            for root, _, files in os.walk(folder, topdown=False):
                for name in files:
                    path_set.add(os.path.join(root, name).replace("\\", "/"))
        path_list = list(path_set)
        path_list.sort(key=lambda x: os.path.basename(x) + os.path.dirname(x))
        self.file_list.clear()
        for path in path_list:
            if os.path.splitext(path)[1].lower() == ".txt":
                QListWidgetItem(path, self.file_list)
        icon = self.expand_btn.icon()
        pixmap = icon.pixmap(self.expand_btn.iconSize())
        transform = QTransform()
        transform.rotate(180)
        pixmap = pixmap.transformed(transform)
        icon.addPixmap(pixmap)
        self.expand_btn.setIcon(icon)
        self.file_list.show()
        self.signal_row_count.emit(self.folder_list.count() + self.file_list.count())

    def get_path_list(self):
        path_list = list()
        if self.file_list.count() == 0:
            path_set = set()
            path_set.update(self.file_set)
            for folder in self.dir_set:
                for root, _, files in os.walk(folder, topdown=False):
                    for name in files:
                        path_set.add(os.path.join(root, name).replace("\\", "/"))
            path_list.extend(path_set)
        else:
            for row in range(0, self.file_list.count()):
                path_list.append(self.file_list.item(row).text())
        path_list.sort()
        return path_list

    @staticmethod
    def open(path):
        if os.path.exists(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "linux":
                os.system("xdg-open " + path)

    def list_context_menu_event(self, pos):
        sender: QListWidget = self.sender()
        hit_index = sender.indexAt(pos).row()
        if hit_index > -1:
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
            del_action.triggered.connect(self.delete_path)
            menu.addAction(del_action)
            menu.exec_(QCursor.pos())


if __name__ == "__main__":
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)
    __box = FileListBox()
    __box.show()
    sys.exit(app.exec_())
