# -*- coding: utf-8 -*-

from __future__ import print_function
import pika

username, password = "guest", "guest"
host = "127.0.0.1"
port = 5672

credentials = pika.PlainCredentials(username, password)

connection = pika.BlockingConnection(pika.ConnectionParameters(host, port, "/", credentials))
channel = connection.channel()

channel.queue_declare(queue="wzg")


# 定义一个回调函数来处理，这边的回调函数就是将信息打印出来
def callback(ch, method, properties, body):
    print(" [x] Received  %r" % body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


#  告诉rabbitmq使用callback来接收信息
# auto_ack=True 表示在回调函数中不需要发送确认标识
channel.basic_consume(on_message_callback=callback, queue="hello", auto_ack=False)
print(" [*] Waiting for messages. To exit press CTRL+C")

# 开始接收信息，并进入阻塞状态，队列里有信息才会调用callback进行处理。按ctrl+c退出。
channel.start_consuming()
