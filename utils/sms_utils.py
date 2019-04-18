#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: sms_utils
#         Desc: 短信对接脚本
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-12-27 15:34
#=============================================================================
"""
import suds
import json
import logging
import sys

url = "http://ip:8080/api/services/SmsMessageService?wsdl"
username = "user"
password = "password"

logging.basicConfig(level=logging.INFO, filename="sms.log",
                    format='%(levelname)s [%(asctime)s] [%(pathname)s L%(lineno)d] %(message)s')

client = suds.client.Client(url, location=url)
client.set_options(timeout=20)


def send_sms(message):
    print "building client ..."
    # print client
    print "finish building"
    print "sending sms ..."
    result = client.service.send(username, password, message)
    # result = client.service.getGeoIPContext()
    print "ok"
    logging.info(result)


def test_user():
    print "start testing username and password"
    result = client.service.activeTest(username=username, password=password)
    print result
    print "finish testing...\n{}\n".format(result)


def build_message(params):
    content = "{warn_status}[{time}] {db_ip}({single_name}):{category}-{send_message}".format(**params)
    # content = "test"
    message = client.factory.create("ns2:SmsMessage")
    message.content = content
    # message.destAddr = ",".join(params.get("mobile_no", None))
    message.destAddr = params["mobile_no"]
    message.reqReport = True
    return message


if __name__ == "__main__":
    try:
        parameter = json.loads(sys.argv[1])
        message = build_message(parameter)
        # test_user()
        send_sms(message)
    except Exception, e:
        logging.error("SMS SEND ERROR: {}".format(e))
