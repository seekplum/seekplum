# -*- coding: utf-8 -*-
"""
https://www.cnblogs.com/pangguoping/p/5720134.html
"""
from __future__ import print_function

import pika

username, password = "guest", "guest"
host = "127.0.0.1"
port = 5672
# 创建生产者
credentials = pika.PlainCredentials(username, password)

# 连接 rabbit 服务器
connection = pika.BlockingConnection(pika.ConnectionParameters(host, port, "/", credentials))

# 创建频道
channel = connection.channel()

# 声明消息队列，消息将在这个队列中进行传递
# 如果消息发送到不存在的队列，rabbitmq将会自动清除这些消息
# 如果队列不存在，则创建
channel.queue_declare(queue="hello", durable=True)  # durable=True 声明队列持久化

# exchange 能够确切的指定消息应该到哪个队列中
# 向队列插入数值, routing_key 是队列名， body 是要插入的内容

channel.basic_publish(exchange="", routing_key="hello", body="Hello World!")
print("start...")
connection.close()
