#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: server
#         Desc: 等待接收同网段机器的发送过来的广播
#       Author: hjd
#        Email:
#     HomePage:
#      Version:
#   LastChange: 2018-03-20 14:40
#      History:
#=============================================================================
"""

import socket

HOST = ""
PORT = 51423
REPLY_MESSAGE = "I am here"


def print_info(text):
    """打印信息

    :param text: 需要打印的消息
    """
    print text


def receive_broadcast():
    """接收广播
    """
    # 创建UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 设置给定套接字选项的值
    # 打开地址复用功能
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # 允许发送广播数据
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # 将套接字绑定到地址
    sock.bind((HOST, PORT))

    print_info("start listen to '%s:%s'" % (HOST, PORT))
    while True:
        try:
            # 接收客户端的数据
            message, address = sock.recvfrom(1024)
            print_info("get message: %s, address: %s" % (message, address))

            # 发送数据给客户端
            sock.sendto(REPLY_MESSAGE, address)
            print_info("send message: %s to %s" % (REPLY_MESSAGE, address))
        except (KeyboardInterrupt, SystemExit):
            print_info("exit")
            break
        except Exception as err:
            print_info(str(err))


if __name__ == '__main__':
    receive_broadcast()
