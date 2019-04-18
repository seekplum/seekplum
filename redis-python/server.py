#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
res 服务端,启动服务端后等待客户端消息
"""
import redis

rc = redis.Redis(host='127.0.0.1')
ps = rc.pubsub()
ps.subscribe(['abc', 'def'])  # 订阅两个频道，abc, def
for item in ps.listen():
    if item['type'] == 'message':
        print "频道:%s\n消息内容:%s\npattern:%s" % (item['channel'], item['data'], item['pattern'])
