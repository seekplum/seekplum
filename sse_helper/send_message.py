#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import random

from datetime import datetime

import redis

host = "127.0.0.1"
port = 6379


class SseSender(object):
    def __init__(self, redis_, channel="sse"):
        """
        redis 的发布
        channel: 要发布的频道
        """
        self.redis = redis_
        self.channel = channel
        self.send_num = 0

    def send(self, event, data, id_=""):
        """
        event: sse数据格式中的event
        data: 要发送的数据
        """
        data_ = {
            "event": event,
            "message": data,
            "id": id_
        }
        send_num = self.redis.publish(self.channel, json.dumps(data_))
        self.send_num = send_num


def get_pool(db=0):
    pool = redis.ConnectionPool(host=host, port=port, db=db)
    return pool


def redis_connect(db=0, pool=None):
    if not pool:
        pool = get_pool(db)
    return redis.Redis(connection_pool=pool)


def main():
    channel = "seekplum"
    event = "detail_info"
    # event = "abc"
    r_client = redis_connect()
    sender = SseSender(r_client, channel)
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    count = random.randint(1, 100)
    message = "%s: %s" % (time_str, count)
    id_ = "" if count < 90 else "CLOSE"
    sender.send(event, message, id_)
    number = sender.send_num
    print "number: ", number


if __name__ == '__main__':
    main()
