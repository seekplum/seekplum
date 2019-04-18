# !/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import
from celery_task.celery import app
import time
import os


@app.task
def add(x, y):
    result = x + y
    current_path = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(current_path, 'celery.log')
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    output = "hjd now time： %s, %s + %s = %s\n" % (now_time, x, y, result)
    with open(log_file, 'a') as f:
        f.write(output)
    f.close()
    print output
