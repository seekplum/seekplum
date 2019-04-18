#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import division
from PIL import Image

import xlwt
import xlrd
from xlutils.copy import copy


def set_style(font_name, height, bold=False):
    """
    设置内容样式
    :param font_name: 字体
    :param height: 字号
    :param bold: 是否加粗
    :return:
    """
    style = xlwt.XFStyle()  # 初始化样式

    font = xlwt.Font()  # 为样式创建字体
    font.name = font_name  # 'Times New Roman'
    font.bold = bold  # 是否加粗
    font.colour_index = 0x34  # 字体颜色
    font.height = height  # 除以 20 就是字号

    borders = xlwt.Borders()  # 设置边框
    borders.left = 6
    borders.right = 6
    borders.top = 6
    borders.bottom = 6

    style.font = font
    style.borders = borders

    return style


def read_excel(execl_file):
    """
    读取excel数据
    :param execl_file:excel工作簿
    :return:
    """
    data = xlrd.open_workbook(execl_file, formatting_info=True)  # 打开execl_file
    sheet_name = data.sheet_names()  # 获取xls文件中所有sheet的名称
    table_one = data.sheets()[0]  # 获取xls文件第一个工作表
    table_index = data.sheet_by_index(0)  # 通过索引获取xls文件第0个sheet
    table_name = data.sheet_by_name('merge')  # 通过工作表名获取 sheet
    for sheet in sheet_name:
        print "工作表：", sheet
    # 工作表名字
    sheet = table_index.name
    print "工作表名：", sheet
    # 获取行数
    rows = table_one.nrows
    # 获取列数
    cols = table_name.ncols
    print "row: %s, col: %s" % (rows, cols)
    # 获取整行的值
    rows_value = table_index.row_values(0)
    for i, value in enumerate(rows_value):
        value = value.encode('utf-8') if isinstance(value, unicode) else value
        print value,
    print
    # 获取整列的值
    cols_value = table_index.col_values(0)
    for value in cols_value:
        value = value.encode('utf-8') if isinstance(value, unicode) else value
        print value,
    print
    # 获取单元格数据类型
    cell_type = table_index.cell(0, 0).ctype  # 行、列
    # 获取单元格数据
    cell = table_index.cell(0, 0).value
    # 转为日期类型，但转之前要确认 ctype = 3
    if cell_type == 3:
        date_value = xlrd.xldate_as_tuple(table_index.cell_value(0, 0), data.datemode)
        print "date_value:", date_value
    # 使用行索引
    cell_row = table_index.row(2)[2].value
    # 使用列索引
    cell_col = table_index.col(2)[2].value
    print "cell_type: %s, cell: %s, cell_row: %s, cell_col: %s" % (cell_type, cell, cell_row, cell_col)
    row = 2
    col = 2
    c_type = 2  # 类型 0:empty,1:string, 2:number, 3:date, 4:boolean, 5：error
    value = 1234
    xf = 0  # 扩展的格式化 (默认是0)
    table_index.put_cell(row, col, c_type, value, xf)  # 值不会写入，但是现在能被获取
    # 获取合并的单元格 此时，formatting_info参数要设置为 True,否则无法读取合并单元格的值
    merge_value = table_index.merged_cells
    print "merge_value:", merge_value


def write_excel(execl_file):
    """
    不保留原来数据
    :param execl_file:excel工作簿
    :return:
    """

    # 表头设置颜色
    style_bold_red = xlwt.easyxf('font: color-index red, bold on')
    header_style = style_bold_red
    wb = xlwt.Workbook()
    # 工作表名
    ws = wb.add_sheet('1')
    # 设置 单元格宽度
    first_col = ws.col(0)
    first_col.width = 256 * 30  # 设置单元格宽带30
    ws.write(2, 0, "Header", header_style)  # excel x,y轴都是从0开始计算，2，0代表在第三行第一列交叉那个单元格写入数据
    ws.write(2, 1, "CatalogNumber", header_style)
    ws.write(2, 2, "PartNumber", header_style)
    wb.save(execl_file)


def save_old_excel(execl_file):
    """
    保留原数据
    :param execl_file:excel工作簿
    :return:
    """

    # formatting_info=True 保留表格原来数据
    old_wb = xlrd.open_workbook(execl_file, formatting_info=True)
    new_wb = copy(old_wb)
    new_ws = new_wb.add_sheet('2')
    for i in xrange(1, 20):
        new_ws.write(10, i, i)
    new_wb.save(execl_file)


def add_image(execl_file):
    """
    插入图片
    :param execl_file:excel工作簿
    :return:
    """
    # 使用PIL模块转换图片格式
    img = Image.open('D:\er.jpg')
    img.convert('RGB')
    img.save('D:\er.bmp', 'BMP')
    image = xlwt.Workbook(encoding='utf-8')  # 创建工作簿
    new_ws = image.add_sheet('image', cell_overwrite_ok=True)  # 创建sheet
    # 只能保存bmp格式的图片
    # new_ws.insert_bitmap('D:\er.bmp', 0, 0)
    new_ws.insert_bitmap('D:\er.bmp', 0, 0, 100, 100, scale_x=1, scale_y=1)
    # img表示要插入的图像地址
    # x表示行
    # y表示列
    # x1表示相对原来位置向下偏移的像素
    # y1表示相对原来位置向右偏移的像素
    # scale_x表示相对原图宽的比例
    # scale_y表示相对原图高的比例
    image.save(execl_file)


def write_merge_table(execl_file):
    """
    创建合并单元格
    :param execl_file:excel工作簿
    :return:
    """
    f = xlwt.Workbook(encoding='utf-8')  # 创建工作簿
    sheet1 = f.add_sheet('merge', cell_overwrite_ok=True, )  # 创建sheet, cell_overwrite_ok:是否可以覆盖单元格
    row0 = ['业务', '状态', '北京', '上海', '广州', '深圳', '状态小计', '合计']
    column0 = ['机票', '船票', '火车票', '汽车票', '其它']
    status = ['预订', '出票', '退票', '业务小计']
    # status = [u'预订', u'出票', u'退票', u'业务小计']  # 未设置编码写法

    # 生成第一行
    for i in range(0, len(row0)):
        sheet1.write(0, i, row0[i], set_style('Times New Roman', 300, True))

    # 生成第一列和最后一列(合并4行)
    i, j = 1, 0
    while i < 4 * len(column0) and j < len(column0):
        sheet1.write_merge(i, i + 3, 0, 0, column0[j], set_style('Arial', 220))  # 第一列
        # write_merge(x, x + m, y, y + n, string, sytle)
        # x表示行，y表示列，m表示跨行个数，n表示跨列个数，string表示要写入的单元格内容，style表示单元格样式。其中，x，y，w，h，都是以0开始计算的。
        sheet1.write_merge(i, i + 3, 7, 8)  # 最后一列"合计"
        i += 4
        j += 1

    sheet1.write_merge(21, 21, 0, 1, u'合计', set_style('Times New Roman', 220))

    # 生成第二列
    i = 0
    while i < 4 * len(column0):
        for j in range(0, len(status)):
            sheet1.write(j + i + 1, 1, status[j])
        i += 4
    f.save(execl_file)  # 保存文件


def write_link(execl_file):
    """
    创建超链接
    :param execl_file: excel工作簿
    :return:
    """
    f = xlwt.Workbook(encoding='utf-8')  # 创建工作簿
    sheet1 = f.add_sheet('merge', cell_overwrite_ok=True, )  # 创建sheet, cell_overwrite_ok:是否可以覆盖单元格
    # 添加超链接
    n = "HYPERLINK"
    sheet1.write_merge(9, 10, 9, 10, xlwt.Formula(n + u'("http://www.cnblogs.com/hm24"; "黄剑冬")'))
    f.save(execl_file)  # 保存文件


if __name__ == '__main__':
    execl_file = 'D://test.xls'
    read_excel(execl_file)
