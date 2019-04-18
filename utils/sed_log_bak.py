#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import os
import subprocess
import time
import datetime


def run(cmd):
    print "cmd:", cmd
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


def sed_log_file(time_str, log_path):
    """
    查找指点时间段内的所有日志
    :param log_path:
    :return: 
    """
    # 开始时间
    start_output = run("grep -iE '{}' {}".format(time_str, log_path)).splitlines()
    # 结束时间
    end_output = run("grep -iE '{}' {}".format(time_str, log_path)).splitlines()
    start_time = start_output[0]
    end_time = end_output[-1]
    if not start_time or not end_time:
        return []
    else:
        start_time = start_time[:9]
        end_time = end_time[:9]
    # 注意，如果起始时间在日志中不存在，则整个截取将返回 0 行结果。
    # 而如果结束时间在日志中不存在，则会截取到日志的最后一条。
    if start_time == end_time:
        sed_cmd = "sed -n '/{start_time}/p' {log_path}".format(start_time=start_time, log_path=log_path)
    else:
        sed_cmd = "sed -n '/{start_time}/ , /{end_time}/p' {log_path}".format(start_time=start_time, end_time=end_time,
                                                                              log_path=log_path)
    print "sed_cmd:", sed_cmd
    out_put = run(sed_cmd)
    return out_put.splitlines()


if __name__ == '__main__':
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "messages")
    start_time = time.mktime(datetime.datetime(2017, 2, 27, 10).timetuple()) * 1000
    end_time = time.mktime(datetime.datetime(2017, 2, 27, 12).timetuple()) * 1000
    start_time = datetime.datetime.fromtimestamp(float(start_time) / 1000)
    end_time = datetime.datetime.fromtimestamp(float(end_time) / 1000)
    data = end_time - start_time
    number = int(round(data.seconds / 60 / 60))
    all_data = []
    for i in range(number):
        new_data = start_time + datetime.timedelta(hours=i)
        new_data = new_data.strftime("%b %d %H")
        all_data.append(new_data)
    time_str = "|".join(all_data)
    print sed_log_file(time_str=time_str, log_path=log_path)
