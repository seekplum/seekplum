#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: redis_utils
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-03-29 18:10
#=============================================================================
"""

import logging
from functools import wraps

import redis
from retools.lock import Lock

logger = logging.getLogger(__name__)


def generate_lock_key(key):
    return "redis_lock:{}".format(key)


def get_pool(host, port, db=0):
    pool = redis.ConnectionPool(host=host, port=port, db=db)
    return pool


def redis_connect(host, port, db=0, pool=None):
    if not pool:
        pool = get_pool(host, port, db=db)
    return redis.Redis(connection_pool=pool)


def lock_factory(key, host=None, port=None, redis_=None, expires=60 * 5, timeout=5):
    # 全局性锁，用于性能采集，持有锁的有效时间为60*5秒，申请锁的超时时间为5s
    if not redis_:
        redis_ = redis_connect(host, port)
    return Lock(key, expires=expires, timeout=timeout, redis=redis_)


class redis_lock(object):
    def __init__(self, key, redis_client, ttl=60):
        self.ttl = ttl  # 超时时间默认60秒
        self.lock_key = generate_lock_key(key)
        self.delete_key = False
        self.redis_client = redis_client

    def acquire(self):
        if self.redis_client.exists(self.lock_key):
            return False
        else:
            self.redis_client.set(name=self.lock_key, value="FUCK FRANK", ex=self.ttl)
            self.delete_key = True
            return True

    def release(self):
        if self.delete_key is True:
            self.redis_client.delete(self.lock_key)

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def with_lock(redis_host, redis_port, expires=60, timeout=5):
    def _wraps(func):
        @wraps(func)
        def __wraps(*args, **kw):
            lock_key = generate_lock_key(func.__name__)
            lock = lock_factory(key=lock_key, expires=expires, timeout=timeout, host=redis_host, port=redis_port)
            try:
                lock.acquire()
            except Exception as e:
                logger.exception(e)
                logger.warning("another task is running, quite ...")
            else:
                try:
                    return func(*args, **kw)
                except Exception as e:
                    raise e
                finally:
                    lock.release()

        return __wraps

    return _wraps
