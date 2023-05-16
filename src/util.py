#!/usr/bin/env python
# -*- encoding:utf-8 -*-
"""
@Author : 卢晋
@File   : util.py
@Time   : 2023年5月15日
@Desc   : 工具类
"""

import openpyxl
import pdb

def exportExcel(table, filename):
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        
        max_row = table.rowCount()
        max_col = table.columnCount()

        # 测试值
        for col in range(1, max_col):
            max_length = 0
            for row in range(2, max_row):
                item = table.item(row, col)
                if not item:
                    continue
                cell = ws.cell(row + 1, col + 1)
                text = item.text().strip()
                if text[0] == '-':
                    text = text[1:]
                if text.find('.') > -1:
                    integer, decimal = text.split('.')
                    if integer.isdigit() and decimal.isdigit():
                        cell.value = float(item.text().strip())
                    else:
                        cell.value = item.text().strip()
                elif text.isdigit():
                    cell.value = int(item.text().strip())
                else:
                    cell.value = item.text().strip()
                cell.alignment = openpyxl.styles.alignment.Alignment(horizontal='center', vertical='center')
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            adjusted_width = (max_length + 2) * 1.2
            col_letter = [x[0].column_letter for x in ws.columns][col]
            ws.column_dimensions[col_letter].width = adjusted_width

        # 芯片ID
        it = iter(range(max_row))
        for row in it:
            span = table.rowSpan(row, 0)
            item = table.item(row, 0)
            if not item:
                continue
            cell = ws.cell(row + 1, 1)
            cell.value = item.text()
            cell.alignment = openpyxl.styles.alignment.Alignment(horizontal='center', vertical='top')
            ws.merge_cells(start_row = row + 1, start_column = 1, end_row = row + span, end_column = 1)
            if span > 1:
                for i in range(span - 1):
                    next(it)

        # 表头
        for row in range(2):
            it = iter(range(max_col))
            for col in it:
                span = table.columnSpan(row, col)
                item = table.item(row, col)
                if not item:
                    continue
                cell = ws.cell(row + 1, col + 1)
                cell.value = item.text()
                cell.alignment = openpyxl.styles.alignment.Alignment(horizontal='center', vertical='center')
                ws.merge_cells(start_row = row + 1, start_column = col + 1, end_row = row + 1, end_column = col + span)
                if span > 1:
                    for i in range(span - 1):
                        next(it)

        wb.save(filename)
    except Exception as e:
        print(e)