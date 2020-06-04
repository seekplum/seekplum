# -*- coding: utf-8 -

import socket


def sock_send(msg):
    if isinstance(msg, str):
        msg = msg.encode("ascii")

    # http://docs.datadoghq.com/guides/dogstatsd/#datagram-format
    if dogstatsd_tags:
        msg = msg + b"|#" + dogstatsd_tags.encode('ascii')

    if sock:
        sock.send(msg)


def increment(name, value, sampling_rate=1.0):
    sock_send("{0}{1}:{2}|c|@{3}".format(prefix, name, value, sampling_rate))


if __name__ == '__main__':
    prefix = "hjd_test"
    host, port = "127.0.0.1", 9125
    dogstatsd_tags = ""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((host, int(port)))
    increment("gunicorn.requests", 1)
