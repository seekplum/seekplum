# -*- coding: utf-8 -*-

import time

from concurrent.futures import ThreadPoolExecutor


def test1(x):
    time.sleep(1)
    return {x: x}


def test2(x):
    time.sleep(1)
    return {x: x * x}


def test3(x):
    time.sleep(1)
    return {x: x + x}


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


if __name__ == '__main__':
    number = 10
    pool = ThreadPoolHandler()
    start_time = time.time()
    for i in range(number):
        pool.add_task(test1, "test1", (i,))
        pool.add_task(test2, "test2", (i,))
        pool.add_task(test3, "test3", (i,))
    data = pool.get_result()
    end_time = time.time()
    print "=" * 100
    print end_time - start_time
    print data
    print "=" * 100
