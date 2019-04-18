# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: client
#         Desc: tcp连接服务端,等待连接接收消息
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

# 本地ip,等待客户端连接
HOST = "0.0.0.0"
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


def get_data(conn):
    """接收消息

    :param conn: socket连接对象
    """
    while RUNNING:
        # 接受TCP链接并返回
        data = conn.recv(1024)
        if check_data(data):
            print_info("get data: %s" % data)
        else:
            print_info("The other party opted out.")
            stop()
    # 关闭连接
    conn.close()
    print_info("get data stop")


def sent_data(conn):
    """发送消息

    :param conn: socket连接对象
    """
    while RUNNING:
        # 输入数据
        message = raw_input("Please input msg: ")

        # 发送TCP数据，将字符串中的数据发送到链接的套接字
        conn.send(message)

        if message == EXIT:
            print_info("You chose to quit.")
            stop()
    # 关闭连接
    conn.close()
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
        # 将套接字绑定到地址
        sock.bind((HOST, PORT))
    except socket.error as err:
        error_msg = str(err)
        if "Address already in use" in error_msg:
            print_info("Port %s is occupied" % PORT)
        else:
            print_info("Error: %s" % error_msg)
        sys.exit(1)

    # 开始监听TCP传入连接, 最大连接数为 5
    sock.listen(5)

    print_info("Server start at  '%s:%s'" % (HOST, PORT))
    print_info("Wait for connection...")

    # 接受TCP链接并返回
    conn, address = sock.accept()
    print_info("Connected by: %s" % str(address))

    # 定义Ctrl + C 信号
    old_handler = signal.signal(signal.SIGINT, stop_handler)

    # 使用两个线程分别发送/接收消息
    sent_thread = Thread(target=sent_data, args=(conn,))
    get_thread = Thread(target=get_data, args=(conn,))

    sent_thread.setDaemon(True)
    get_thread.setDaemon(True)

    sent_thread.start()
    get_thread.start()

    # 等待结束信号
    while RUNNING:
        pass

    # 取消信号处理
    signal.signal(signal.SIGINT, old_handler)

    # 关闭套接字
    print_info("close socket")
    sock.close()


if __name__ == '__main__':
    main()
