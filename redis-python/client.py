#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
redis 客户端,发送消息给服务端
"""
import redis
import sys

rc = redis.Redis(host='127.0.0.1')

if len(sys.argv) != 3:
    subscribe = raw_input("请输入频道> ")
    message = raw_input("请输入要发送的消息> ")
else:
    subscribe = sys.argv[1]
    message = sys.argv[2]
rc.publish(subscribe, message)
