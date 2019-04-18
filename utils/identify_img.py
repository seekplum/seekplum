# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: identify_img
#         Desc:
#       Author: hjd
#        Email:
#     HomePage:
#      Version:
#   LastChange: 2017-04-24 22:51
#      History:
#=============================================================================

┏┓ ┏┓
┏┛┻━━━┛┻┓
┃ ☃ ┃
┃ ┳┛ ┗┳ ┃
┃ ┻ ┃
┗━┓ ┏━┛
┃ ┗━━━┓
┃ 神兽保佑 ┣┓
┃　永无BUG ┏┛
┗┓┓┏━┳┓┏┛
┃┫┫ ┃┫┫
┗┻┛ ┗┻┛
""""""
先安装： sudo apt-get install tesseract-ocr
"""

import os
from PIL import ImageEnhance
from pytesser import *


def image1(img_path):
    img = Image.open(img_path)
    img_grey = img.convert('L')
    threshold = 140
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    img_out = img_grey.point(table, '1')

    result = image_to_string(img_out)  # 将图片转成字符串
    print result


def image2(img_path):
    image = Image.open(img_path)
    result = image_to_string(image)
    print result


def image3(img_path):
    img = Image.open(img_path)
    # 将图片转成黑白，增加识别率
    enhancer = ImageEnhance.Contrast(img)
    image = enhancer.enhance(4)
    result = image_to_string(image)
    print result


def image4(img_path, cleanup=True, plus=''):
    # cleanup为True则识别完成后删除生成的文本文件
    # plus参数为给tesseract的附加高级参数
    txt_name = img_path.split(".")[0]
    subprocess.check_output('tesseract ' + img_path + ' ' +
                            txt_name + ' ' + plus, shell=True)  # 生成同名txt文件
    text = ''
    with open(txt_name + '.txt', 'r') as f:
        text = f.read().strip()
    if cleanup:
        os.remove(txt_name + '.txt')
    return text


def main():
    image_path = '/home/hjd/PycharmProjects/seekplum/1.jpg'
    print "=" * 100
    image1(image_path)
    print "*" * 100
    image2(image_path)
    print "-" * 100
    image3(image_path)
    print "=" * 100
    print image4(image_path, cleanup=False)
    print "=" * 100


if __name__ == '__main__':
    main()
