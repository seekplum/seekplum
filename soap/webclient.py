#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: shiqi-yiyuan
#     FileName: webclient
#         Desc: soap协议客户端
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-03-06 09:54
#=============================================================================
"""

import suds
import logging

logging.basicConfig(level=logging.INFO)


class WebServiceClient(object):

    def __init__(self, url):
        self.client = suds.client.Client(url)
        print "wsdl services: ", self.client.wsdl.services
        print "client: ", self.client

    def say_hello(self):
        return self.client.service.say_hello("hjd", 3)

    def notify(self):
        person = {
            "name": "hjd",
            "age": "100"
        }
        person2 = {
            "name": "seekplum",
            "age": "500"
        }
        d = self.client.factory.create("PersonArray")
        d.Person.append(person)
        d.Person.append(person2)
        return self.client.service.notify(d)


def main():
    test = WebServiceClient('http://127.0.0.1:5558/?wsdl')
    print "say hello: ", test.say_hello()
    print "notify: ", test.notify()


if __name__ == '__main__':
    main()
