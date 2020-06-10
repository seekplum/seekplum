#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
1.安装Python包

pip install mitmproxy==0.18.2

2.配置PAC脚本

function FindProxyForURL(url, host) {
    // 百度转必应
    if (dnsDomainIs(host, "baidu.com") || dnsDomainIs(host, "www.baidu.com")) {
        return "PROXY 127.0.0.1:8123";
    }

    return "DIRECT";
}

3.启动服务,用 `mitmproxy`, `mitmdump`, `mitmweb` 这三个命令中的任意一个即可

mitmproxy -p 8123 -s proxy_rewrite.py --no-upstream-cert --insecure

4.浏览器访问 http://www.baidu.com/ 显示必应官网
"""

import mitmproxy.script


SOURCE_HOST = "www.baidu.com"
TARGET_HOST = "cn.bing.com"
TARGET_PORT = 80


@mitmproxy.script.concurrent
def request(flow):
    r = flow.request
    host = r.headers.get("Host", "")
    print("Source host: {}, target host: {}".format(host, TARGET_HOST))
    if host in (SOURCE_HOST,):
        # 必须先设置 host 再改写 header, 不然会被覆盖
        (r.scheme, r.host, r.port) = ("http", TARGET_HOST, TARGET_PORT)
        r.headers["Host"] = TARGET_HOST
