# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: hello_world
#         Desc: 官方示例代码
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-12-22 17:23
#=============================================================================
"""
from __future__ import print_function

import time
import threading

from tornado.ioloop import IOLoop

from tornado.web import Application, RequestHandler

from tornado import gen
from concurrent.futures import ThreadPoolExecutor

import redis_utils


class Result(object):
    def __init__(self):
        self._value = None
        self._evt = threading.Event()
        # self.__running = False

    def set_result(self, value):
        self._value = value
        self._evt.set()
        # self.__running = True

    def result(self):
        self._evt.wait()
        # while not self.__running:
        #     pass
        return self._value


class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)

        return cls._instance


class Scheduler(Singleton):
    def __init__(self):
        self._result_queue = set()

    def add_result(self, r):
        self._result_queue.add(r)
        print("length: ", len(self._result_queue))

    def set_result(self, value):
        while self._result_queue:
            r = self._result_queue.pop()
            r.set_result(value)


def get_message(sleep_time):
    time.sleep(sleep_time)
    msg = "Hello, world " + "\n"
    return msg


class MainHandler(RequestHandler):
    _executor = ThreadPoolExecutor(30)
    _scheduler = Scheduler()

    def do(self):
        r_client = redis_utils.redis_connect("127.0.01", 6379)
        with redis_utils.redis_lock("hello", r_client) as is_lock:
            if is_lock:
                print("start task...")
                msg = get_message(3)
                print("end task")
                self._scheduler.set_result(msg)
            else:
                print("task is running")

    @gen.coroutine
    def get(self):
        r = Result()
        self._scheduler.add_result(r)
        yield self._executor.submit(self.do)
        data = r.result()
        self.write(data)


def make_app():
    return Application([
        (r"/", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(12345)
    print("http://127.0.0.1:12345/")
    IOLoop.current().start()
