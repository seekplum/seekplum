#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import requests
import urlparse


def generate_requests_form_data_type(data):
    """把正常数据转成from_data需要的格式"""
    if isinstance(data, list):
        return None, json.dumps(data)
    elif isinstance(data, dict):
        for k, v in data.iteritems():
            data[k] = None, json.dumps(v)
        return data
    elif isinstance(data, (int, float)):
        return None, str(data)
    elif isinstance(data, basestring):
        return None, data


def add_header_on_requests_from_data(headers, data):
    """添加header和form-data标识到数据中"""
    boundary = "------WebKitFormBoundary7MA4YWxkTrZu0gW"
    headers["content-type"] = "multipart/form-data; boundary={boundary}".format(boundary=boundary)
    disposition = "Content-Disposition: form-data;"
    params = disposition.join(['\nname="{}"\n\n{}\r\n'.format(k, v) for k, v in data.iteritems()])

    context = "{boundary}\r\n{params}{boundary}".format(boundary=boundary, params=params)

    return headers, context


class MethodAttrError(Exception):
    """函数名错误"""
    pass


class HttpRequest(object):
    def __init__(self, domain, is_form_data=False, from_name="files"):
        """

        :param domain: str 域名
        :param is_form_data: bool 是否是`form-data`格式数据
        """
        self._domain = domain
        self._from_name = from_name
        self._is_form_data = is_form_data
        self._session = requests.Session()

    def set_is_form_data(self, value):
        self._is_form_data = value

    def parse_form_data(self, **kwargs):
        kwargs[self._from_name] = generate_requests_form_data_type(kwargs[self._from_name])
        return kwargs

    def _option(self, url, **kwargs):
        uri = urlparse.urljoin(self._domain, url)
        if self._is_form_data:
            kwargs = self.parse_form_data(**kwargs)
        return uri, kwargs

    def get(self, url, **kwargs):
        uri = urlparse.urljoin(self._domain, url)
        return self._session.get(uri, **kwargs)

    def post(self, url, **kwargs):
        return self._session.post(self._option(url, **kwargs))

    def put(self, url, **kwargs):
        return self._session.put(self._option(url, **kwargs))

    def delete(self, url, **kwargs):
        return self._session.delete(self._option(url, **kwargs))


def main():
    url = "/api/test/getEncryptRequestData"

    header = {
        "requestSeqNo": "Picc1201254715345799565681",
        "partnerCode": "09999999",
        "interfaceCode": "GetPolicyDetail",
        "interfaceVersion": "v1"
    }
    data = {
        "policyNumber": "PUBA201633020000000066"
    }
    # encrypt_data = requests.post(url=url, files={
    #     "body": (None, json.dumps(data)),
    #     "header": (None, json.dumps(header))
    # })
    http_request = HttpRequest("http://host.com", is_form_data=True)
    encrypt_data = http_request.post(url=url, files={"body": data, "header": header})
    print encrypt_data


if __name__ == '__main__':
    main()
