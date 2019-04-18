#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
在Python3中生效
"""


# def apply_async(func, *args, callback):
#     result = func(*args)
#     callback(result)
#
#
# def make_handler1():
#     sequence = 0
#
#     def handler(result):
#         nonlocal sequence  # 声明变量会在回调函数中被修改
#         sequence += 1
#         print('[{}] Got: {}'.format(sequence, result))
#
#     return handler


def print_result(result):
    print('Got:', result)


class ResultHandler:

    def __init__(self):
        self.sequence = 0

    def handler(self, result):
        self.sequence += 1
        print('[{}] Got: {}'.format(self.sequence, result))


def make_handler():
    sequence = 0
    while True:
        result = yield
        sequence += 1
        print("[{}] Got1: {}".format(sequence, result))
        result1 = yield
        sequence += 1
        print("[{}] Got2: {}".format(sequence, result1))


def add(x, y):
    return x + y


# def test1():
#     apply_async(add, 2, 3, callback=print_result)
#
#
# def test2():
#     handler = make_handler1()
#     apply_async(add, 2, 3, callback=handler)
#
#
# def test3():
#     r = ResultHandler()
#     apply_async(add, 2, 3, callback=r.handler)
#
#
# def test4():
#     handler = make_handler()
#     next(handler)  # 和 handler.send(None) 等价
#     apply_async(add, 2, 3, callback=handler.send)
#     apply_async(add, 2, 3, callback=handler.send)
#     apply_async(add, 2, 3, callback=handler.send)
#     apply_async(add, 2, 3, callback=handler.send)


def make_handler_python2():
    print('start ...')
    start = yield 5
    print start
    end = yield 12
    print("end ... {}".format(end))


def test_python3():
    pass
    # test1()
    # test2()
    # test3()
    # test4()


def test_python2():
    handler = make_handler_python2()
    start = handler.next()  # start 获取了yield 5 的参数值 5
    end = handler.send('Fighting!')  # end 获取了yield 12 的参数值12
    print("start={},end={}".format(start, end))


if __name__ == '__main__':
    test_python2()
