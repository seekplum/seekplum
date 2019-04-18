#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: fluentbit
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-02-18 20:15
#=============================================================================
"""

from __future__ import absolute_import

import os


def insert_server():
    context = """[SERVICE]
    Flush                     3
    Daemon                    off
    Log_Level                 debug
    
    storage.path              /var/log/flb-storage/
    storage.sync              normal
    storage.checksum          off
    storage.backlog.mem_limit 5M

    Parsers_File              parsers.conf

@INCLUDE conf.d/*.conf
@INCLUDE es.d/*.conf

"""
    with open("fluent-bit.conf", "w+") as f:
        f.write(context)


def insert_elasitc(host, tag):
    context = """[OUTPUT]
    Name     es
    Match    %s
    Host     %s
    Port     10015
    Logstash_Format On
""" % (tag, host)

    file_path = os.path.join("es.d", "%s-%s.conf" % (tag, host))
    with open(file_path, "w+") as f:
        f.write(context)


def insert_configuration(tag, parser_head, parser):
    context = """[INPUT]
    Name    tail
    Path    /var/log/qflame_exporter.log*
    Tag     %s
    Multiline On
    Parser_Firstline %s
    Parser_1 %s
    Path_Key file

[FILTER]
    Name record_modifier
    Match %s
    Record ip 192.168.1.105
    Record hostname seekplum


""" % (tag, parser_head, parser, tag)

    file_path = os.path.join("conf.d", "%s.conf" % tag)
    with open(file_path, "w+") as f:
        f.write(context)


def insert_parser(parser_head, parser):
    context = """
[PARSER]
    Name %s""" % parser_head + """
    Format regex
    Regex ^time="(?<log_time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})[+-]\d+:\d+" level=(?<level>\w+) msg="(?<message>.*)"
    Time_Key time
    Time_Format %Y-%m-%d%T%H:%M:%S%Z

""" + """[PARSER]
    Name %s
    Format regex
    Regex .*

""" % parser

    with open("parsers.conf", "a+") as f:
        f.write(context)


def insert_normal_parser():
    context = """[PARSER]
    Name normal_parser
    Format regex
    Regex .*

"""

    with open("parsers.conf", "a+") as f:
        f.write(context)


def main():
    if not os.path.exists("conf.d"):
        os.makedirs("conf.d")
    if not os.path.exists("es.d"):
        os.makedirs("es.d")
    host1 = "192.168.1.137"
    # host2 = "192.168.1.105"
    insert_normal_parser()
    insert_server()
    for i in xrange(1, 2):
        tag = "qflame%s" % i
        # parser_head = "qflame_log_parser_head%s" % i
        # parser = "qflame_log_parser%s" % i
        parser_head = "normal_parser"
        parser = "normal_parser"
        insert_configuration(tag, parser_head, parser)
        insert_elasitc(host1, tag)
        # insert_elasitc(host2, tag)


if __name__ == '__main__':
    main()
