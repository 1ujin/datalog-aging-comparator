#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : table.py
@Time   : 2023年05月22日
@Desc   : 表格组件
"""

import pdb
import os
import re
import sys
from collections import OrderedDict
from decimal import Decimal
from PyQt5.QtWidgets import QApplication, QTabWidget, QWidget, QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QStyleFactory, QStyledItemDelegate, QTreeWidgetItemIterator, QFrame, QListWidget, QListWidgetItem, QAbstractItemView, QSpacerItem, QSizePolicy, QFileDialog, QMenu, QAction, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QProgressDialog
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QBrush, QColor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize

import resource
import util

MIN_SIZE = -sys.maxsize - 1

class Table(QTableWidget):
    """docstring for Table"""
    def __init__(self, parent):
        super(Table, self).__init__(0, 0, parent)
        self.parent = parent
        self.progress = None

    def extractDataToDict(self, before_list, after_list, pin_map, regex, begin_regex):
        # 解析文件名并分类
        path_dict = OrderedDict()
        id_error = list()
        duplicate_error = list()
        temperature_error = list()

        for path in before_list:
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
            # 老炼前
            if chip_dict.get('before_aging'):
                duplicate_error.append(path)
                continue
            chip_dict['before_aging'] = path

        for path in after_list:
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
            # 老炼后
            temperature = 25
            if not chip_dict.get('after_aging'):
                chip_dict['after_aging'] = dict()
            after_aging_dict = chip_dict['after_aging']
            if after_aging_dict.get(temperature):
                duplicate_error.append(path)
            else:
                after_aging_dict[temperature] = path

        # for path in path_list:
        #     # 提取编号
        #     basename = os.path.basename(path)
        #     matcher = re.match(r'^([0-9]+)(_(?i)failed)?\.(?i)txt', basename)
        #     chip_id = None
        #     if matcher:
        #         chip_id = matcher.groups()[0]
        #     else:
        #         id_error.append(path)
        #         continue
        #     if not path_dict.get(chip_id):
        #         path_dict[chip_id] = dict()
            
        #     chip_dict = path_dict[chip_id]
            
        #     # 提取温度
        #     dirname = os.path.dirname(path)
        #     if path.upper().find('LAOLIANQIAN') > -1:
        #         # 老炼前
        #         if chip_dict.get('before_aging'):
        #             duplicate_error.append(path)
        #             continue
        #         chip_dict['before_aging'] = path
        #     elif path.upper().find('LAOLIANHOU') > -1:
        #         # 老炼后
        #         temperature = os.path.basename(dirname)
        #         matcher = re.match(r'(-55|-40|0|25|85|105|125)', temperature)
        #         if matcher:
        #             temperature = int(matcher.groups()[0])
        #         else:
        #             temperature_error.append(path)
        #             continue
        #         if not chip_dict.get('after_aging'):
        #             chip_dict['after_aging'] = dict()
        #         after_aging_dict = chip_dict['after_aging']
        #         if after_aging_dict.get(temperature):
        #             duplicate_error.append(path)
        #         else:
        #             after_aging_dict[temperature] = path

        if self.progress:
            self.progress.setLabelText('正在解析文件内容')
            self.progress.setRange(0, len(path_dict) + len(pin_map))
            if sys.platform == 'win32':
                self.taskbar_progress = self.parent.taskbar_progress
                self.taskbar_progress.setRange(0, len(path_dict) + len(pin_map))
                self.taskbar_progress.setValue(0)

        done = 0
        compare_dict = OrderedDict()
        for testname in pin_map.keys():
            compare_dict[testname] = dict()
        for path_item in path_dict.items():
            done += 1
            if self.progress:
                if self.progress.wasCanceled():
                    raise Exception('user canceled')
                self.progress.setValue(done)
                if sys.platform == 'win32':
                    self.taskbar_progress.setValue(done)
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
                                    val = Decimal(val.split(' ')[0]) / 1000
                                elif val.find('u') > -1:
                                    val = Decimal(val.split(' ')[0])
                                elif val.find('m') > -1:
                                    val = Decimal(val.split(' ')[0]) * 1000
                                else:
                                    val = Decimal(val.split(' ')[0]) * 1000 * 1000
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
                                        val = Decimal(val.split(' ')[0]) / 1000
                                    elif val.find('u') > -1:
                                        val = Decimal(val.split(' ')[0])
                                    elif val.find('m') > -1:
                                        val = Decimal(val.split(' ')[0]) * 1000
                                    else:
                                        val = Decimal(val.split(' ')[0]) * 1000 * 1000
                                    compare_pin_dict[after_temperature] = val
                                    pinname_dict[after_temperature] = True
                        line = f.readline()
        return compare_dict, pin_map, path_dict, id_error, temperature_error, duplicate_error

    def fillTable(self, before_list, after_list, pin_map, regex, begin_regex):
        self.progress = QProgressDialog(self)
        self.progress.setWindowTitle('请稍等...')
        self.progress.setLabelText('正在计算文件数量')
        self.progress.setCancelButtonText('停止')
        self.progress.setMinimumDuration(100)
        self.progress.setFixedWidth(500)
        # 窗口是应用的模式窗口，阻塞所有其他应用窗口获得输入
        self.progress.setWindowModality(Qt.ApplicationModal)
        # 设置窗口标题只有关闭
        self.progress.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        if sys.platform == 'win32':
            self.taskbar_progress = self.parent.taskbar_progress
            self.taskbar_progress.setValue(0)

        try:
            compare_dict, pin_map, path_dict, id_error, temperature_error, duplicate_error = self.extractDataToDict(before_list, after_list, pin_map, regex, begin_regex)
        except Exception as e:
            self.progress.cancel()
            if sys.platform == 'win32':
                self.taskbar_progress.stop()
            if str(e) == 'user canceled':
                QMessageBox.information(self, "提示", "已取消")
            else:
                QMessageBox.critical(self, "提示", "失败\n" + str(e))
            if sys.platform == 'win32':
                self.taskbar_progress.resume()
                self.taskbar_progress.reset()
            print(e)
            return

        if len(path_dict) == 0:
            QMessageBox.warning(self, "提示", "请选择至少一个有效的Datalog！")
            return

        self.progress.setLabelText('正在填充表格')
        try:
            self.clear()
            self.setRowCount(3)
            self.setColumnCount(0)
            
            col = 0
            done = self.progress.value()
            for testname_item in pin_map.items():
                if self.progress.wasCanceled():
                    if sys.platform == 'win32':
                        self.taskbar_progress.resume()
                        self.taskbar_progress.reset()
                    self.setRowCount(0)
                    self.setColumnCount(0)
                    return
                done += 1
                self.progress.setValue(done)
                if sys.platform == 'win32':
                    self.taskbar_progress.setValue(done)
                # 循环测试项
                testname, pin_dict = testname_item
                lower_bound = pin_dict.get('__lower_bound')
                upper_bound = pin_dict.get('__upper_bound')

                # 表头
                temp_set = set()
                for pin_item in pin_dict.items():
                    if pin_item[0] == '__upper_bound' or pin_item[0] == '__lower_bound':
                        continue
                    temp_set.update(pin_item[1].keys())
                temp_list = list(temp_set)
                temp_list.sort()
                for i in range(len(temp_set) * 3):
                    self.insertColumn(self.columnCount())
                current_w = 0
                self.setSpan(0, col + current_w, 1, len(temp_set) * 3)
                upper_bound = ''
                if pin_dict.get('__upper_bound') != None:
                    upper_bound = pin_dict.get('__upper_bound')
                lower_bound = ''
                if pin_dict.get('__lower_bound') != None:
                    lower_bound = pin_dict.get('__lower_bound')
                bound = ' [%s,%s]' % (str(lower_bound), str(upper_bound))
                self.setItem(0, col + current_w, self.getTableItem(testname + bound))
                current_w += 2
                self.setItem(1, col + current_w, self.getTableItem('老炼前'))
                # self.setItem(2, col + current_w, self.getTableItem('常温'))
                current_w += 1
                if len(temp_set) > 1:
                    # self.setSpan(1, col + current_w, 1, (len(temp_set) - 1) * 3)
                    # self.setItem(1, col + current_w, self.getTableItem('老炼后'))
                    for temp in temp_list[1:]:
                        self.setItem(1, col + current_w, self.getTableItem('老炼后'))
                        current_w += 1
                        self.setItem(1, col + current_w, self.getTableItem('变化值'))
                        current_w += 1
                        self.setItem(1, col + current_w, self.getTableItem('变化百分比'))
                        current_w += 1

                # 测试结果
                compare_testname_dict = compare_dict.get(testname)
                if not compare_testname_dict:
                    continue
                row = 2
                max_w = 0
                for compare_chip_item in compare_testname_dict.items():
                    # 循环芯片
                    chip_id, compare_pin_dict = compare_chip_item
                    current_h = 0
                    for pin_item in pin_dict.items():
                        # 循环Pin
                        pinname, temperature = pin_item
                        if pinname == '__lower_bound' or pinname == '__upper_bound':
                            continue
                        current_w = 1
                        if row + current_h >= self.rowCount():
                            self.insertRow(self.rowCount())
                        self.setItem(row + current_h, col + current_w, self.getTableItem(pinname))
                        current_w += 1
                        compare_temp_dict = compare_pin_dict.get(pinname)
                        if not compare_temp_dict:
                            continue
                        # 老炼前
                        before_val = compare_temp_dict.get(MIN_SIZE)
                        if before_val:
                            self.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(before_val)))
                        current_w += 1
                        diff = None
                        for compare_temp_item in compare_temp_dict.items():
                            # 循环温度
                            temperature, test_val = compare_temp_item
                            if temperature != MIN_SIZE and test_val != None:
                                # 老炼后
                                self.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(test_val)))
                                current_w += 1
                                if before_val:
                                    diff = test_val - before_val
                                    self.setItem(row + current_h, col + current_w, self.getTableItem(self.convertDecimal(diff)))
                                    current_w += 1
                                    percent = (diff * 100 / before_val).quantize(Decimal("0.00"))
                                    self.setItem(row + current_h, col + current_w, self.getTableItem(str(percent) + '%'))
                                    current_w += 1
                                    if lower_bound != '' and diff < lower_bound or upper_bound != '' and diff > upper_bound:
                                        for i in range(-3, 0):
                                            self.item(row + current_h, col + current_w + i).setBackground(QBrush(QColor(255, 0, 0)))
                                else:
                                    current_w += 2
                        max_w = max(max_w, current_w)
                        current_h += 1
                    # 芯片编号
                    self.setItem(row, col, self.getTableItem(chip_id, Qt.AlignHCenter|Qt.AlignTop))
                    self.setSpan(row, col, current_h, 1)
                    row += current_h
                col += max_w
        
        except Exception as e:
            self.progress.cancel()
            if sys.platform == 'win32':
                self.taskbar_progress.stop()
            QMessageBox.critical(self, "提示", "失败\n" + str(e))
            if sys.platform == 'win32':
                self.taskbar_progress.resume()
                self.taskbar_progress.reset()
            print(e)
            return
        if sys.platform == 'win32':
            self.taskbar_progress.reset()
        self.show()

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

    def exportExcel(self):
        filename = QFileDialog.getSaveFileName(self, '导出表格', filter='Excel Files (*.xlsx *.xls)')[0]
        if filename == '':
            return
        util.exportExcel(self, filename)
        return filename