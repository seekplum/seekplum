# !/usr/bin/env python
# -*- coding:utf-8-*-

from __future__ import absolute_import
from celery import Celery

app = Celery('celery_task', include=['celery_task.tasks'])

app.config_from_object('celery_task.config')

if __name__ == '__main__':
    print "hjd celery start..."
    app.start()


