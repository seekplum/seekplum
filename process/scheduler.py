#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
project name: ${PROJECT_NAME}
file name: ${NAME}
author: ${USER}
create time:  ${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}

┏┓ ┏┓
┏┛┻━━━┛┻┓
┃ ☃ ┃
┃ ┳┛ ┗┳ ┃
┃ ┻ ┃
┗━┓ ┏━┛
┃ ┗━━━┓
┃ 神兽保佑 ┣┓
┃　永无BUG！ ┏┛
┗┓┓┏━┳┓┏┛
┃┫┫ ┃┫┫
┗┻┛ ┗┻┛
"""
'''

# from pytz import utc
# import time
# from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
# from apscheduler.jobstores.mongodb import MongoDBJobStore
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
#
import time
import signal
import psutil
import threading
from datetime import datetime
from multiprocessing import Process, Queue

import logging


class Timer(threading.Thread):
    def __init__(self, job, interval, job_args=None, job_kwargs=None, job_lable=None, share=False):
        """

        :param job: 执行任务
        :param interval: 时间间隔
        :param job_args: 位置参数
        :param job_kwargs: 可选参数
        :param job_lable: 任务标记
        :param share: 是否存在共享数据
        """
        threading.Thread.__init__(self)

        self.job = job
        self.interval = interval
        self.job_args = job_args if job_args else tuple()
        self.job_kwargs = job_kwargs if job_kwargs else dict()
        self.job_lable = job_lable
        self.play = True

        # 子进程之间共享队列
        if share:
            self.share_queue = Queue()
            self.job_kwargs['share_queue'] = self.share_queue

    def run(self):
        logging.info('start timer: %s' % self.job_lable)
        while self.play:
            start_time = datetime.now()

            # 启动进程,超时不结束Kill掉
            p = Process(target=self.job, args=self.job_args, kwargs=self.job_kwargs)
            p.start()
            p.join(timeout=self.interval)
            if p.is_alive():
                logging.info('timeout kill process: %s' % self.job_lable)
                kill_child_processes(p.pid, kill_parent=True)
                p.join(timeout=1)

            # 补足等待时间
            finish_time = datetime.now()

            offset = (finish_time - start_time).seconds
            if offset < self.interval:
                time.sleep(self.interval - offset)

    def stop(self):
        self.play = False


def kill_child_processes(parent_pid, sig=signal.SIGKILL, kill_parent=False):
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)
    for process in children:
        process.send_signal(sig)
    if kill_parent:
        parent.send_signal(signal.SIGKILL)


def func(*args, **kwargs):
    import random
    sec = args[0]

    share_queue = kwargs["share_queue"]
    if share_queue.empty():
        share_queue.put(datetime.now())
        return
    pro_date = kwargs["share_queue"].get(block=False)
    kwargs["share_queue"].put(datetime.now(), block=False)

    print '====> start read:' + str(pro_date)
    sleep_sec = random.randint(0, sec)
    print 'sleep %s s' % sleep_sec
    time.sleep(sleep_sec)
    print '++++> end read:' + str(pro_date)


def func1():
    print "test"


if __name__ == '__main__':
    t = Timer(job=func, interval=3, job_args=(6,), job_lable="test", share=True)
    # t = Timer(job=func1, interval=3)
    t.start()
    time.sleep(3600)
