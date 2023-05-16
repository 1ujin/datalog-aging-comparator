#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : formatdialog.py
@Time   : 2023年05月09日
@Desc   : 格式对话框
"""

import pdb
import re
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QFormLayout, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QMessageBox, QGroupBox, QFormLayout, QFileDialog
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal

import resource

COLUMN_NAME = ['Number', 'Site', 'Result', r'Test\ Name', 'Pin', 'Channel', 'Low', 'Measured', 'High', 'Force', 'Loc']

class FormatDialog(QDialog):
    """docstring for FormatDialog"""
    
    column_width = [11, 6, 9, 26, 12, 10, 15, 15, 15, 15, 3]
    Signal_Pin_Dict = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super(FormatDialog, self).__init__(parent)
        self.parent = parent
        # 设置阻塞整个应用程序
        self.setWindowModality(Qt.ApplicationModal)
        # 设置窗口只有关闭按键
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowTitle("配置")
        self.logo = QIcon(QPixmap(':/images/logo.png').copy(2, 0, 50, 50))
        self.setWindowIcon(self.logo)
        self.setStyleSheet('\
            QPushButton { font-family: \"微软雅黑\"; font-size: 18px; max-width: 100px; } \
            QLabel { height: 28px;  font-family: \"微软雅黑\"; font-size: 18px; } \
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
            QSpinBox { height: 28px; font-family: \"微软雅黑\"; font-size: 18px; } \
            QLineEdit { height: 28px; font-family: \"微软雅黑\"; font-size: 18px; }')
        self.initUI()

    def initUI(self):
        # QFormLayout
        self.path_line_edit = QLineEdit(self)
        path_btn = QPushButton('选择文件', self)
        path_btn.clicked.connect(self.loadDatalog)
        datalog_layout = QHBoxLayout()
        datalog_layout.addWidget(self.path_line_edit)
        datalog_layout.addWidget(path_btn)
        group1 = QGroupBox('请选择 Data Log 文件', self)
        group1.setLayout(datalog_layout)

        form_layout = QFormLayout()
        form_layout.setAlignment(Qt.AlignHCenter)
        form_layout.setFormAlignment(Qt.AlignHCenter)
        # form_layout.addRow(QLabel('请填写 Data Log 每列数据的宽度', alignment=Qt.AlignHCenter))
        for idx, pair in enumerate(zip(COLUMN_NAME, self.column_width)):
            name = pair[0].replace('\\', '')
            lbl = QLabel(name)
            spin = QSpinBox(parent=self, maximum=50, minimum=len(name), value=pair[1])
            form_layout.addRow(name, spin)
        group2 = QGroupBox('请确认并调整 Data Log 每列数据的宽度', self)
        group2.setLayout(form_layout)
        
        confirm_btn = QPushButton('确定', self)
        confirm_btn.clicked.connect(self.confirm)
        
        layout = QVBoxLayout(self)
        layout.addWidget(group1, stretch=0)
        layout.addWidget(group2, stretch=0)
        layout.addWidget(confirm_btn, alignment=Qt.AlignHCenter)
        
        # QGridLayout
        # layout = QGridLayout(self)
        # layout.addWidget(QLabel('请填写 Data Log 每列数据的宽度'), 0, 0, 1, 10, Qt.AlignHCenter)
        # for idx, pair in enumerate(zip(COLUMN_NAME, self.column_width)):
        #     lbl = QLabel(pair[0])
        #     spin = QSpinBox(parent=self, maximum=50, minimum=len(pair[0]), value=pair[1])
        #     lbl.setBuddy(spin)
        #     layout.addWidget(lbl, idx + 1, 0, 1, 1)
        #     layout.addWidget(spin, idx + 1, 1, 1, 9)
        # confirm_btn = QPushButton('确定', self)
        # confirm_btn.clicked.connect(self.getRegex)
        # layout.addWidget(confirm_btn, 12, 0, 1, 10, Qt.AlignHCenter)

    def loadDatalog(self):
        filename = QFileDialog.getOpenFileName(self, '选择 DataLog 文件', filter='All Files (*.*);;Text Files (*.txt)', initialFilter='Text Files (*.txt)')[0]
        if filename == None or len(filename) == 0:
            return
        self.path_line_edit.setText(filename)
        column_width = None
        begin_regex = r'\ (%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)(%s[^A-Z]*)\n' % (*COLUMN_NAME, )
        self.parent.begin_regex = begin_regex
        with open(filename) as f:
            line = f.readline()
            while line != None and len(line) > 0:
                matcher = re.match(begin_regex, line)
                if matcher:
                    groups = matcher.groups()
                    for (x, y) in zip(self.findChildren(QSpinBox), groups):
                        x.setValue(len(y))
                    break
                line = f.readline()

    def confirm(self):
        regex = self.getRegex()
        self.parent.regex = regex
        datalog_path = self.path_line_edit.text()
        pin_map = self.parent.loadTestName(datalog_path, regex)
        self.Signal_Pin_Dict.emit(pin_map)
        self.close()

    def getRegex(self):
        self.column_width = [x.value() for x in self.findChildren(QSpinBox)]
        regex = r'\ (.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})(.{%d})\s+' % (*self.column_width, )
        return regex


if __name__ == '__main__':
    app = QApplication(sys.argv)
    __dialog = FormatDialog()
    __dialog.show()
    # __dialog.setFixedHeight(__dialog.height())
    sys.exit(app.exec_())
