#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import logging
import json
import time
import sys

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options

from concurrent.futures import ThreadPoolExecutor
from tornado.options import options
from tornado.options import define
from tornado.web import gen
from tornado.web import Finish
from tornado.web import URLSpec as U
from tornado.web import RequestHandler

COMMAND_EXECUTOR = ThreadPoolExecutor(30)
logger = logging.getLogger(__name__)


class ApiHandler(RequestHandler):
    executor = ThreadPoolExecutor(30)

    def write_json(self, data):
        real_ip = self.request.headers.get('X-Real-Ip', "unknown")
        logger.info("method: {}, uri: {}, real ip: {}, remote ip: {}, start time: {}, finish_time: {}, "
                    "error_code: {}".format(self.request.method, self.request.uri, real_ip, self.request.remote_ip,
                                            self.request._start_time, time.time(), data["error_code"]))
        self.set_header("Content-Type", "application/json")
        if options.debug:
            self.write(json.dumps(data, indent=2))
        else:
            self.write(json.dumps(data))

    def success_response(self, data=None, message="", finish=True):
        response = {
            "error_code": 0,
            "message": message,
            "data": data
        }
        self.write_json(response)
        if finish:
            raise Finish


def run_on_executor(executor):
    def run_on_executor_decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return executor.submit(fn, *args, **kwargs)

        return wrapper

    return run_on_executor_decorator


@run_on_executor(executor=COMMAND_EXECUTOR)
def exec_command(host, cmd):
    """线程executor pool中执行耗时命令

    :param host: 主机
    :param cmd: 命令
    """
    time.sleep(2)
    return {
        "host": host,
        "cmd": cmd
    }


class CommandMixin(object):
    def __init__(self):
        pass

    def exec_command(self, host, cmd):
        future = exec_command(host, cmd)
        return future


class BaseTestManager(CommandMixin):
    @staticmethod
    def get_func_name():
        # func_name = sys._getframe().f_code.co_name # 获取当前函数名
        return sys._getframe().f_back.f_code.co_name  # 获取调用函数名

    @gen.coroutine
    def get_physical_flash(self, ip):
        func_name = self.get_func_name()
        future = self.exec_command(ip, func_name)
        data = yield future
        raise gen.Return(data)

    @gen.coroutine
    def get_physical_disk(self, ip):
        func_name = self.get_func_name()
        data = yield self.exec_command(ip, func_name)
        raise gen.Return(data)

    @gen.coroutine
    def get_physical_nvme(self, ip):
        func_name = self.get_func_name()
        data = yield self.exec_command(ip, func_name)
        raise gen.Return(data)

    @gen.coroutine
    def get_logical_flash(self, ip):
        func_name = self.get_func_name()
        data = yield self.exec_command(ip, func_name)
        raise gen.Return(data)

    @gen.coroutine
    def get_logical_disk(self, ip):
        func_name = self.get_func_name()
        data = yield self.exec_command(ip, func_name)
        raise gen.Return(data)

    @gen.coroutine
    def get_logical_nvme(self, ip):
        func_name = self.get_func_name()
        data = yield self.exec_command(ip, func_name)
        raise gen.Return(data)


class TestHandler(ApiHandler, BaseTestManager):
    @gen.coroutine
    def get(self, node_id):
        """
        获取Flash的物理信息
        :param node_id: 节点id
        :return:
        """
        node_ip = "10.10.100.%s" % node_id

        physical_flash = yield self.get_physical_flash(node_ip)
        # physical_disk = yield self.get_physical_disk(node_ip)
        # physical_nvme = yield self.get_physical_nvme(node_ip)
        #
        # logical_flash = yield self.get_logical_flash(node_ip)
        # logical_disk = yield self.get_logical_disk(node_ip)
        # logical_nvme = yield self.get_logical_nvme(node_ip)

        data = {
            "physical_flash": physical_flash,
            # "physical_disk": physical_disk,
            # "physical_nvme": physical_nvme,
            # "logical_flash": logical_flash,
            # "logical_disk": logical_disk,
            # "logical_nvme": logical_nvme,
        }

        self.success_response(data)


class ThreadPoolHandler(object):
    def __init__(self, max_workers=None):
        """通过线程池执行多种类型的多个耗时任务

        注意： max_workers 参数会影响线程数量，进而影响执行速度，建议使用默认值 `None`

        :param max_workers 线程池大小
        :type max_workers int
        """
        self._thread_pool = ThreadPoolExecutor(max_workers)
        self._result = {}
        self._futures = []

        self._funcs = []

    def _complete(self, category, future):
        """任务执行完成对结果进行分类

        :param category 任务的类型
        :type category str

        :param future 任务对象
        :type future concurrent.futures._base.Future
        """
        self._result.setdefault(category, []).append(future.result())

    def add_task(self, func, category, *args, **kwargs):
        """添加在线程池中执行的任务

        :param func 在线程中执行的函数

        :param category 任务的类型
        :type category str

        :param args func的位置参数
        :type args tuple

        :param kwargs func的关键字参数
        :type kwargs dict
        """
        future = self._thread_pool.submit(func, *args, **kwargs)
        future.add_done_callback(lambda x: self._complete(category, future))
        self._futures.append(future)

    def get_result(self):
        """查询执行结果

        :rtype dict
        :return 按照 `category` 分组的结果
        """
        # 等待所有任务执行完
        while not all([f.done() for f in self._futures]):
            pass
        return self._result

    def future_func(self, func, category, *args, **kwargs):
        result = yield func(*args, **kwargs)
        self._result.setdefault(category, []).append(result)
        # raise gen.Return(result)

    def add_async_task(self, func, category, *args, **kwargs):
        """添加在线程池中执行的任务

        :param func 在线程中执行的函数

        :param category 任务的类型
        :type category str

        :param args func的位置参数
        :type args tuple

        :param kwargs func的关键字参数
        :type kwargs dict
        """
        future = self._thread_pool.submit(self.future_func, func, category, *args, **kwargs)
        # future.add_done_callback(lambda x: self._async_complete(category, future))
        self._futures.append(future)

    def _async_complete(self, category, future):

        """任务执行完成对结果进行分类

        :param category 任务的类型
        :type category str

        :param future 任务对象
        :type future concurrent.futures._base.Future
        """
        self._result.setdefault(category, []).append(future.result())

    def get_async_result(self):
        """查询执行结果

        :rtype dict
        :return 按照 `category` 分组的结果
        """
        # 等待所有任务执行完
        result = []
        while True:
            for future in self._futures:
                if not (future.done()):
                    break
                tornado_future = future.result()
                try:
                    f = next(tornado_future)
                    info = f.result()
                except Exception as e:
                    break
                if info:
                    result.append(info)
            else:
                if self._futures:
                    break

        return result
        # return self._result
        # # 等待所有任务执行完
        # result = []
        # for future in self._futures:
        #     print "future: %s" % type(future)
        #     tornado_future = future.result()
        #     print "done: %s" % tornado_future.done()
        #     print "tornado_future: %s" % type(tornado_future)
        #     data = tornado_future.result()
        #     print "data: %s" % type(data)
        #     result.append(data)
        # return result


class Test1Handler(ApiHandler, BaseTestManager):
    @gen.coroutine
    def get(self, node_id):
        """
        获取Flash的物理信息
        :param node_id: 节点id
        :return:
        """
        node_ip = "10.10.100.%s" % node_id

        thread_pool = ThreadPoolHandler()
        thread_pool.add_async_task(self.get_physical_flash, "physical_flash", node_ip)
        thread_pool.add_async_task(self.get_physical_disk, "physical_disk", node_ip)
        thread_pool.add_async_task(self.get_physical_nvme, "physical_nvme", node_ip)
        thread_pool.add_async_task(self.get_logical_flash, "logical_flash", node_ip)
        thread_pool.add_async_task(self.get_logical_disk, "logical_disk", node_ip)
        thread_pool.add_async_task(self.get_logical_nvme, "logical_nvme", node_ip)

        data = thread_pool.get_async_result()

        self.success_response(data)


define("port", default=11100, help="run on the given port", type=int)
define("debug", default=False, help="start debug mode", type=bool)

COOKIE_SECRET = "12345678"


class Application(tornado.web.Application):
    def __init__(self):
        app_settings = dict(
            cookie_secret=COOKIE_SECRET,
            debug=options.debug,
        )

        test_urls = [
            U(r"/seekplum/test/(?P<node_id>[\d]+)", TestHandler),  # 测试使用
            U(r"/seekplum/test1/(?P<node_id>[\d]+)", Test1Handler),  # 测试使用
        ]

        super(Application, self).__init__(test_urls, **app_settings)


def main():
    tornado.options.parse_command_line()
    app = Application()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    logger.info("Server start on port %s", options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
