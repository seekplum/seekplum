#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: websocket
#         Desc: 手动实现的websocket
#       Author: hjd
#     HomePage: seekplum.github.io
#   LastChange: 2018-04-12 14:00
#=============================================================================
"""

import socket
import base64
import hashlib
import struct

# 对请求头中的sec-websocket-key进行加密
HEADERS = "HTTP/1.1 101 Switching Protocols\r\n" \
          "Upgrade:websocket\r\n" \
          "Connection: Upgrade\r\n" \
          "Sec-WebSocket-Accept: {0}\r\n" \
          "WebSocket-Location: ws://{1}{2}\r\n\r\n"

MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'  # 固定的，魔法字符串就是这个字符串
HOST = "127.0.0.1"
PORT = 8002
RUNNING = True


def get_headers(data):
    """将请求头格式化成字典

    :param data: 请求头数据字符串
    :type data str

    :rtype dict
    :return: 请求头数据
    """
    header_dict = {}
    header, body = data.split('\r\n\r\n', 1)
    header_list = header.split('\r\n')
    length = len(header_list)
    for i in range(length):
        if i == 0:
            if len(header_list[i].split(' ')) == 3:
                header_dict['method'], header_dict['url'], header_dict['protocol'] = header_list[i].split(' ')
        else:
            k, v = header_list[i].split(':', 1)
            header_dict[k] = v.strip()
    return header_dict


def parse_data(data):
    """解析数据

    :param data 接收到参数
    :type data str

    下面是对浏览器发来的消息解密的过程
    浏览器包格式
    固定子节 + 包长度字节(变长) + mark掩码 + 兄弟数据
    固定字节：
    10000001或是10000002）这里没用，忽略
    包长度字节：
    第一位肯定是1，忽略。剩下7个位可以得到一个整数(0 ~ 127)，其中
    （1 - 125）表此字节为长度字节，大小即为长度；
    （126）表接下来的两个字节才是长度；
    （127）表接下来的八个字节才是长度；
    用这种变长的方式表示数据长度，节省数据位。
    mark掩码：
    mark掩码为包长之后的4个字节，之后的兄弟数据要与mark掩码做运算才能得到真实的数据。
    兄弟数据：
    得到真实数据的方法：将兄弟数据的每一位x，和掩码的第i % 4位做xor运算，其中i是x在兄弟数据中的索引。
    """
    payload_len = ord(data[1]) & 127
    if payload_len == 126:
        mask = data[4:8]
        decoded = data[8:]  # 数据
    elif payload_len == 127:
        mask = data[10:14]
        decoded = data[14:]
    else:
        mask = data[2:6]
        decoded = data[6:]

    bytes_list = bytearray()
    # 上面解密的最终结果，就是拿到这个decode,就是浏览器发来的真实的数据(加密的)
    for i, info in enumerate(decoded):
        # 按位异或 对于中文来说会占两个字符
        c = chr(ord(info) ^ ord(mask[i % 4]))
        bytes_list.append(c)

    message = str(bytes_list)
    return message


def send_data(conn, data):
    """发送数据

    :param conn
    :type conn

    :param data 要发送的数据
    :type data str

    固定子节 + 包长度字节(变长) + 原始数据
    固定字节：固定的1000 0001(‘\x81′)
    包长：根据发送数据长度是否超过125，0xFFFF(65535)来生成1个或3个或9个字节，来代表数据长度。
    """
    token = "\x81"
    length = len(data)
    if length < 126:
        token += struct.pack("B", length)
    elif length <= 0xFFFF:
        token += struct.pack("!BH", 126, length)
    else:
        token += struct.pack("!BQ", 127, length)

    conn.send("{}{}".format(token, data))


def start_server():
    """启动web server服务
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    conn, address = sock.accept()
    data = conn.recv(1024)

    headers = get_headers(data)  # 提取请求头信息

    sec_key = headers['Sec-WebSocket-Key']
    res_key = base64.b64encode(hashlib.sha1(sec_key + MAGIC_STRING).digest())  # 把返回消息加密

    response = HEADERS.format(res_key, HOST, PORT)

    # 响应【握手】信息
    conn.send(response)

    while RUNNING:
        data = conn.recv(1024)
        message = parse_data(data)
        if message in ["exit", "quit"]:
            print "断开连接"
            break
        print message
        send_data(conn, message)


def main():
    print "开始监听: {}:{}".format(HOST, PORT)
    start_server()


if __name__ == '__main__':
    main()
