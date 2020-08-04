#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
1.安装mitmproxy

pip install mitmproxy==0.18.2

或者

brew install mitmproxy

2.配置PAC脚本

```js
function FindProxyForURL(url, host) {
    // 百度转必应
    if (dnsDomainIs(host, "baidu.com") || dnsDomainIs(host, "www.baidu.com")) {
        return "PROXY 127.0.0.1:8123";
    }

    return "DIRECT";
}
```

3.访问 http://mitm.it/ 下载证书

下载后双击打开，`钥匙串` 选择 `系统`，之后配置 `始终信任`

4.启动服务,用 `mitmproxy`, `mitmdump`, `mitmweb` 这三个命令中的任意一个即可

mitmproxy -p 8123 -s proxy_rewrite.py --no-upstream-cert --insecure

不同版本注意命令行选项是否更改，如

mitmdump -p 8123 -s proxy_rewrite.py --set upstream_cert=false --ssl-insecure

5.浏览器访问 http://www.baidu.com/ 显示必应官网
"""

import mitmproxy.script


SOURCE_HOST = "www.baidu.com"
TARGET_HOST = "cn.bing.com"
TARGET_PORT = 80


@mitmproxy.script.concurrent
def request(flow):
    r = flow.request
    host = r.headers.get("Host", "")
    authority = r.headers.get(':authority', '')
    print("Source host: {}, authority: {}, target host: {}".format(host, authority, TARGET_HOST))
    if host in (SOURCE_HOST,):
        # 必须先设置 host 再改写 header, 不然会被覆盖
        (r.scheme, r.host, r.port) = ("http", TARGET_HOST, TARGET_PORT)
        r.headers["Host"] = TARGET_HOST
        # r.headers[":authority"] = authority

