#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import redis

from redis.client import PubSub
from sse import Sse
from tornado import gen
from tornado import web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options


def build_sse_msg(message, event=None, id_=None):
    sse = Sse()
    if id_:
        sse.set_event_id(id_)
    sse.add_message(event, message)
    sse_msg = "".join(sse)
    return sse_msg


class SSEModule(PubSub):
    """Module PubSub class"""

    def __init__(self,
                 connection_pool,
                 shard_hint=None,
                 ignore_subscribe_messages=False):
        self.fd = None
        super(self.__class__, self).__init__(connection_pool, shard_hint, ignore_subscribe_messages)

    def on_connect(self, connection):

        super(self.__class__, self).on_connect(connection)
        self.fd = connection._sock
        io_loop = IOLoop.current()
        io_loop.add_handler(connection._sock, self.loop_callback, IOLoop.READ)

    def loop_callback(self, fd, events):
        """Deail with subscribe messages"""
        self.callback()

    def set_handler(self, handler):
        """
        set the sse request handler
        """
        self.handler = handler

    def callback(self):
        # result = {"id": id, "event": xxx, message: {"a":1, "b": 2}}
        message = self.get_message()
        data = message["data"]
        if isinstance(data, (int, long)):
            return
        data = json.loads(data)
        message = json.dumps(data["message"])
        event = data["event"]
        id_ = data["id"]

        sse_msg = build_sse_msg(message, event, id_)

        if not self.handler.is_alive:
            io_loop = IOLoop.current()
            io_loop.remove_handler(self.fd)
        else:
            self.handler.send_message(sse_msg)


class SSEHandler(web.RequestHandler):
    """
    usage: just inherite the class and define the redis_pool method with `@property`
    example:
        ```
        class TestHandler(SSEHandler):
            @property
            def redis_pool(self):
                return redis_util.get_pool()
        ```
    """
    __metaclass__ = abc.ABCMeta
    CHANNEL = "sse"

    def __init__(self, application, request, **kwargs):
        super(SSEHandler, self).__init__(application, request, **kwargs)
        self.sub_obj = None
        self.stream = request.connection.stream

    def prepare(self):
        SSE_HEADERS = (
            ('Content-Type', 'text/event-stream; charset=utf-8'),
            ('Cache-Control', 'no-cache'),
            ('Connection', 'keep-alive'),
            ('X-accel-Buffering', 'no'),
            ('Access-Control-Allow-Origin', '*'),
        )
        for name, value in SSE_HEADERS:
            self.set_header(name, value)

    @abc.abstractproperty
    def redis_pool(self):
        """
        this property will be supplied by the inheriting classes individually
        """
        pass

    @property
    def is_alive(self):
        return not self.stream.closed()

    @gen.coroutine
    def get(self, *args, **kwargs):
        channels = self.get_argument("channels")
        if not channels:
            raise Exception("channels shoud in url arguments")
        channels = channels.split(",")
        sub_obj = SSEModule(self.redis_pool)
        sub_obj.set_handler(self)
        sub_obj.subscribe(*channels)
        self.sub_obj = sub_obj
        # send message when on open, when use nginx, on_open will not work in js
        msg = build_sse_msg(message="ok", event="on_open")
        self.send_message(msg)
        while self.is_alive:
            yield gen.sleep(1000 * 1)
        del sub_obj

    def send_message(self, message):
        self.write(message)
        self.flush()

    def on_connection_close(self):
        # unsubscribe when close the connection
        self.sub_obj.unsubscribe()
        self.stream.close()


html = """
<div id="messages"></div>
<script type="text/javascript">
    if(EventSource == "undefined") {
        alert("sse not support!");
    }
    // var sse = new EventSource('http://127.0.0.1:11100/seekplum/sse?channels=seekplum');
    var sse = new EventSource('/events?channels=seekplum');
    sse.addEventListener('detail_info', function(data) {
        console.log("监听数据： ", data);
        var div = document.getElementById("messages");
        div.innerHTML = data.data + "<br>" + div.innerHTML;
        if (data.lastEventId == 'CLOSE') {
            console.log("关闭sse");
            sse.close();
        }
    }, false);
    sse.addEventListener('on_open', function(data) {
        console.log("打开时接收数据： ", data);
        var div = document.getElementById("messages");
        div.innerHTML = data.data + "<br>" + div.innerHTML;
    }, false);

    //  default event type is "message"
    sse.onmessage = function(data) {
        console.log("正常接收到数据： ", data);
        var div = document.getElementById("messages");
    };

    // on open
    sse.onopen = function () {
      console.log("sse open!")
    };

    sse.onerror = function () {
      console.log("sse closed!")
    };

</script>"""


class THandler(SSEHandler):
    @property
    def redis_pool(self):
        pool = redis.ConnectionPool(
            host="localhost",
            port="6379",
            # password="password",
            db=0)
        return pool


class MainHandler(web.RequestHandler):
    def get(self):
        self.write(html)


port = 9001
define("port", default=port, help="run on the given port", type=int)


def run_server():
    options.parse_command_line()

    app = web.Application(
        [
            (r'/', MainHandler),
            (r'/events', THandler)
        ],
        debug=True
    )
    server = HTTPServer(app)
    server.listen(options.port)
    print "Start server: http://127.0.0.1:%s" % port
    IOLoop.instance().start()


if __name__ == "__main__":
    run_server()
