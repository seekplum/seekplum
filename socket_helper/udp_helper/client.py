#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: client
#         Desc: 向同网段机器发送广播,获取所有同网段存活的主机ip地址
#       Author: hjd
#        Email:
#     HomePage:
#      Version:
#   LastChange: 2018-03-20 14:40
#      History:
#=============================================================================
"""
import commands
import socket

from multiprocessing import Process
from multiprocessing import Queue

PORT = 51423
MESSAGE = 'hello'
TIMEOUT = 1


def print_info(text):
    """打印信息

    :param text: 需要打印的消息
    """
    print text


def get_local_ips():
    """查询本地的所有ip
    """
    cmd = 'ip a | grep inet | grep -v "inet6" | grep -v "127.0.0.1"'
    output = commands.getoutput(cmd).split('\n')

    ips = []
    for line in output:
        ip = line.strip().split(' ')[1].split('/')[0]
        ips.append(ip)
    return set(ips)


def get_broadcast_ips(ips):
    """获取本地ip的子网掩码

    :param ips: iter 本地所有ip
    """
    broadcast_ips = []
    for ip in ips:
        ip = ip.split('.')
        ip[3] = '255'
        broadcast_ip = '.'.join(ip)
        broadcast_ips.append(broadcast_ip)
    return set(broadcast_ips)


def broadcast_message(que, broadcast_ip):
    """给同网段的所有ip发送广播

    :param que: Queue 消息队列
    :param broadcast_ip: str 广播地址
    """
    print_info("broadcast ip: %s" % broadcast_ip)

    # 创建UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 设置给定套接字选项的值
    # 打开地址复用功能
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 允许发送广播数据
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # 发送UDP数据
    sock.sendto(MESSAGE, (broadcast_ip, PORT))
    print_info("send message: %s, address: %s:%s" % (MESSAGE, broadcast_ip, PORT))

    received_ips = []
    while True:
        # 接收数据
        (message, address) = sock.recvfrom(1024)
        print_info("get message: %s, address: %s" % (message, address))
        received_ips.append(address)
        if not message:
            break
        que.put(address[0])


def get_ips(que):
    """从队列中读取ip

    :param que: Queue 消息队列
    """
    ips = []
    while True:
        if not que.empty():
            ip = que.get(True)
            ips.append(ip)
        else:
            break
    return set(ips)


def get_all_ips():
    """查询所有的ip
    """
    # 查询本地所有ip
    local_ips = get_local_ips()
    print_info("local ips: %s" % local_ips)

    # 查询广播地址
    broadcast_ips = get_broadcast_ips(ips=local_ips)
    print_info("local broadcast ips: %s" % broadcast_ips)

    # 通过队列在多进程中同步数据
    que = Queue()
    processes = []

    # 多线程发送多个广播
    for broadcast_ip in broadcast_ips:
        process = Process(target=broadcast_message,
                          args=(que, broadcast_ip,))
        processes.append(process)

    for process in processes:
        process.start()
        # 通过超时控制进程结束
        process.join(timeout=TIMEOUT)

    ips = get_ips(que)

    # 检查进程是否结束
    for process in processes:
        if process.is_alive():
            process.terminate()

    return set(ips)


if __name__ == '__main__':
    alive_ips = get_all_ips()
    print_info("alive host: %s" % alive_ips)
