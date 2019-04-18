# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: client
#         Desc: tcp连接客户端,连接后发送消息
#               1. 使用多线程，分别用于接收/发送消息
#               2. 使用信号，Ctrl + C 时正常退出
#               3. 强制结束 ps aux|grep -E "server.py|client.py" | grep -v grep | awk '{print $2}' | xargs kill -9
#       Author: hjd
#        Email:
#     HomePage:
#      Version:
#   LastChange: 2017-05-14 11:28
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

import socket
import signal
import sys

from threading import Thread

# 服务端的ip，两台服务器时则写对端服务器ip,同台服务器则写 127.0.0.1
HOST = "127.0.0.1"
PORT = 9527
EXIT = "exit"
RUNNING = True


def print_info(text):
    """打印信息

    :param text: 需要打印的消息
    """
    print "\n[Client] %s" % text


def check_data(data):
    """检查接收的消息

    :param data: str 接收的消息

    :rtype bool
    :return
        True: 消息正常
        False: 消息有问题正常
    """
    result = False
    if data and data != EXIT:
        result = True
    return result


def get_data(sock):
    """接收消息

    :param sock: socket连接对象
    """
    while RUNNING:
        # 接收消息
        data = sock.recv(1024)
        if check_data(data):
            print_info("get data: %s" % data)
        else:
            print_info("The other party opted out.")
            stop()
    print_info("get data stop")


def sent_data(sock):
    """发送消息

    :param sock: socket连接对象
    """
    while RUNNING:
        # 输入数据
        message = raw_input("Please input msg: ")
        # 发送数据
        sock.send(message)
        if message == EXIT:
            print_info("You chose to quit.")
            stop()
    print_info("sent data stop")


def stop():
    """停止程序运行
    """
    global RUNNING
    RUNNING = False


def stop_handler(signum, frame):
    """接收信号
    """
    stop()
    print_info("\nstop")


def main():
    # 创建服务器与服务器之间的Tcp socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到address处的套接字
        sock.connect((HOST, PORT))
    except socket.error:
        print_info("server is not running")
        sys.exit(1)

    # 定义Ctrl + C 信号
    old_handler = signal.signal(signal.SIGINT, stop_handler)

    # 使用两个线程分别发送/接收消息
    sent_thread = Thread(target=sent_data, args=(sock,))
    get_thread = Thread(target=get_data, args=(sock,))

    sent_thread.setDaemon(True)
    get_thread.setDaemon(True)

    sent_thread.start()
    get_thread.start()

    # 等待结束信号
    while RUNNING:
        pass

    # 取消信号处理
    signal.signal(signal.SIGINT, old_handler)

    # 关闭连接
    print_info("close socket")
    sock.close()


if __name__ == '__main__':
    main()
