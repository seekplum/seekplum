#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import pytest


def print_text(text):
    print text


def main():
    # parametrize 中需要对每个测试用例指定id,对应不上会导致整个test文件无法运行
    curr_path = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(curr_path, "test.py")
    if os.path.exists(file_path):
        print_text("测试文件: %s" % file_path)
        # 测试单个文件
        pytest.main(file_path)
    else:
        print_text("测试目录: %s" % curr_path)
        # 测试整个目录下的文件
        pytest.main(curr_path)


if __name__ == '__main__':
    main()
