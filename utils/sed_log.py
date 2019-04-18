#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import subprocess

import datetime


def run(cmd):
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    std_out, std_err = p.communicate()
    if std_err:
        raise Exception("cmd: %s, std err: %s" % (cmd, std_err))
    else:
        return std_out


def real_time(data, option=True):
    """
    对时间进行加减
    :param data: 原时间
    :param option: 操作，加或者减
    :return: 处理之后的数据格式
    """
    # 把字符串转成datetime类型
    old_data = datetime.datetime.strptime(data, "%Y-%m-%d %H:%M")
    if option:
        minute = 1
    else:
        minute = -1
    new_data = old_data + datetime.timedelta(minutes=minute)
    new_data = new_data.strftime("%Y-%m-%d %H:%M")
    return new_data


def sed_log_file(start, end, log_path):
    """
    查找指点时间段内的所有日志
    :param start: 
    :param end: 
    :param log_path: 
    :return: 
    """
    start_ok = False
    end_ok = False
    while start < end:
        start_time = run("grep -i '{}' {}".format(start, log_path))
        if not start_ok:
            # 起始时间
            if start_time:
                start_ok = True
            else:
                start = real_time(start)
        if not end_ok:
            # 结束时间
            end_time = run("grep -i '{}' {}".format(end, log_path))
            if end_time:
                end_ok = True
            else:
                end = real_time(end, option=False)
        if end_ok and start_ok:
            break
    else:
        # 在要查找的时间段内没有日志
        if end > start:
            return []
    # 注意，如果起始时间在日志中不存在，则整个截取将返回 0 行结果。
    # 而如果结束时间在日志中不存在，则会截取到日志的最后一条。
    if start != end:
        sed_cmd = "sed -n '/{start_time}/ , /{end_time}/p' {log_path}".format(start_time=start, end_time=end,
                                                                              log_path=log_path)
    else:
        sed_cmd = "sed -n '/{start_time}/p' {log_path}".format(start_time=start, log_path=log_path)
    print "sed_cmd:", sed_cmd
    out_put = run(sed_cmd)
    return out_put.splitlines()


if __name__ == '__main__':
    start_time = "2017-02-26 15:10"
    end_time = "2017-02-26 15:13"
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log/log1.log")
    output = sed_log_file(start_time, end_time, path)
    print "结果：\n{}".format(output)
