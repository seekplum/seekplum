# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import requests
import subprocess

"""
下载网址 http://man.linuxde.net/ 的所有静态页面
"""


def run(cmd):
    """
    执行系统命令
    :param cmd:
    :rtype str
    :return: 执行命令的输出
    """
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    std_out, std_err = p.communicate()
    if std_err:
        raise Exception("cmd: %s, std_err: %s" % (cmd, std_err))
    else:
        return std_out


def create_dir():
    """创建各个类别的目录
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    url = "http://man.linuxde.net/"
    home_result = requests.get(url)
    # 主目录
    home_dir = re.findall(r'<h3>(.*)</h3>', home_result.text)
    first_dir = re.findall(r'<li><a href="(http://man.linuxde.net/sub/\S+)".*?>(\S+)</a></li>', home_result.text)
    for home in range(0, len(home_dir)):
        home_dir[home] = home_dir[home].encode("utf-8")
        home_dir[home] = home_dir[home].replace(' | ', '-')
        try:
            home_dir[home] = os.path.join(current_path, home_dir[home])
            run("mkdir -p %s" % home_dir[home])
            print home_dir[home]
        except Exception as e:
            print str(e)

    # 主目录和下一级目录的对应关系
    root_dir = dict()
    root_dir[json.dumps(first_dir[0:7])] = home_dir[0]  # 7
    root_dir[json.dumps(first_dir[7:13])] = home_dir[1]  # 6
    root_dir[json.dumps(first_dir[13:17])] = home_dir[2]  # 4
    root_dir[json.dumps(first_dir[17:27])] = home_dir[3]  # 10
    root_dir[json.dumps(first_dir[27:32])] = home_dir[4]  # 5
    return root_dir


def download(root_dir):
    """下载网页内容
    """
    for second_dir in root_dir:
        print root_dir[second_dir]
        for second in json.loads(second_dir):
            second = list(second)
            second[0] = second[0].encode("utf-8")
            second[1] = second[1].encode("utf-8")
            third_dir = os.path.join(root_dir[second_dir], second[1])
            run("mkdir -p %s" % third_dir)
            print third_dir
            second_result = requests.get(second[0])
            command = re.findall(r'<div class="name"><a href="(http://man.linuxde.net/\w*)".*?>(\w*)</a></div>',
                                 second_result.text)
            for html in command:
                html = list(html)
                html[0] = html[0].encode("utf-8")
                html[1] = html[1].encode("utf-8")
                html_content = requests.get(html[0])
                html_name = os.path.join(third_dir, html[1] + ".html")
                with open(html_name, 'wt') as f:
                    f.write(html_content.text.encode("utf-8"))
                f.close()


if __name__ == '__main__':
    dirs = create_dir()
    download(dirs)
