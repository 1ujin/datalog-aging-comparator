#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : table.py
@Time   : 2023年05月22日
@Desc   : 表格组件
"""
import gc
import os
import re
import sys
import traceback
from collections import OrderedDict
from decimal import Decimal
from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox, QProgressDialog
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt

import util
from errordialog import ErrorDialog

MIN_SIZE = -sys.maxsize - 1


class Table(QTableWidget):
    """docstring for Table"""

    def __init__(self, parent):
        super(Table, self).__init__(0, 0, parent)
        self.parent = parent
        self.progress = None
        self.taskbar_progress = None

    @staticmethod
    def extract_j750(temperature, path, compare_chip_dict, pin_map, regex, begin_regex):
        total = 0
        # 读取文件
        with open(path, "r", encoding="utf-8") as f:
            line = f.readline()
            while line is not None and len(line) > 0:
                if re.match(begin_regex, line):
                    break
                line = f.readline()
            line = f.readline()
            while line is not None and len(line) > 0:
                matcher = re.match(regex, line)
                if not matcher:
                    line = f.readline()
                    continue
                group = matcher.groups()
                test_name = group[3].strip()
                pin_name = group[4].strip()
                # 匹配测试项
                test_dict = pin_map.get(test_name)
                if test_dict is None:
                    # 该测试项未被选中
                    line = f.readline()
                    continue

                compare_test_dict = compare_chip_dict.get(test_name)
                if compare_test_dict is None:
                    compare_test_dict = dict()
                    compare_chip_dict[test_name] = compare_test_dict

                if test_dict is not None:
                    unit = 1
                    test_unit = test_dict.get("__unit")
                    if test_unit is not None and len(test_unit) > 0:
                        if test_unit.find("p") > -1:
                            unit = 1
                        elif test_unit.find("n") > -1:
                            unit = 1000
                        elif test_unit.find("u") > -1:
                            unit = 1000 * 1000
                        elif test_unit.find("m") > -1:
                            unit = 1000 * 1000 * 1000
                        else:
                            unit = 1000 * 1000 * 1000 * 1000

                    # 匹配Pin
                    pin_dict = test_dict.get(pin_name)
                    if pin_dict is not None:
                        compare_pin_dict = compare_test_dict.get(pin_name)
                        if compare_pin_dict is None:
                            compare_pin_dict = OrderedDict()
                            compare_test_dict[pin_name] = compare_pin_dict

                        val = group[7].strip()
                        if val.find("p") > -1:
                            val = Decimal(val.split(" ")[0])
                        elif val.find("n") > -1:
                            val = Decimal(val.split(" ")[0]) * 1000
                        elif val.find("u") > -1:
                            val = Decimal(val.split(" ")[0]) * 1000 * 1000
                        elif val.find("m") > -1:
                            val = Decimal(val.split(" ")[0]) * 1000 * 1000 * 1000
                        else:
                            val = Decimal(val.split(" ")[0]) * 1000 * 1000 * 1000 * 1000
                        val /= unit
                        compare_pin_dict[temperature] = val
                        pin_dict.append(temperature)
                        total += 1
                line = f.readline()
        return total

    def extract_data_to_dict(self, before_list, after_list, pin_map, regex, begin_regex):
        # 解析文件名并分类
        path_dict = OrderedDict()
        id_error = list()
        duplicate_error = list()
        temperature_error = list()

        chip_max_count = 0
        for path in before_list:
            # 提取编号
            basename = os.path.basename(path)
            matcher = re.match(r"^([0-9]+)(_(?i)failed)?\.(?i)txt", basename)
            if matcher:
                chip_id = matcher.groups()[0]
                passed = matcher.groups()[1] is None
            else:
                id_error.append(path)
                continue
            if not path_dict.get(chip_id):
                path_dict[chip_id] = dict()

            chip_dict = path_dict[chip_id]
            # 老炼前
            if chip_dict.get("before_aging"):
                duplicate_error.append(path)
                continue
            chip_dict["before_aging"] = (path, passed)

        for path in after_list:
            # 提取编号
            basename = os.path.basename(path)
            matcher = re.match(r"^([0-9]+)(_(?i)failed)?\.(?i)txt", basename)
            if matcher:
                chip_id = matcher.groups()[0]
                passed = matcher.groups()[1] is None
            else:
                id_error.append(path)
                continue
            if not path_dict.get(chip_id):
                path_dict[chip_id] = dict()

            chip_dict = path_dict[chip_id]
            # 老炼后
            temperature = 25
            if not chip_dict.get("after_aging"):
                chip_dict["after_aging"] = dict()
            after_aging_dict = chip_dict["after_aging"]
            if after_aging_dict.get(temperature):
                duplicate_error.append(path)
            else:
                after_aging_dict[temperature] = (path, passed)
            if chip_dict.get("before_aging") and chip_dict.get("after_aging"):
                chip_max_count = max(chip_max_count, len(chip_dict.get("after_aging")))

        error_reply = 1
        if len(id_error) + len(duplicate_error) + len(temperature_error) > 0:
            if self.progress:
                self.progress.reset()
                if sys.platform == "win32":
                    self.taskbar_progress.resume()
                    self.taskbar_progress.reset()
            # 错误列表
            dialog = ErrorDialog(self)
            dialog.fill_id_error_list(id_error)
            dialog.fill_duplicate_error_list(duplicate_error)
            dialog.fill_temperature_error_list(temperature_error)
            error_reply = dialog.exec()

        if error_reply != 1:
            raise Exception("user canceled")

        if chip_max_count < 1:
            raise Exception("找不到可比较的老炼前后Datalog")

        if self.progress:
            self.progress.setLabelText("正在解析文件内容")
            self.progress.setRange(0, len(path_dict))
            self.progress.setValue(0)
            if sys.platform == "win32":
                self.taskbar_progress = self.parent.taskbar_progress
                self.taskbar_progress.setRange(0, len(path_dict))
                self.taskbar_progress.setValue(0)

        done = 0
        total = 0
        compare_dict = OrderedDict()
        for path_item in path_dict.items():
            done += 1
            if self.progress:
                if self.progress.wasCanceled():
                    raise Exception("user canceled")
                self.progress.setValue(done)
                if sys.platform == "win32":
                    self.taskbar_progress.setValue(done)
            chip_id = path_item[0]

            compare_chip_dict: Optional[Dict[str, Any]] = compare_dict.get(chip_id)
            if compare_chip_dict is None:
                compare_chip_dict = dict()
                compare_dict[chip_id] = compare_chip_dict

            # 老炼前
            before_path = path_item[1].get("before_aging")
            if before_path:
                total = self.extract_j750(MIN_SIZE, before_path[0],
                                          compare_chip_dict, pin_map, regex, begin_regex)

            # 老炼后
            after_item = path_item[1].get("after_aging")
            if after_item:
                for temperature_item in after_item.items():
                    # 循环温度
                    after_temperature, after_temperature_path = temperature_item
                    self.extract_j750(after_temperature, after_temperature_path[0],
                                      compare_chip_dict, pin_map, regex, begin_regex)

        if self.progress:
            self.progress.setLabelText("正在填充表格")
            self.progress.setRange(0, total)
            self.progress.setValue(0)
            if sys.platform == "win32":
                self.taskbar_progress = self.parent.taskbar_progress
                self.taskbar_progress.setRange(0, total)
                self.taskbar_progress.setValue(0)
        return compare_dict, pin_map, path_dict, id_error, temperature_error, duplicate_error

    def fill_table(self, before_list, after_list, pin_map, regex, begin_regex):
        if self.progress is None:
            self.progress = QProgressDialog(self)
        self.progress.setWindowTitle("请稍等...")
        self.progress.setLabelText("正在计算文件数量")
        self.progress.setCancelButtonText("停止")
        self.progress.setMinimumDuration(100)
        self.progress.setFixedWidth(500)
        # 窗口是应用的模式窗口，阻塞所有其他应用窗口获得输入
        self.progress.setWindowModality(Qt.ApplicationModal)
        # 设置窗口标题只有关闭
        self.progress.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        self.progress.setValue(0)
        if sys.platform == "win32":
            self.taskbar_progress = self.parent.taskbar_progress
            self.taskbar_progress.setValue(0)

        try:
            compare_dict, pin_map, path_dict, *_ = self.extract_data_to_dict(
                before_list, after_list, pin_map, regex, begin_regex)
        except Exception as e:  # pylint: disable=broad-except
            self.progress.cancel()
            if sys.platform == "win32":
                self.taskbar_progress.stop()
            if str(e) == "user canceled":
                QMessageBox.information(self, "提示", "已取消")
            else:
                tb = traceback.extract_tb(e.__traceback__)[-1]
                QMessageBox.critical(self, "提示", "失败\n" + str(e) + "\n" + str(tb)[19:-1] + "\n" + tb.line)
            self.progress.reset()
            if sys.platform == "win32":
                self.taskbar_progress.resume()
                self.taskbar_progress.reset()
            return

        if len(path_dict) == 0:
            QMessageBox.warning(self, "提示", "请选择至少一个有效的Datalog！")
            return

        try:
            self.clear()
            self.setRowCount(2)
            self.setColumnCount(2)
            self.setSpan(0, 0, 2, 2)

            test_name_col = 2
            done = 0
            # 确定列数
            for test_item in pin_map.items():
                if self.progress.wasCanceled():
                    self.setRowCount(0)
                    self.setColumnCount(0)
                    raise Exception("user canceled")
                # 循环测试项
                test_name, pin_dict = test_item

                # 上下限值和单位
                lower_bound = pin_dict.get("__lower_bound")
                upper_bound = pin_dict.get("__upper_bound")
                unit = pin_dict.get("__unit")

                # 表头
                temp_set = set()
                for pin_item in pin_dict.items():
                    if pin_item[0] == "__upper_bound" or pin_item[0] == "__lower_bound" or pin_item[0] == "__unit":
                        continue
                    temp_set.update(pin_item[1])
                    self.insertColumn(self.columnCount())
                temp_list = list(temp_set)
                temp_list.sort()

                pin_name_col = 0
                bound = ""
                if lower_bound is None:
                    lower_bound = ""
                if upper_bound is None:
                    upper_bound = ""
                if lower_bound != "" or upper_bound != "":
                    bound = " [%s,%s]" % (str(lower_bound), str(upper_bound))
                unit = " (" + unit + ")"
                self.setItem(0, test_name_col + pin_name_col, self.get_table_item(test_name + bound + unit))
                for pin_item in pin_dict.items():
                    if pin_item[0] == "__upper_bound" or pin_item[0] == "__lower_bound" or pin_item[0] == "__unit":
                        continue
                    self.setItem(1, test_name_col + pin_name_col, self.get_table_item(pin_item[0]))
                    pin_name_col += 1
                self.setSpan(0, test_name_col, 1, pin_name_col)
                test_name_col += pin_name_col

            # 测试结果
            chip_row = 2
            for compare_chip_item in compare_dict.items():
                # 循环样品
                max_temp_row = 0
                test_name_col = 2
                chip_id, chip_dict = compare_chip_item
                self.insertRow(self.rowCount())
                for test_item in pin_map.items():
                    pin_name_col = 0
                    # 循环test_name
                    test_name, test_dict = test_item
                    compare_test_dict = chip_dict.get(test_name)
                    if self.progress.wasCanceled():
                        self.setRowCount(0)
                        self.setColumnCount(0)
                        raise Exception("user canceled")

                    lower_bound = test_dict.get("__lower_bound")
                    upper_bound = test_dict.get("__upper_bound")
                    for pin_item in test_dict.items():
                        # 循环pin_name
                        temp_row = 0
                        if self.progress.wasCanceled():
                            self.setRowCount(0)
                            self.setColumnCount(0)
                            raise Exception("user canceled")
                        if compare_test_dict is None:
                            # self.insertRow(self.rowCount())
                            continue
                        pin_name, pin_dict = pin_item
                        if pin_name == "__lower_bound" or pin_name == "__upper_bound" or pin_name == "__unit":
                            continue
                        compare_pin_dict = compare_test_dict.get(pin_name)
                        if not compare_pin_dict:
                            continue
                        exp_row_cnt = chip_row + len(compare_pin_dict) * 3 - 2
                        if exp_row_cnt > self.rowCount():
                            self.setRowCount(exp_row_cnt)
                        # 老炼前
                        before_val = compare_pin_dict.get(MIN_SIZE)
                        if before_val:
                            if chip_row + temp_row >= self.rowCount():
                                self.setRowCount(chip_row + temp_row + 1)
                            self.setItem(chip_row + temp_row, test_name_col + pin_name_col,
                                         self.get_table_item(self.convert_decimal(before_val)))
                            done += 1
                            self.progress.setValue(done)
                            if sys.platform == "win32":
                                self.taskbar_progress.setValue(done)
                        temp_row += 1
                        for compare_temp_item in compare_pin_dict.items():
                            # 循环温度
                            temperature, test_val = compare_temp_item
                            if temperature != MIN_SIZE and test_val is not None:
                                # 老炼后
                                if chip_row + temp_row >= self.rowCount():
                                    self.setRowCount(chip_row + temp_row + 3)
                                self.setItem(chip_row + temp_row, test_name_col + pin_name_col,
                                             self.get_table_item(self.convert_decimal(test_val)))
                                temp_row += 1
                                if before_val:
                                    diff = test_val - before_val
                                    self.setItem(chip_row + temp_row, test_name_col + pin_name_col,
                                                 self.get_table_item(self.convert_decimal(diff)))
                                    temp_row += 1
                                    percent = (diff * 100 / before_val).quantize(Decimal("0.00"))
                                    self.setItem(chip_row + temp_row, test_name_col + pin_name_col,
                                                 self.get_table_item(str(percent) + "%"))
                                    temp_row += 1
                                    if lower_bound and diff < lower_bound \
                                            or upper_bound and diff > upper_bound:
                                        for i in range(-3, 0):
                                            self.item(chip_row + temp_row + i, test_name_col + pin_name_col) \
                                                .setBackground(QBrush(QColor(255, 0, 0)))
                                else:
                                    temp_row += 2
                        pin_name_col += 1
                        max_temp_row = max(temp_row, max_temp_row)
                    test_name_col += pin_name_col
                # 芯片编号
                self.setItem(chip_row, 0, self.get_table_item(chip_id, Qt.AlignHCenter | Qt.AlignTop))
                self.setSpan(chip_row, 0, max_temp_row, 1)
                self.setItem(chip_row, 1, self.get_table_item("老炼前"))
                for i in range(1, max_temp_row, 3):
                    self.setItem(chip_row + i, 1, self.get_table_item("老炼后"))
                    self.setItem(chip_row + i + 1, 1, self.get_table_item("变化值"))
                    self.setItem(chip_row + i + 2, 1, self.get_table_item("变化百分比"))
                # for path_item in path_dict:
                #     if path_item[0] == chip_id and path_item[2] is False:
                #         for red_row in range(max_temp_row):
                #             for red_col in range(self.columnCount()):
                #                 if self.item(chip_row + red_row, red_col) is None:
                #                     continue
                #                 self.item(chip_row + red_row, red_col).setBackground(QBrush(QColor(255, 0, 0)))
                #         break
                chip_row += max_temp_row

        except Exception as e:  # pylint: disable=broad-except
            self.progress.cancel()
            if sys.platform == "win32":
                self.taskbar_progress.stop()
            if str(e) == "user canceled":
                QMessageBox.information(self, "提示", "已取消")
            else:
                tb = traceback.extract_tb(e.__traceback__)[-1]
                QMessageBox.critical(self, "提示", "失败\n" + str(e) + "\n" + str(tb)[19:-1] + "\n" + tb.line)
            self.progress.reset()
            if sys.platform == "win32":
                self.taskbar_progress.resume()
                self.taskbar_progress.reset()
            del compare_dict
            del pin_map
            del path_dict
            gc.collect()
            return
        self.progress.reset()
        if sys.platform == "win32":
            self.taskbar_progress.resume()
            self.taskbar_progress.reset()
        if self.rowCount() != 0 and self.columnCount() != 0:
            self.show()
        del compare_dict
        del pin_map
        del path_dict
        gc.collect()

    @staticmethod
    def get_table_item(text, alignment=Qt.AlignHCenter | Qt.AlignVCenter):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(alignment)
        return item

    @staticmethod
    def convert_decimal(val):
        if val == 0:
            return Decimal(0)
        elif val == val.to_integral():
            val = val.to_integral()
        else:
            val = val.normalize()
        return val

    def export_excel(self):
        filename = QFileDialog.getSaveFileName(self, "导出表格", filter="Excel Files (*.xlsx *.xls)")[0]
        if filename == "":
            return
        if self.progress is None:
            self.progress = QProgressDialog(self)
        self.progress.setWindowTitle("请稍等...")
        self.progress.setLabelText("正在导出")
        self.progress.setCancelButtonText("停止")
        self.progress.setMinimumDuration(100)
        self.progress.setFixedWidth(500)
        # 窗口是应用的模式窗口，阻塞所有其他应用窗口获得输入
        self.progress.setWindowModality(Qt.ApplicationModal)
        # 设置窗口标题只有关闭
        self.progress.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        try:
            if sys.platform == "win32":
                util.export_excel(self, filename, self.progress, self.parent.taskbar_progress)
            else:
                util.export_excel(self, filename, self.progress)
            return filename
        except PermissionError:
            QMessageBox.critical(self, "提示", "文件已被打开或占用")
        except Exception as e:  # pylint: disable=broad-except
            self.progress.cancel()
            if sys.platform == "win32":
                self.taskbar_progress.stop()
            if str(e) == "user canceled":
                QMessageBox.information(self, "提示", "已取消")
            else:
                tb = traceback.extract_tb(e.__traceback__)[-1]
                QMessageBox.critical(self, "提示", "失败\n" + str(e) + "\n" + str(tb)[19:-1] + "\n" + tb.line)
            self.progress.reset()
            if sys.platform == "win32":
                self.taskbar_progress.resume()
                self.taskbar_progress.reset()
