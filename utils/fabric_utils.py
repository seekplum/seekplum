#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: fabric_utils
#         Desc: 通过 fabric 批量部署项目
#               文档地址: http://docs.fabfile.org/en/1.14/
#       Author: hjd
#        Email:
#     HomePage:
#      Version: 
#   LastChange: 2018-03-15 16:38
#      History:
#=============================================================================
"""

from fabric.api import local, lcd, cd, run, env, execute, roles

from fabric.colors import green, red, yellow

env.hosts = [
    "root@xx.xx.xx.xx:22"  # 用户名@IP:端口号
]
# env.password = "xxxx"  # 机器密码 # 若没有这行,需要提前打通ssh
env.roledefs = {
    "test_server": [
        "root@xx.xx.xx.xx:22"
    ],
    "demo_server": [
        "root@xx.xx.xx.xx:22"
    ]
}


def hello(name, value):
    """运行方式

    若当前文件名为 `fabfile.py`
        fab  hello:name=age,value=20
    否则
        fab -f fabric_utils.py hello:name=age,value=20
    """
    print("%s = %s" % (name, value))


@roles("test_server")
def task_test():
    run("hostname")


@roles("demo_server")
def task_demo():
    run("hostname -I")


def ls_fab():
    with lcd("/tmp"):  # 进入本地目录
        local("ls -l")  # 执行本地命令


def update():
    with cd("/tmp"):  # 进入远程机器目录
        run("ls -l")  # 执行远程操作命令


def task():
    execute(task_test)
    execute(task_demo)


def show():
    print green("success")
    print red("fail")
    print yellow("warn")
