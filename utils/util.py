#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import uuid
import netifaces
import os
import sys
import time
import fcntl
import struct

import yaml

from threading import Thread
from functools import wraps, partial
import commands
import socket

from utils.exceptions import NetworkCardError


def get_local_ip():
    # 这个得到本地ip
    local_ip = socket.gethostbyname(socket.gethostname())
    # 获取本机电脑名
    my_name = socket.getfqdn(socket.gethostname())
    # 获取本机ip
    my_address = socket.gethostbyname(my_name)
    return local_ip, my_address


def get_eth_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        eth_ip, port = s.getsockname()
    except socket.error:
        try:
            eth_ip_list = commands.getoutput("hostname -I")
            for eth_ip in eth_ip_list.split():
                if eth_ip.startswith("10.") or eth_ip.startswith("192."):
                    eth_ip = eth_ip
                    break
            else:
                eth_ip = eth_ip_list.split()[0]
        except:
            eth_ip = '127.0.0.1'
    finally:
        s.close()
    return eth_ip


def asyn(f):
    """
    :param f: 处理函数
    :return: 封装了处理函数的线程
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        Thread(target=f, args=args, kwargs=kwargs).start()

    return wrapper


def retry_onFalse(times=-1, interval=10):
    """
    失败重试机制，作为装饰器使用
    默认重试次数是无限次，默认重试间隔为10秒
    重试的条件是方法返回值为False
    """
    return _retry_onFalse({'times': times, 'interval': interval})


def _retry_onFalse(params):
    """

    :param params:
    :return:
    """

    def _retry(func):
        @wraps(func)
        def __retry(*args, **kwargs):
            time_count_start = params['times']
            while params['times'] != 0:
                res = func(*args, **kwargs)
                if not res:
                    params['times'] -= 1
                    time.sleep(params['interval'])
                    print('Retry(times: {0}) function: {1}, args: {2}, kwargs: {3}'.format(
                        time_count_start - params['times'], func.func_name, args, kwargs
                    ))
                else:
                    return res
            return False

        return __retry

    return _retry


def singleton(cls):
    """
    单例模式装饰器
    :param cls:
    :return:
    """

    _instances = {}  # 容器字典，存储每个类对应生成的实例

    @wraps(cls)
    def wrapper(*args, **kwargs):
        # 检查类是否_instances的key；如果是，直接返回生成过的实例
        key = '<{}_{}_{}>'.format(cls.__name__, args, kwargs)
        if key not in _instances:
            _instances[key] = cls(*args, **kwargs)
        return _instances[key]

    return wrapper


def get_func(module_name, func_name, need_reload=True):
    if module_name in sys.modules and need_reload:
        reload(sys.modules[module_name])
    else:
        __import__(module_name)
    m = sys.modules[module_name]
    return getattr(m, func_name)


def get_settings():
    current_path = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(current_path, "settings.yaml")

    with open(yaml_file) as f:
        yaml_string = f.read()
        settings = yaml.load(yaml_string)
    return settings


def get_project_path():
    """get the project path"""
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return project_path


def get_mac_address():
    """通过UUID查询mac地址
    """
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])


def get_network_card_name():
    """查询主机中的网卡名

    查询到系统中所有的网卡名,过滤掉 ib/bond/lo 三种网口,对所有网卡名进行排序,取顺序的第一个

    :rtype str
    :return 网卡名

    :raise NetworkCardError 查询网卡名失败
    """

    def filter_name(name):
        """检查name是否符合要求

        :param name: str 网卡名

        :rtype bool
        :return
            True: 符合要求的网卡名
            False: 不符合要求的网卡名
        """
        result_ = True
        if name.startswith("ib") or name.startswith("bond") or name == "lo":
            result_ = False
        return result_

    # 所有的网卡名
    interfaces = netifaces.interfaces()

    # 过滤掉 ib/lo/bond 网卡名
    interfaces = filter(filter_name, interfaces)

    # 没有符合条件的网卡名
    if len(interfaces) < 1:
        raise NetworkCardError("The network card list is empty.")

    # 对网卡名进行排序
    interfaces.sort()
    return interfaces[0]


class RunRealCmdError(Exception):
    """执行命令异常
    """
    pass


def run_real_cmd(cmd):
    """执行系统命令并实时返回

    :param cmd 系统命令
    :type cmd str
    :example cmd "ping www.baidu.com"

    >>> for line in run_real_cmd("ping www.baidu.com"):
    ...     print line

    """
    p = subprocess.Popen(cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        yield line

    if p.returncode != 0:
        raise RunRealCmdError("run `%s` fail" % cmd)


def time_use(func=None, name=None):
    if func is None:
        return partial(time_use, name=name)

    if name is None:
        name = func.__name__

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        use_time = time.time() - start_time
        print "%s, use time: %ss" % (name, use_time)
        return result

    return wrapper


def get_ip_address(ifname):
    """查询指定网卡ip

    注意: 只在linux平台有效，在OSX上报错

    :param ifname 网口名
    :type ifname basestring
    :example ifname lo

    :rtype ip str
    :return ip 网卡的ip
    :example ip 127.0.0.1
    """
    # 创建使用IPv4网络和UDP协议的socket对象
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    packed_ip = fcntl.ioctl(
        s.fileno(),
        0x8915,
        struct.pack('256s', ifname[:15]))[20:24]

    # 把4字节的IP地址转成十进制的可读形式
    ip = socket.inet_ntoa(packed_ip)
    return ip
