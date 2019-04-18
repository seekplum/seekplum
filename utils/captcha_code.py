#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: code
#         Desc: 生成验证码
                pip install captcha
                sudo apt-get install python-tk
#       Author: hjd
#     HomePage: seekplun.github.io
#   LastChange: 2018-03-24 02:28
#=============================================================================
"""
from __future__ import division

import os
import random

import numpy as np
import matplotlib.pyplot as plt

from captcha.image import ImageCaptcha
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_letter_cases = "abcdefghjkmnpqrstuvwxy"  # 小写字母，去除可能干扰的i，l，o，z
_upper_cases = _letter_cases.upper()  # 大写字母
_numbers = "23456789"  # 数字 去除 0,1
init_chars = ''.join((_letter_cases, _upper_cases, _numbers))


def create_validate_code(size=(160, 60),
                         chars=_numbers,
                         mode="RGB",
                         bg_color=(255, 255, 255),
                         fg_color=(0, 0, 255),
                         font_size=47,
                         font_type="msyh.ttf",
                         length=4,
                         draw_lines=False,
                         n_line=(1, 2),
                         draw_points=False,
                         point_chance=2):
    """生成验证码图片

    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param chars: 允许的字符集合，格式字符串
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param font_type: 验证码字体，默认为 ae_AlArabiya.ttf(这个字体必须得是系统/usr/share/fonts/存在的 ，否则会报错的！！！！！！！！)
    @param length: 验证码字符个数
    @param draw_lines: 是否划干扰线
    @param n_line: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    @param draw_points: 是否画干扰点
    @param point_chance: 干扰点出现的概率，大小范围[0, 100]

    @return: [0]: PIL Image实例
    @return: [1]: 验证码图片中的字符串
    """

    width, height = size  # 宽， 高
    img = Image.new(mode, size, bg_color)  # 创建图形
    draw = ImageDraw.Draw(img)  # 创建画笔

    def get_chars():
        """生成给定长度的字符串，返回列表格式
        """
        return random.sample(chars, length)

    def create_lines():
        """绘制干扰线
        """
        line_num = random.randint(*n_line)  # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            # 结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        """绘制干扰点
        """
        chance = min(100, max(0, int(point_chance)))  # 大小限制在[0, 100]

        for w in range(width):
            for h in range(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_text():
        """绘制验证码字符
        """
        c_chars = get_chars()
        text_ = ' %s ' % ' '.join(c_chars)  # 每个字符前后以空格隔开

        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(text_)

        draw.text(((width - font_width) / 3, (height - font_height) / 3), text_, font=font, fill=fg_color)

        return ''.join(c_chars)

    def transform():
        """对验证码中的文件进行偏移
        """
        # 图形扭曲参数
        params = [1 - float(random.randint(1, 2)) / 100,
                  0,
                  0,
                  0,
                  1 - float(random.randint(1, 10)) / 100,
                  float(random.randint(1, 2)) / 500,
                  0.001,
                  float(random.randint(1, 2)) / 500
                  ]
        return img.transform(size, Image.PERSPECTIVE, params)  # 创建扭曲

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    text = create_text()

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 滤镜，边界加强（阈值更大）

    return img, text


# 验证码中的字符
NUMBERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
LOWERCASE_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                     'u', 'v', 'w', 'x', 'y', 'z']
CAPITAL_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                   'U', 'V', 'W', 'X', 'Y', 'Z']


def random_captcha_text(char_set, captcha_size=4):
    """验证码一般都无视大小写；验证码长度4个字符

    :param char_set: 字符列表
    :type char_set list

    :param captcha_size: 验证码长度
    :type captcha_size int

    :rtype captcha_text str
    :return 生成的验证码字符
    """
    if char_set is None:
        char_set = NUMBERS + LOWERCASE_LETTERS + CAPITAL_LETTERS
    captcha_text = []
    for i in range(captcha_size):
        c = random.choice(char_set)
        captcha_text.append(c)
    return captcha_text


def gen_captcha_text_and_image(is_save, image_path=None, char_set=None, file_name=None, suffix="png"):
    """生成字符对应的验证码

    :param image_path: 生成后的验证码路径
    :type image_path str

    :param is_save: 是否保存图片
    :type is_save bool

    :param char_set: 字符列表
    :type char_set list

    :param file_name: 验证码文件名
    :type file_name str

    :param suffix: 图片后缀,默认值位 png
    :type suffix str

    :rtype captcha_text str
    :return captcha_text 验证码内容

    :rtype file_path str
    :return file_path 验证码路径

    :rtype captcha_image PIL.Image.Image
    :return captcha_image Image对象
    """
    image_captcha = ImageCaptcha(width=160, height=60, fonts=None, font_sizes=(56,))

    # 获得验证码内容
    captcha_text = random_captcha_text(char_set)
    captcha_text = ''.join(captcha_text)

    if is_save:
        # 图片路径
        file_name_ = file_name if file_name else captcha_text
        file_name = "{}.{}".format(file_name_, suffix)
        file_path = os.path.join(image_path, file_name)

        # 设置颜色
        background = (255, 255, 255)  # 白色
        color = (220, 0, 0)  # 红色

        # 在write中会随机字体大小颜色和背景色
        # image_captcha.write(captcha_text, file_path)
        img = image_captcha.create_captcha_image(captcha_text, color, background)

        # 保存图片
        img.save(file_path)
        return captcha_text, file_path
    else:
        # 进一步处理图片
        captcha = image_captcha.generate(captcha_text)
        captcha_image = Image.open(captcha)
        captcha_image = np.array(captcha_image)
        return captcha_text, captcha_image


def show_image():
    """显示图片
    """
    text, image = gen_captcha_text_and_image(False)

    f = plt.figure()
    ax = f.add_subplot(111)
    ax.text(0.1, 0.9, text, ha='center', va='center', transform=ax.transAxes)
    plt.imshow(image)

    plt.show()


def test():
    """测试
    """
    gen_captcha_text_and_image(True, "./")
    show_image()


if __name__ == '__main__':
    img, text = create_validate_code()
    img.save("test.png")
    test()
