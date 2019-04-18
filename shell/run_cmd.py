#!usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import subprocess


def run(cmd):
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    std_out, _ = p.communicate()
    return std_out


def sys_name():
    print sys._getframe().f_code.co_filename  # 当前文件名，可以通过__file__获得
    print sys._getframe(0).f_code.co_name  # 当前函数名
    print sys._getframe(1).f_code.co_name  # 调用该函数的函数的名字，如果没有被调用，则返回<module>，貌似call stack的栈低
    print sys._getframe().f_lineno  # 当前行号
    print sys._getframe().f_code.co_name  # 当前函数名


if __name__ == '__main__':
    hostname = run("hostname")
    print hostname
