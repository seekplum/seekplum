# !/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import absolute_import
from datetime import timedelta
import random

CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
BROKER_URL = 'redis://127.0.0.1:6379/1'

# 运行方式
# celery -A celery_task worker -l info
# celery -A celery_task worker --loglevel=info

x = random.random() * 10
y = random.randint(1, 100)

infoCELERY_TIMEZONE = 'Asia/Shanghai'

CELERYBEAT_SCHEDULE = {
    'add-every-5-seconds': {
        'task': 'celery_task.tasks.add',
        'schedule': timedelta(seconds=5),
        'args': (x, y)
    },
}

# 运行方式
# celery -A celery_task worker -B -l info 或者 celery -A celery_task worker --loglevel=info + celery -A celery_task beat
# 指定log文件，默认会在本地生成一个celerybeat-schedule文件
# celery -A celery_task worker -B -s /tmp/abc.log --loglevel=info
