#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: query
#         Desc: ElasticSearch查询Demo
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-11-16 18:18
#=============================================================================
"""

from elasticsearch import Elasticsearch

ES_HOST = "192.168.1.78"
ES_PORT = 9200


class ElasticSearchClient(object):
    def __init__(self, es):
        """ElasticSearch客户端，支持搜索数据

        :param es: 实例化的es对象
        :type es: Elasticsearch
        :example es: Elasticsearch()
        """
        self._es = es

    def search_body(self, body):
        """搜索数据

        :param body: 查询参数
        :type body: dict
        :example body: {
            "query": {
                "match_phrase": {
                    "name": "alertmanager"
                }
            }
        }

        :rtype dict
        :return 查询结果
        :example {
            'hits': {
                'hits': [
                    {
                        '_score': 0.18232156,
                        '_type': 'fluentd',
                        '_id': 'aybAFWcB90wAhiDJQr4S',
                        '_source': {
                            'status': 'RUNNING',
                            'name': 'alertmanager',
                            'level': 'INFO',
                            '@timestamp': '2018-11-15T13:02:57.000000000+08:00',
                            'hostname': 'seekplum-98lite-dev',
                            'state': 'success:',
                            'line': '394'
                        },
                        '_index': 'logstash-2018.11.15'},
                    {
                        '_score': 0.18232156,
                        '_type': 'fluentd',
                        '_id': 'bCYTFmcB90wAhiDJrr6i',
                        '_source': {
                            'status': 'RUNNING',
                            'name': 'alertmanager',
                            'level': 'INFO',
                            '@timestamp': '2018-11-15T14:34:04.000000000+08:00',
                            'hostname': 'seekplum-98lite-dev', 'state': 'success:',
                            'line': '520'
                        },
                        '_index': 'logstash-2018.11.15'
                    }],
                'total': 2,
                'max_score': 0.18232156
            },
            '_shards': {
                'successful': 11,
                'failed': 0,
                'skipped': 0,
                'total': 11
            },
            'took': 8,
            'timed_out': False
        }
        """
        return self._es.search(body=body)


def print_text(text):
    print text


def get_data(client):
    """查询数据

    :param client:
    :type client: ElasticSearchClient
    :example client: ElasticSearchClient(es)
    """
    body = {
        "query": {
            "match_phrase": {
                "name": "alertmanager"
            }
        }
    }
    result = client.search_body(body)
    hists = result["hits"]
    total = hists["total"]

    print_text("total: {}".format(total))

    for item in hists["hits"]:
        source = item["_source"]

        timestamp = source["@timestamp"]
        name = source["name"]
        hostname = source["hostname"]
        level = source["level"]
        status = source["status"]

        message = "timestamp: {}, hostname: {}, name: {}, level: {}, status: {}".format(timestamp, hostname, name,
                                                                                        level, status)
        print_text(message)


def get_page_data(client, number, page_line):
    """查询分页数据

    :param client:
    :type client: ElasticSearchClient
    :example client: ElasticSearchClient(es)

    :param number: 指定页数
    :type number: int
    :example number: 3

    :param page_line: 每页条数， ElasticSearch中默认值 10 条
    :type page_line: int
    :example page_line: 20
    """
    body = {
        # 搜索
        "query": {
            # 广泛匹配
            "match": {
                "hostname": "host"
            },

            # 精确匹配
            # "match_phrase": {
            #     "hostname": "host-192-168-1-178"
            # }
        },

        # 分页
        "from": number * page_line,
        "size": page_line,

        # 排序
        "sort": {
            "@timestamp": {
                "order": "asc",
                # "order": "desc"
            }
        }

    }

    result = client.search_body(body)

    hists = result["hits"]
    total = hists["total"]

    print_text("total: {}".format(total))

    for item in hists["hits"]:
        source = item["_source"]

        timestamp = source["@timestamp"]
        hostname = source["hostname"]
        code = source["code"]
        method = source["method"]
        host = source["host"]

        message = "timestamp: {}, host: {}, hostname: {}, method: {}, code: {}".format(timestamp, host, hostname,
                                                                                       method, code)
        print_text(message)


def main():
    hosts = "{host}:{port}".format(host=ES_HOST, port=ES_PORT)
    es = Elasticsearch(hosts=hosts)
    client = ElasticSearchClient(es)
    get_data(client)
    get_page_data(client, 1, 11)


if __name__ == '__main__':
    main()
