# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: process_helper
#         Desc: 
#       Author: hjd
#        Email:
#     HomePage:
#      Version:
#   LastChange: 2018-03-24 21:50
#      History:
#=============================================================================

┏┓ ┏┓
┏┛┻━━━┛┻┓
┃ ☃ ┃
┃ ┳┛ ┗┳ ┃
┃ ┻ ┃
┗━┓ ┏━┛
┃ ┗━━━┓
┃ 神兽保佑 ┣┓
┃　永无BUG ┏┛
┗┓┓┏━┳┓┏┛
┃┫┫ ┃┫┫
┗┻┛ ┗┻┛
"""

from multiprocessing import Pool
from multiprocessing import current_process


def test(x):
    message = "name: {} {}".format(current_process().name, str(x) * 10)
    # print message
    return message


if __name__ == '__main__':
    # 创建 4 个进程
    pool = Pool(processes=4)
    results = []
    for i in range(10):
        # pool.apply_async(test, args=(i,))
        # 接收test函数的返回值
        results.append(pool.apply_async(test, args=(i,)))

    print "close pool"
    # 关闭进程池，表示不能在往进程池中添加进程
    pool.close()
    # 等待进程池中的所有进程执行完毕，必须在close()之后调用
    pool.join()
    for res in results:
        print res.get()
