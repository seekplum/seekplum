#!/usr/bin/python env
# -*- coding:utf-8 -*-
"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: identify_code
#          Desc: 识别验证码,识别验证码通常是这几个步骤：
        　　　　1、灰度处理
        　　　　2、二值化
        　　　　3、去除边框（如果有的话）
        　　　　4、降噪
        　　　　5、切割字符或者倾斜度矫正
        　　　　6、训练字体库
        　　　　7、识别
#       Author: hjd
#   LastChange: 2018-03-22 22:51
#=============================================================================
"""

import os

from Queue import Queue

import cv2

from PIL import Image, ImageDraw
from pytesseract import image_to_string


class FileTypeError(Exception):
    """文件类型错误
    """
    pass


class FilePathError(Exception):
    """文件路径错误
    """
    pass


class PixelError(Exception):
    """坐标错误
    """
    pass


def generate_alias_name(file_path, suffix, separator="."):
    """生成别名，保留后缀格式不变

    :param file_path: str 文件全路径
    :param suffix: str 要增加的后缀
    :param separator: str 分隔符，默认为 `.`

    :return: 生成后的文件名

    :raise ValueError 分割符不在文件名中
    """
    parent_directory = os.path.dirname(file_path)
    # 获取文件名和类型
    file_name, file_type = os.path.basename(file_path).rsplit(separator, 1)
    # 生成新的文件路径
    new_path = os.path.join(parent_directory, "{}{}{}{}".format(file_name, suffix, separator, file_type))
    return new_path


def get_dynamic_binary_image(image_path):
    """自适应阀值二值化

    灰度处理，就是把彩色的验证码图片转为灰色的图片。

　　二值化，是将图片处理为只有黑白两色的图片，利于后面的图像处理和识别

    :param image_path: str 图片路径

    :rtype numpy.ndarray, str
    :returns 图片二维坐标，新的图片路径
    """
    # 生成新的图片，不影响原来的文件
    # new_image_path = generate_alias_name(image_path, suffix="_binary")
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 灰值化
    # 二值化
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 1)
    cv2.imwrite(image_path, img)
    return img


def get_static_binary_image(image_path, threshold=150):
    """手动二值化

    1. 对于超过阀值的设置成白色,文字部分设置黑色
    2. 重新保存图片

    :param image_path: str 图片路径
    :param threshold: int 阀值

    :rtype str
    :return 处理之后的文件路径
    """
    img = Image.open(image_path)
    img = img.convert('L')
    pix_data = img.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            if pix_data[x, y] < threshold:
                pix_data[x, y] = 0
            else:
                pix_data[x, y] = 255

    image = Image.new("1", img.size)
    draw = ImageDraw.Draw(image)

    for x in xrange(0, width):
        for y in xrange(0, height):
            draw.point((x, y), pix_data[(x, y)])
    new_image_path = generate_alias_name(image_path, suffix="_static")
    image.save(new_image_path)
    return new_image_path


def clear_border(img, image_path):
    """去除边框

    去除边框就是遍历像素点，找到四个边框上的所有点，把他们都改为白色

    注意：在用OpenCV时，图片的矩阵点是反的，就是长和宽是颠倒的

    :param img: `numpy.ndarray` 图片对象
    :param image_path: str 图片路径

    :rtype numpy.ndarray
    :returns 图片二维坐标
    """
    height, width = img.shape[:2]
    for y in range(0, width):
        for x in range(0, height):
            # if y ==0 or y == width -1 or y == width - 2:
            if y < 4 or y > width - 4:
                img[x, y] = 255
            # if x == 0 or x == width - 1 or x == width - 2:
            if x < 4 or x > height - 4:
                img[x, y] = 255
    cv2.imwrite(image_path, img)
    return img


def interference_line(img, image_path):
    """降噪去除干扰线

    线降噪的思路就是检测这个点相邻的四个点，判断这四个点中是白点的个数，
    如果有两个以上的白色像素点，那么就认为这个点是白色的，从而去除整个干扰线，
    但是这种方法是有限度的，如果干扰线特别粗就没有办法去除，只能去除细的干扰线

    :param img: `numpy.ndarray` 图片对象
    :param image_path: str 图片路径

    :rtype numpy.ndarray
    :returns 图片二维坐标
    """
    height, width = img.shape[:2]
    value = 245
    for y in range(1, width - 1):
        for x in range(1, height - 1):
            count = 0
            if img[x, y - 1] > value:
                count += 1
            if img[x, y + 1] > value:
                count += 1
            if img[x - 1, y] > value:
                count += 1
            if img[x + 1, y] > value:
                count += 1
            if count > 2:
                img[x, y] = 255
    cv2.imwrite(image_path, img)
    return img


def interference_point(img, image_path, x=0, y=0):
    """降噪去除干扰点

    邻域框,以当前点为中心的田字框,黑点个数

    :param img: `numpy.ndarray` 图片对象
    :param image_path: str 图片路径
    :param x: int 开始像素点的横坐标
    :param y: int 开始像素点的纵坐标

    :rtype numpy.ndarray
    :returns 图片二维坐标
    """
    height, width = img.shape[:2]
    # 检查x,y 坐标值是否有效
    if x > height or x < 0 or y > width or y < 0:
        raise PixelError("({}, {}) beyond ({}, {})".format(x, y, height, width))
    curr_pixel = img[x, y]  # 当前像素点的值
    for y in range(1, width - 1):
        for x in range(1, height - 1):
            if y == 0:  # 第一行
                if x == 0:  # 左上顶点,4邻域
                    # 中心点旁边3个点
                    number = int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x + 1, y]) \
                             + int(img[x + 1, y + 1])
                    if number <= 2 * 245:
                        img[x, y] = 0
                elif x == height - 1:  # 右上顶点
                    number = int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x - 1, y]) \
                             + int(img[x - 1, y + 1])
                    if number <= 2 * 245:
                        img[x, y] = 0
                else:  # 最上非顶点,6邻域
                    number = int(img[x - 1, y]) \
                             + int(img[x - 1, y + 1]) \
                             + int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x + 1, y]) \
                             + int(img[x + 1, y + 1])
                    if number <= 3 * 245:
                        img[x, y] = 0
            elif y == width - 1:  # 最下面一行
                if x == 0:  # 左下顶点
                    # 中心点旁边3个点
                    number = int(curr_pixel) \
                             + int(img[x + 1, y]) \
                             + int(img[x + 1, y - 1]) \
                             + int(img[x, y - 1])
                    if number <= 2 * 245:
                        img[x, y] = 0
                elif x == height - 1:  # 右下顶点
                    number = int(curr_pixel) \
                             + int(img[x, y - 1]) \
                             + int(img[x - 1, y]) \
                             + int(img[x - 1, y - 1])

                    if number <= 2 * 245:
                        img[x, y] = 0
                else:  # 最下非顶点,6邻域
                    number = int(curr_pixel) \
                             + int(img[x - 1, y]) \
                             + int(img[x + 1, y]) \
                             + int(img[x, y - 1]) \
                             + int(img[x - 1, y - 1]) \
                             + int(img[x + 1, y - 1])
                    if number <= 3 * 245:
                        img[x, y] = 0
            else:  # y不在边界
                if x == 0:  # 左边非顶点
                    number = int(img[x, y - 1]) \
                             + int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x + 1, y - 1]) \
                             + int(img[x + 1, y]) \
                             + int(img[x + 1, y + 1])

                    if number <= 3 * 245:
                        img[x, y] = 0
                elif x == height - 1:  # 右边非顶点
                    number = int(img[x, y - 1]) \
                             + int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x - 1, y - 1]) \
                             + int(img[x - 1, y]) \
                             + int(img[x - 1, y + 1])

                    if number <= 3 * 245:
                        img[x, y] = 0
                else:  # 具备9领域条件的
                    number = int(img[x - 1, y - 1]) \
                             + int(img[x - 1, y]) \
                             + int(img[x - 1, y + 1]) \
                             + int(img[x, y - 1]) \
                             + int(curr_pixel) \
                             + int(img[x, y + 1]) \
                             + int(img[x + 1, y - 1]) \
                             + int(img[x + 1, y]) \
                             + int(img[x + 1, y + 1])
                    if number <= 4 * 245:
                        img[x, y] = 0
    cv2.imwrite(image_path, img)
    return img


def detect_block_point(img, x_max):
    """搜索区块起点

    :param img: `numpy.ndarray` 图片对象
    :param x_max: int x 横坐标

    :rtype numpy.ndarray
    :returns 图片二维坐标
    """
    height, width = img.shape[:2]
    for y_fd in range(x_max + 1, width):
        for x_fd in range(height):
            if img[x_fd, y_fd] == 0:
                return x_fd, y_fd


def completely_fair_scheduler(img, x_fd, y_fd):
    """用队列和集合记录遍历过的像素坐标代替单纯递归以解决cfs访问过深问题

    :param img: `numpy.ndarray` 图片对象
    :param x_fd: int x 横坐标
    :param y_fd: int y 纵坐标

    :rtype int, int, int, int
    :returns y坐标最大值，y坐标最小值，x坐标最大值，x坐标最小值
    """
    x_axis = []
    y_axis = []
    visited = set()
    q = Queue()
    q.put((x_fd, y_fd))
    visited.add((x_fd, y_fd))
    offsets = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # 四邻域

    while not q.empty():
        x, y = q.get()
        for x_offset, y_offset in offsets:
            x_neighbor, y_neighbor = x + x_offset, y + y_offset
            if (x_neighbor, y_neighbor) in visited:
                continue  # 已经访问过了
            visited.add((x_neighbor, y_neighbor))
            try:
                if img[x_neighbor, y_neighbor] == 0:
                    x_axis.append(x_neighbor)
                    y_axis.append(y_neighbor)
                    q.put((x_neighbor, y_neighbor))

            except IndexError:
                pass
    if len(x_axis) == 0 or len(y_axis) == 0:
        x_max = x_fd + 1
        x_min = x_fd
        y_max = y_fd + 1
        y_min = y_fd
    else:
        x_max = max(x_axis)
        x_min = min(x_axis)
        y_max = max(y_axis)
        y_min = min(y_axis)
    return y_max, y_min, x_max, x_min


def cut_position_block(img):
    """切割图片中的字符

    字符切割通常用于验证码中有粘连的字符，粘连的字符不好识别，所以我们需要将粘连的字符切割为单个的字符，在进行识别

　　字符切割的思路就是找到一个黑色的点，然后在遍历与他相邻的黑色的点，直到遍历完所有的连接起来的黑色的点，
    找出这些点中的最高的点、最低的点、最右边的点、最左边的点，记录下这四个点，认为这是一个字符，
    然后在向后遍历点，直至找到黑色的点，继续以上的步骤。最后通过每个字符的四个点进行切割

    :param img: `numpy.ndarray` 图片对象

    :rtype list, list, list
    :returns 各区块长度列表 各区块的X轴[起始，终点]列表 各区块的Y轴[起始，终点]列表
    (
        [14, 13, 14, 14], # 各个字符长度
        [[4, 18], [28, 41], [49, 63], [72, 86]], # 字符 X 轴[起始，终点]位置
        [[6, 32], [14, 28], [8, 29], [8, 28]]  # 字符 Y 轴[起始，终点]位置
    )
    """
    zone_length = []  # 各区块长度列表
    zone_width = []  # 各区块的X轴[起始，终点]列表
    zone_height = []  # 各区块的Y轴[起始，终点]列表

    x_max = 0  # 上一区块结束黑点横坐标,这里是初始化
    for i in range(10):

        try:
            x_fd, y_fd = detect_block_point(img, x_max)
            x_max, x_min, y_max, y_min = completely_fair_scheduler(img, x_fd, y_fd)
            length = x_max - x_min
            zone_length.append(length)
            zone_width.append([x_min, x_max])
            zone_height.append([y_min, y_max])
        except TypeError:
            return zone_length, zone_width, zone_height

    return zone_length, zone_width, zone_height


def get_stick_together_position(img):
    """查询粘在一起的字符的切割位置

    如果有粘连字符，如果一个字符的长度过长就认为是粘连字符，并从中间进行切割

    :param img: `numpy.ndarray` 图片对象

    :rtype tuple
    :return
    (
        [14, 13, 14, 14], # 各个字符长度
        [[4, 18], [28, 41], [49, 63], [72, 86]], # 字符 X 轴[起始，终点]位置
        [[6, 32], [14, 28], [8, 29], [8, 28]]  # 字符 Y 轴[起始，终点]位置
    )
    """
    # 切割的位置
    img_position = cut_position_block(img)

    max_length = max(img_position[0])
    min_length = min(img_position[0])

    # 如果有粘连字符，如果一个字符的长度过长就认为是粘连字符，并从中间进行切割
    if max_length > (min_length + min_length * 0.7):
        max_length_index = img_position[0].index(max_length)
        # 设置字符的宽度
        img_position[0][max_length_index] = max_length // 2
        img_position[0].insert(max_length_index + 1, max_length // 2)
        # 设置字符X轴[起始，终点]位置
        img_position[1][max_length_index][1] = img_position[1][max_length_index][0] + max_length // 2
        img_position[1].insert(max_length_index + 1,
                               [img_position[1][max_length_index][1] + 1,
                                img_position[1][max_length_index][1] + 1 + max_length // 2])
        # 设置字符的Y轴[起始，终点]位置
        img_position[2].insert(max_length_index + 1, img_position[2][max_length_index])
    return img_position


def cutting_img(img, img_position, image_path, x_offset=1, y_offset=1):
    """切割图片

    切割字符，要想切得好就得配置参数，通常 1 or 2 就可以

    :param img: `numpy.ndarray` 图片对象
    :param img_position: type 各个字符信息
            比如 (
                    [14, 13, 14, 14], # 各个字符长度
                    [[4, 18], [28, 41], [49, 63], [72, 86]], # 字符 X 轴[起始，终点]位置
                    [[6, 32], [14, 28], [8, 29], [8, 28]]  # 字符 Y 轴[起始，终点]位置
                )
    :param image_path: str 图片路径
    :param x_offset: int X 轴偏移位置
    :param y_offset: int Y 轴偏移位置

    :rtype set()
    :return: 切割之后的路径集合
    """
    # 识别出的字符个数
    im_number = len(img_position[1])
    # 切割字符
    paths = set()
    for i in range(im_number):
        img_start_x = img_position[1][i][0] - x_offset
        img_end_x = img_position[1][i][1] + x_offset
        img_start_y = img_position[2][i][0] - y_offset
        img_end_y = img_position[2][i][1] + y_offset
        cropped = img[img_start_y:img_end_y, img_start_x:img_end_x]

        new_image_path = generate_alias_name(image_path, suffix="cut_{}".format(i))
        cv2.imwrite(new_image_path, cropped)

        paths.add(new_image_path)
    return paths


def identify_code(paths):
    """识别验证码

    识别用的是typesseract库，主要识别一行字符和单个字符时的参数设置，识别中英文的参数设置

    :param paths: iter 路径列表

    :rtype str
    :return 图片中的文字
    """
    result = []
    for image_path in paths:
        try:
            # 识别字符
            img_text = image_to_string(Image.open(image_path), lang='eng', config='-psm 10')  # 单个字符是10，一行文本是7
        except Exception as e:
            print("{} error: {}".format(image_path, e.message))
        else:
            result.append(img_text)
    return "".join(reversed(result))


def check_image_path_valid(image_path):
    """检查图片路径是否合法

    1. 检查路径是否为绝对路径
    2. 检查是否存在
    3. 检查类型是否为文件

    :param image_path: str 图片路径

    :rtype str
    :return 有效的图片路径
    """
    abs_image_path = os.path.abspath(image_path)
    if not os.path.exists(abs_image_path):
        raise IOError("{} file does not exist".format(image_path))
    if not os.path.isfile(abs_image_path):
        raise FileTypeError("{} is not a file".format(image_path))
    return abs_image_path


def identify_image_verification_code(image_path):
    """
    解析图片中的验证码

    1. 自适应阈值二值化
    2. 去除边框
    3. 对图片进行干扰线降噪
    4. 对图片进行点降噪
    5. 对字符进行切割
    6. 识别验证码

    :param image_path: str 图片路径
    """
    # 检查图片路径是否合法
    image_path = check_image_path_valid(image_path)

    # 手动二值化
    new_image_path = get_static_binary_image(image_path, threshold=100)

    # 自适应阀值二值化
    img = get_dynamic_binary_image(new_image_path)

    # 去除边框
    img = clear_border(img, new_image_path)

    # 降噪去除干扰线
    img = interference_line(img, new_image_path)

    # 降噪去除干扰点
    img = interference_point(img, new_image_path)

    # 查询粘在一起的字符的切割位置
    img_position = get_stick_together_position(img)

    # 切割图片
    paths = cutting_img(img, img_position, new_image_path, 1, 1)

    # 识别验证码
    text = identify_code(paths)

    # 删除生成的文件
    paths.add(new_image_path)
    map(os.remove, paths)
    return text


def test_identify():
    images = [
        {
            "path": "authcode.png",
            "result": "dxg8"
        },
        {
            "path": "captcha.png",
            "result": "qjwb"
        },
    ]
    for item in images:
        image_path = item["path"]
        result = item["result"]
        text = identify_image_verification_code(image_path)
        print("=" * 100)
        print("path: {}, result: {}, text: {}".format(image_path, result, text))
        print("=" * 100)


if __name__ == '__main__':
    test_identify()
