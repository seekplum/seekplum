#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
# file: websocket_chat.py

import json
import os
from uuid import uuid4
import tornado.websocket
import tornado.web
import tornado.httpserver
import tornado.ioloop
from tornado import options


class ChatRoom(object):
    """ 处理服务器与客户端的交互信息 """

    # 聊天室容器, 存储聊天室和其对应的`websocket`连接
    chat_room_container = {}
    # 消息缓存, 不过这里没有呈现到网页上
    cache = []
    cache_size = 200

    def register(self, ws_handler):
        """ 注册聊天室用户 """

        room = str(ws_handler.get_argument('n'))  # 获取所在聊天室
        session = str(ws_handler.get_argument('u'))
        ws_handler.session = session

        if room in self.chat_room_container:
            self.chat_room_container[room].append(ws_handler)
        else:
            self.chat_room_container[room] = [ws_handler, ]

        self.new_msg_trigger(ws_handler, is_new_user=True)

    def unregister(self, ws_handler):
        """ 离开聊天室, 注销用户 """

        room = str(ws_handler.get_argument('n'))

        self.chat_room_container[room].remove(ws_handler)

        self.new_msg_trigger(ws_handler, is_leave_user=True)

    def message_maker(self, session, message=None, is_leave=False, is_new=False,
                      self_new=False):
        """ 消息生成器 """

        _from = 'sys'
        if message:
            _from = session
            msg = message
        elif is_leave:
            msg = '(%s)离开了聊天室' % session
        elif is_new:
            msg = '欢迎(%s)加入聊天室' % session
        elif self_new:
            msg = '欢迎你加入聊天室'
        else:
            raise Exception('WTF?')

        msg = {
            'from': _from,
            'message': msg,
        }
        self.update_msg_cache(msg)
        return json.dumps(msg)

    def update_msg_cache(self, message):
        """ 消息缓存更新 """
        self.cache.append(message)
        if len(self.cache) > self.cache_size:
            self.cache = self.cache[-self.cache_size:]

    def send_room_message(self, ws_handler, message, except_self=False):
        """ 发送聊天室信息, except_self为True则该消息不推送给消息的生产者 """

        room = str(ws_handler.get_argument('n'))  # 获取所在聊天室

        if except_self:
            session = str(ws_handler.get_argument('u'))
            for ws_handler in self.chat_room_container[room]:
                if ws_handler.session != session:
                    ws_handler.write_message(message)
        else:
            for ws_handler in self.chat_room_container[room]:
                ws_handler.write_message(message)

    def send_left_msg(self, ws_handler):
        """ 发送离开信息 """

        session = str(ws_handler.get_argument('u'))

        msg = self.message_maker(session, is_leave=True)
        self.send_room_message(ws_handler, msg, except_self=True)

    def send_welcome_msg(self, ws_handler):
        """ 发送欢迎信息 """

        session = str(ws_handler.get_argument('u'))

        msg = self.message_maker(session, self_new=True)
        ws_handler.write_message(msg)

        msg = self.message_maker(session, is_new=True)
        self.send_room_message(ws_handler, msg, except_self=True)

    def send_chat_msg(self, ws_handler, message):
        """ 发送聊天信息 """

        session = str(ws_handler.get_argument('u'))

        msg = self.message_maker(session, message)
        self.send_room_message(ws_handler, msg)

    def new_msg_trigger(self, ws_handler, message=None, is_new_user=False,
                        is_leave_user=False):
        """ 消息触发器，将最新消息返回给对应聊天室的所有成员 """
        print "消息过来了：{}".format(message)
        if message:
            self.send_chat_msg(ws_handler, message)
        elif is_new_user:
            self.send_welcome_msg(ws_handler)
        elif is_leave_user:
            self.send_left_msg(ws_handler)
        else:
            raise Exception('WTF?')


class ChatRoomIndexPage(tornado.web.RequestHandler):
    """ 首页, 聊天室选择页 """

    def get(self, *args, **kwargs):
        # 生成随机标识码, 取代用户名
        session = uuid4()
        self.render('basic.html', session=session)


class ChatRoomInnerPage(tornado.web.RequestHandler):
    """ 聊天室内页 """

    def get(self, *args, **kwargs):
        # n=聊天室, u=用户
        n = self.get_argument('n')
        u = self.get_argument('u')
        self.render('room.html', n=n, u=u)


class NewChat(tornado.websocket.WebSocketHandler):
    """ WebSocket服务, 消息处理中转 """

    @property
    def chatroom(self):
        return self.application.chatroom

    def open(self):
        """ 新的WebSocket连接打开 """

        self.chatroom.register(self)

    def on_close(self):
        """ WebSocket连接断开 """

        self.chatroom.unregister(self)

    def on_message(self, message):
        """ WebSocket服务端接收到消息 """

        self.chatroom.new_msg_trigger(self, message)
        print "前端数据: {}".format(message)
        # 心跳包, 如果客户端接收到的话, 会返回一样的数据
        self.ping('answer me')

    def on_pong(self, data):
        """ 心跳包响应, data是`.ping`发出的数据 """

        print 'into on_pong the data is |%s|' % data


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', ChatRoomIndexPage),
            (r'/room', ChatRoomInnerPage),
            (r'/new_chat', NewChat),
        ]

        tornado_settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), 'template'),
        )

        super(Application, self).__init__(handlers, **tornado_settings)

        self.chatroom = ChatRoom()


if __name__ == '__main__':
    port = 8888
    options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port)
    print "server start http://127.0.0.1:%s" % port
    tornado.ioloop.IOLoop.current().start()
