#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#=============================================================================
#  ProjectName: shiqi-yiyuan
#     FileName: webservice
#         Desc: soap协议服务端
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-03-05 15:13
#=============================================================================
"""
from spyne import ServiceBase, Application
from spyne import rpc
from spyne import Unicode, Iterable, Integer, Array, ComplexModel
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

from wsgiref.simple_server import make_server


class Person(ComplexModel):
    name = Unicode
    age = Unicode


class WebAPIService(ServiceBase):
    @rpc(Unicode, Integer, _returns=Iterable(Unicode))
    def say_hello(self, name, times):
        for i in range(times):
            yield "Hello %s, It's the %s time to meet you." % (name, i + 1)

    @rpc(Array(Person), Unicode, Unicode, _returns=Iterable(Unicode))
    def notify(self, persons, username, password):
        for person in persons:
            yield "name: %s, age: %s, %s, %s notify success" % (
                person.name, person.age, username, password)


def main():
    # You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    application = Application(
        [WebAPIService],
        tns="spyne.examples.hello",
        # tns="tns",
        in_protocol=Soap11(validator='lxml'),
        out_protocol=Soap11())

    wsgi_app = WsgiApplication(application)
    host = '0.0.0.0'
    port = 5558
    print "http://%s:%d" % (host, port)
    server = make_server(host, port, wsgi_app)
    server.serve_forever()


if __name__ == '__main__':
    main()
