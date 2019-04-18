#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: ioloop_test
#         Desc: 测试ioloop使用
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-12-13 20:28
#=============================================================================
"""

import time
import threading
import tornado.ioloop
from tornado.concurrent import Future

io_loop = tornado.ioloop.IOLoop.current()


def long_task(future, sec=5):
    print "long task start"
    time.sleep(sec)
    future.set_result("long task done in %s sec" % sec)


def after_task_done(future):
    print "future result: %s" % future.result()


def test_future():
    print "start..."
    future = Future()
    threading.Thread(target=long_task, args=(future,)).start()
    io_loop.add_future(future, after_task_done)
    print "end..."


if __name__ == "__main__":
    io_loop.add_callback(test_future)
    io_loop.start()
