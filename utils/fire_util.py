#!/usr/bin/env python
# -*- coding:utf-8 -*-

import fire


class Example(object):
    def __init__(self):
        pass

    def hello(self, name="world"):
        """

        :param name:
        :return:
        """
        msg = "Hello {name}".format(name=name)
        return msg


def main():
    fire.Fire(Example)


if __name__ == "__main__":
    main()

"""
使用方式
github地址：https://github.com/google/python-fire
安装： pip install fire
./fire_util.py hello
./fire_util.py hello HJD
./fire_util.py hello --name=Google
"""