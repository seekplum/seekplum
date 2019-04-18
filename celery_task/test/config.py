# !/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import timedelta

CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/1'
BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_BEAT_SCHEDULE = {
    'add-every-5-seconds': {
        'task': 'tasks.add',
        'schedule': timedelta(seconds=5),
        'args': (2, 4)
    },
}
# 执行 celery -A tasks worker -B --loglevel=info
