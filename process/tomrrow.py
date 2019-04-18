#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import requests

from tomorrow import threads

urls = [
    'http://www.youku.com/',
    'http://cn.bing.com/',
    'http://www.baidu.com/',
    'http://www.youku.com/',
    'http://python.org/',
    'http://github.com/',
    'http://www.youku.com/',
    'http://cn.bing.com/',
    'http://www.baidu.com/',
    'http://www.youku.com/',
    'http://python.org/',
    'http://github.com/'
]


def get_number():
    return 10


def download(url):
    return requests.get(url)


@threads(5)
def download2(url):
    return requests.get(url)


def test():
    start = time.time()
    responses = [download(url) for url in urls]
    html = [response.text for response in responses]
    end = time.time()
    print "Time: %f seconds" % (end - start)


def test2():
    start = time.time()
    responses = [download2(url) for url in urls]
    html = [response.text for response in responses]
    end = time.time()
    print "2 Time: %f seconds" % (end - start)


if __name__ == '__main__':
    test()
    test2()
