#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from time import sleep


def view(i):
    """
    进度条效果
    :param i:
    :return:
    """
    print "开始解压"
    output = sys.stdout
    for count in range(0, i + 1):
        second = 0.1
        sleep(second)
        output.write('\rcomplete percent ----->:%.0f%%' % count)
    output.flush()
    print "\n解压从成功"


def progress_test():
    bar_length = 20
    for percent in xrange(0, 101):
        hashes = '#' * int(percent / 100.0 * bar_length)
        spaces = ' ' * (bar_length - len(hashes))
        sys.stdout.write("\rPercent: [%s] %d%%" % (hashes + spaces, percent))
        sys.stdout.flush()
        sleep(0.1)


def speed():
    n = 20
    while n > 0:
        sleep(5)
        print ".",
        # 刷新stdout， 及时输出
        sys.stdout.flush()
        n -= 1


def copy():
    t = 0
    while t < 1000:
        a = ["|", "/", "-", "\\"]
        for i in a:
            # sys.stdout.write("\b{0}\b".format(i))
            sys.stdout.write("\r{0}".format(i))
            sys.stdout.flush()
            sleep(0.05)
        t += 1


if __name__ == '__main__':
    copy()
