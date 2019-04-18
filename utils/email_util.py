#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests


class Email163(object):
    def __init__(self, username, password):
        """网易163邮箱登录
        """
        self.username = username  # 邮箱用户名
        self.password = password  # 邮箱密码
        self.req_session = requests.Session()  # 所有请求用同一个session,保证登录后不失效
        self.sid = self.get_sid()  # 登录一次后， sid不用变，所以不用每次操作都获取sid

    def get_sid(self):
        """获取sid
        
        :rtype str
        :return
        网易邮箱的认证 sid, 在后续所有的请求中都会带上sid,作为登录成功的标识
        """
        headers = {
            'Host': 'mail.163.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'http://email.163.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        data = {
            'username': self.username,
            'url2': 'http://email.163.com/errorpage/error163.htm',
            'savalogin': '0',
            'password': self.password
        }
        params = {
            'funcid': 'loginone',
            'language': -1,
            'passtype': 1,
            'iframe': 1,
            'product': 'mail163',
            'from': 'web',
            'df': 'email163',
            'race': '-2_-2_-2_db',
            'module': '',
            'uid': self.username,
            'style': -1,
            'net': 'c',
            'skinid': 'null'
        }
        url = 'https://mail.163.com/entry/cgi/ntesdoor'
        response = self.req_session.post(url=url, headers=headers, data=data, params=params)
        sid = re.search(r'(?<=sid=).+(?=&df=email163)', response.text).group(0)
        return sid

    @staticmethod
    def get_id_param(content):
        """把id组合成参数
        
        解析api中返回的xml格式内容,在组合出后续操作需要的数据格式
        
        :rtype str, int
        :return id字符串, id的数量
        """
        pattern = re.compile(r'<string name="id">(\d+:.+)</string>')
        result = pattern.findall(content)
        id_param = "<string>{}</string>".format("</string><string>".join(result))
        return id_param, len(result)

    def get_inbox(self):
        """收件箱列表

        :rtype str
        :return API请求返回的数据
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:listMessages',
            'LeftNavfolder1Click': 1,
            'mbox_folder_enter': 1
        }
        data = {
            'var': '<?xml version="1.0"?><object><int name="fid">1</int><string name="order">date</string>'
                   '<boolean name="desc">true</boolean><int name="limit">100</int><int name="start">0</int>'
                   '<boolean name="skipLockedFolders">false</boolean><string name="topFlag">top</string>'
                   '<boolean name="returnTag">true</boolean><boolean name="returnTotal">true</boolean></object>'
        }
        response = self.req_session.post(url=url, data=data, params=params)
        content = response.content
        return content

    def get_deleted(self):
        """已删除邮箱列表

        :rtype str
        :return API请求返回的数据
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:listMessages',
            'LeftNavfolder1Click': 1,
            'mbox_folder_enter': 4
        }
        data = {
            'var': '<?xml version="1.0"?><object><int name="fid">4</int><string name="order">date</string>'
                   '<boolean name="desc">true</boolean><int name="limit">10</int><int name="start">0</int>'
                   '<boolean name="skipLockedFolders">false</boolean><boolean name="returnTag">true</boolean>'
                   '<boolean name="returnTotal">true</boolean></object>'
        }
        response = self.req_session.post(url=url, data=data, params=params)
        content = response.content
        return content

    def get_send(self):
        """已发送邮箱列表

        :rtype str
        :return API请求返回的数据
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:listMessages',
            'LeftNavfolder1Click': 1,
            'mbox_folder_enter': 3

        }
        data = {
            'var': '<?xml version="1.0"?><object><int name="fid">3</int><string name="order">date</string>'
                   '<boolean name="desc">true</boolean><int name="limit">100</int><int name="start">0</int>'
                   '<boolean name="skipLockedFolders">false</boolean><string name="topFlag">top</string>'
                   '<boolean name="returnTag">true</boolean><boolean name="returnTotal">true</boolean></object>'
        }
        response = self.req_session.post(url=url, data=data, params=params)
        content = response.content
        return content

    def delete_deleted(self):
        """删除已删除邮箱
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:deleteMessages',
            'mbox_toolbar_permanentdeleted': 1
        }
        id_param, count = self.get_id_param(self.get_deleted())
        data = {
            'var': '<?xml version="1.0"?><object><array name="ids">{id_param}</array></object>'.format(
                id_param=id_param)
        }
        response = self.req_session.post(url=url, data=data, params=params)
        print response.status_code
        return count

    def delete_send(self):
        """删除已发送邮箱
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:updateMessageInfos',
            'mbox_toolbar_permanentdeleted': 1
        }
        id_param, count = self.get_id_param(self.get_send())
        data = {
            'var': '<?xml version="1.0"?><object><array name="ids">{id_param}</array><object name="attrs">'
                   '<int name="fid">4</int></object></object>'.format(id_param=id_param)
        }
        response = self.req_session.post(url=url, data=data, params=params)
        print response.status_code
        return count

    def delete_inbox(self):
        """删除收件箱
        """
        url = 'http://mail.163.com/js6/s'
        params = {
            'sid': self.sid,
            'func': 'mbox:updateMessageInfos',
            'mbox_toolbar_allornone': 1,
            'mbox_toolbar_movetodeleted': 1
        }
        id_param, count = self.get_id_param(self.get_inbox())
        data = {
            'var': '<?xml version="1.0"?><object><array name="ids">{id_param}</array><object name="attrs">'
                   '<int name="fid">4</int></object></object>'.format(id_param=id_param)
        }
        response = self.req_session.post(url=url, data=data, params=params)
        print response.status_code
        return count


def delete_email():
    """删除邮箱邮件
    """
    name = "xxx@163.com"
    pwd = "xxx"
    manager = Email163(name, pwd)
    func_list = [
        manager.delete_inbox,  # 收件箱
        manager.delete_send,  # 已发件箱
        manager.delete_deleted  # 已删除
    ]
    # 收件箱，发件箱，已删除的邮件全部删除后结束
    for func in func_list:
        while True:
            try:
                count = func()
            except Exception as e:
                print("执行函数: {} 发生了错误: {}".format(func.__name__, e.message))
                break
            else:
                if count <= 0:
                    break


if __name__ == '__main__':
    delete_email()
