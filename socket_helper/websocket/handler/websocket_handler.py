# !/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import os
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.options
from tornado.web import Finish
from uuid import uuid4
from tornado.options import define, options

define("port", default=8001, help="run on the given port", type=int)
global uuid_str


class Book(object):
    total_count = 10  # 书籍总量
    all_web_socket = []  # 所有页面
    uuid_count = {}  # 每个页面购买的数量

    def register(self, callback):
        """
        为每个页面注册 websocket
        :param callback:
        :return:
        """
        self.all_web_socket.append(callback)

    def del_register(self, callback):
        """
        删除页面的 websocket
        :param callback:
        :return:
        """
        self.all_web_socket.remove(callback)

    def add_book(self, uuid):
        """
        增加购买数量
        :param uuid:
        :return:
        """
        if uuid in self.uuid_count.keys():
            self.uuid_count[uuid] += 1
        else:
            self.uuid_count[uuid] = 1
        self.get_all_count(uuid)

    def remove_book(self, uuid):
        """
        减少购买数量
        :param uuid:
        :return:
        """
        if uuid in self.uuid_count.keys():
            self.uuid_count[uuid] -= 1
        else:
            self.uuid_count[uuid] = 0
        self.get_all_count(uuid)

    def get_all_count(self, uuid):
        """
        对每个页面计算书籍总量
        :param uuid:
        :return:
        """
        for callback in self.all_web_socket:
            count, curr_count = self.get_book_count(uuid)
            callback(count, curr_count)

    def get_book_count(self, uuid):
        """
        剩余书籍总量
        :param uuid:
        :return:
        """
        count = self.total_count - sum(self.uuid_count.values())
        curr_count = self.uuid_count.get(uuid, 0)
        return count, curr_count


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        """
        书籍首页
        :return:
        """
        # 每个页面唯一标识
        uuid = uuid4()
        count, curr_count = self.application.book.get_book_count(uuid)
        websocket_url = 'ws://127.0.0.1:8001/cart/status'
        self.render("index.html", uuid=uuid, count=count, curr_count=curr_count, host=websocket_url)


class CountHandler(tornado.web.RequestHandler):
    def post(self):
        """
        购买书籍、退货
        :return:
        """
        action = self.get_argument('action')
        uuid = self.get_argument('uuid')
        global uuid_str
        uuid_str = uuid
        if not uuid:
            self.set_status(400)
            return
        count, curr_count = self.application.book.get_book_count(uuid)
        if action == 'add':
            if count > 0:
                self.application.book.add_book(uuid)
            else:
                self.write({"code": 1, "uuid": uuid, "message": u"库存不足"})
                raise Finish
        elif action == 'remove':
            if curr_count > 0:
                self.application.book.remove_book(uuid)
            else:
                self.write({"code": 1, "uuid": uuid, "message": u"你没有购买"})
                raise Finish
        else:
            self.set_status(400)
        self.write(json.dumps({"code": 0, "uuid": uuid}))


class WebsocketHandler(tornado.websocket.WebSocketHandler):
    """
    Websocket
    """

    def open(self):
        """
        打开 一个 websocket
        :return:
        """
        self.application.book.register(self.callback)

    def on_close(self):
        """
        关闭 websocket
        :return:
        """
        self.application.book.del_register(self.callback)

    def on_message(self, message):
        """
        接收前端消息
        :param message:
        :return:
        """
        data = json.loads(message)

    def callback(self, count, curr_count):
        """
        回调函数
        :param count: 书籍总量
        :param curr_count: 购买数量
        :return:
        """
        global uuid_str
        self.write_message('{"count":"%d", "curr_count":"%d", "uuid":"%s"}' % (count, curr_count, uuid_str))


class Application(tornado.web.Application):
    def __init__(self):
        self.book = Book()

        handlers = [
            (r'/', IndexHandler),
            (r'/cart', CountHandler),
            (r'/cart/status', WebsocketHandler)
        ]

        settings = {
            'template_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
            'static_path': os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = Application()
    server = tornado.httpserver.HTTPServer(app)
    server.listen(options.port)
    print "server start http://127.0.0.1:%s" % options.port
    tornado.ioloop.IOLoop.instance().start()
