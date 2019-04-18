#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

UNIT = 1024
B = 1
KB = B * UNIT
MB = KB * UNIT
GB = MB * UNIT
TB = GB * UNIT
PB = TB * UNIT
UNIT_MAP = {
    "B/s": B,
    "KB/s": KB,
    "MB/s": MB,
    "GB/s": GB,
    "TB/s": TB,
    "PB/s": PB,
}


def conversion_unit(size, target_unit="B/s"):
    """转换单位

    :rtype float
    :return 转换为字节b的大小
    """
    number, unit = split_unit(size)
    return UNIT_MAP[unit] * number * 1.0 / UNIT_MAP[target_unit]


def split_unit(size):
    """拆分数值和单位
    """
    pattern = re.compile(r"([\d\.]+)\s*([\w\/]+)")
    match = pattern.search(size)
    number, unit = float(match.group(1)), match.group(2)
    return number, unit


def conversion_biggest_unit(size):
    """转成成最大的单位
    """
    number = conversion_unit(size, "B/s")
    items = [(k, number / v) for k, v in UNIT_MAP.items() if (number / v) > 1]
    items.sort(key=lambda x: x[1])
    new_unit = items[0][0]
    new_size = items[0][1]
    # 还可以换成成更大的单位
    if new_size > UNIT:
        return conversion_biggest_unit(
            "{}{}".format(new_size, new_unit))
    return "{:.2f}{}".format(new_size, new_unit)


def analysis_data(data):
    """分析数据
    """
    min_value = min(data)
    max_value = max(data)
    diff = max_value - min_value
    avg = sum(data) / len(data) / 1.0
    return diff, min_value, avg, max_value


def difference_bw(data):
    diff, min_value, avg, max_value = analysis_data(data)
    return len(data), conversion_biggest_unit("{}B/s".format(diff)), conversion_biggest_unit(
        "{}B/s".format(min_value)), conversion_biggest_unit(
        "{}B/s".format(avg)), conversion_biggest_unit("{}B/s".format(max_value))


def difference_iops(data):
    diff, min_value, avg, max_value = analysis_data(data)
    return len(data), diff, min_value, avg, max_value


class CheckFio(object):
    def __init__(self, root):
        self._root = root
        self._read_bw = []
        self._read_iops = []
        self._write_bw = []
        self._write_iops = []

    def _compare_fio(self, result):
        for item in result:
            mode = item[0]
            bw = conversion_unit(item[1])
            iops = float(item[2])
            if mode == "read":
                self._read_bw.append(bw)
                self._read_iops.append(iops)
            else:
                self._write_bw.append(bw)
                self._write_iops.append(iops)

    def _collect(self):
        pattern = re.compile(r'(read|write)\s*: io=[\w\.]+, bw=([\d\.]+[\w\/]+), iops=(\d+)')
        for file_name in os.listdir(self._root):
            path = os.path.join(self._root, file_name)
            if not os.path.isdir(path):
                continue
            for txt_name in os.listdir(path):
                with open(os.path.join(path, txt_name), "r") as f:
                    content = f.read()
                self._compare_fio(pattern.findall(content))

    @staticmethod
    def _print_info(title, data):
        print "{}, fio测试次数: {}, 最大最小差值: {}, 最小值: {}, 平均值: {}, 最大值: {}".format(title, *data)

    def compare(self):
        self._collect()
        self._print_info("[随机读写-读] bw(吞吐)", difference_bw(self._read_bw))
        self._print_info("[随机读写-写] bw(吞吐)", difference_bw(self._write_bw))
        self._print_info("[随机读写-读] iops", difference_iops(self._read_iops))
        self._print_info("[随机读写-写] iops,", difference_iops(self._write_iops))


if __name__ == '__main__':
    check = CheckFio("/root/fio-test")
    check.compare()
