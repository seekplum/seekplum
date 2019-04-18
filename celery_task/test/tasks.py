# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""
在当前目录下执行 celery -A tasks worker -B --loglevel=info
"""
import time


from celery import Celery

# app = Celery('tasks', backend='redis://localhost:6379/1', broker='redis://localhost:6379/0')


app = Celery('tasks')
app.config_from_object('config')


@app.task
def add(x, y):
    result = x + y
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print "\n hjd now time： %s, %s + %s = %s\n" % (now_time, x, y, result)
    return result
    # 执行方式，在tasks.py同目录下执行下面语句
    # 1.celery -A tasks worker --loglevel=info
    # 2.在tasks.py同目录下打开python命令行
    # from tasks import add
    # res = add.delay(4, 3)
