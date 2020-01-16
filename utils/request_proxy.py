# -*- coding: utf-8 -*-

import requests

# 1.在 url 中指定用户名密码
proxies = {
    "http": "http://10.0.0.7:8850",
    # "https": "http://10.0.0.7:8850",
    # "http": "http://test:ceshi@test5.goodtp.com:8700",
    "https": "http://test:ceshi@test5.goodtp.com:8700",
}

# 2.通过 HTTPProxyAuth 指定用户名密码

# from requests.auth import HTTPProxyAuth
#
# auth = HTTPProxyAuth("test", "ceshi")
# url = ""
# requests.get(url, params=params, proxies=proxies, auth=auth)

params = {
    "token": "xxxx",
    "fmt": "json"
}
response = requests.get("http://xxx/common/login/test", params=params, proxies=proxies)
result = response.json()
print("result1: {}".format(result))

session = response.cookies.values()[0]
headers = {
    "Cookie": "super_id={};session={}".format(session, session)
}
response = requests.get("http://xxx/common/huodong/running", params=params, headers=headers, proxies=proxies)
result = response.json()
assert result["success"]
acts = result["acts"]
assert isinstance(acts, list)
names = "\n\t".join(["{}-{}".format(a["act_type"], a["name"].encode("utf-8")) for a in acts])
print("活动列表: \n\t{}".format(names))
