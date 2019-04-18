#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: decorrator
#         Desc: 装饰器工具
#       Author: hjd
#        Email:
#     HomePage:
#      Version: 
#   LastChange: 2018-03-21 13:06
#      History:
#=============================================================================
"""
import time


def running_time(func):
    """运行时间装饰器

    :param func: func 函数

    :return 返回 `func` 执行结果
    """

    def _wrap(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print("[%s] use time: [%s]" % (func.__name__, (end_time - start_time)))
        return result

    return _wrap
