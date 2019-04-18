#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: ssh_utils
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-07-12 12:41
#=============================================================================
"""
import re
import logging
import pexpect

from pexpect.pxssh import pxssh

root_logger = logging.getLogger()  # 或使用未公开的 logging.root
root_logger.level = logging.DEBUG  # 修改日志级别


class my_pxssh(pxssh):
    def __init__(self, ip, username, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.username = username
        self.ip = ip
        self.is_sendline = False  # 用于打log
        self.continue_expect = False  # 用于打log

    def sendline(self, s=""):
        """重载父类方法，必须返回
        """
        logging.info("pxepect ip: {}, cmd: {}".format(self.ip, s))
        self.is_sendline = False
        self.continue_expect = False  # 连续跟多个expect
        for cmd in ["srvctl", "crsstat", "crsctl", "dbca", ]:
            if s and s.startswith(cmd):
                self.is_sendline = True
                break
        if s and self.is_sendline:
            logging.info("========= cmd pexpect({}) ========:\n{}".format(self.ip, s))
        return super(self.__class__, self).sendline(s)

    def expect(self, *args, **kwargs):
        """重载父类方法，必须返回

        注意字符的转义,正则的特殊字符需要转义
        """
        result = super(self.__class__, self).expect(*args, **kwargs)
        output = self.before
        real_output = "\n".join(output.splitlines()[0:])
        logging.info("========= output(pexpect) ======:\n{}\n======={}".format(real_output, self.after))
        if self.is_sendline or self.continue_expect:
            self.is_sendline = False
            self.continue_expect = True
        return result

    def _logout(self, username):
        """退出之前的用户
        """
        output = self.exec_command('whoami', 0.5)
        count = 0
        while username != output and count < 5:
            output = self.exec_command("exit")
            count += 1

    def exec_command(self, cmd, timeout=60):
        self.sendline(cmd)
        try:
            self.expect([self.PROMPT, pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
            result = "\n".join(self.before.splitlines()[1:])  # OK
            # 去掉颜色
            pure_result = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', result). \
                replace('\b', '').replace('\r', '')
            return pure_result
        except Exception as e:
            raise Exception("excute error cmd({}): {}, output: {}, error, {}".format(self.ip, cmd, self.before, e))


class PXSSH_Factory(object):
    def __init__(self, ip, username, port, conn_timeout, password=None, key_filename=None):
        """

        :param ip: 主机ip
        :param username: 登录用户名
        :param port: 端口号
        :param conn_timeout:　超时时间
        :param password: 登录密码
        :param key_filename: 登录密钥路径
        """

        self.hostname = ip
        self.username = username
        self.password = password
        self.port = port
        self.conn_timeout = conn_timeout  # ssh连接超时时间
        self.key_filename = key_filename

    def create(self, retry=4):
        """创建pxssh对象

        :param retry: 重试次数
        :type retry int
        """
        _ssh = my_pxssh(ip=self.hostname, username=self.username, timeout=self.conn_timeout, maxread=5000,
                        options={
                            "StrictHostKeyChecking": "no",
                            "UserKnownHostsFile": "/dev/null"},
                        )
        try:
            login_kwargs = dict(server=self.hostname,
                                username=self.username,
                                port=self.port,
                                auto_prompt_reset=False,
                                login_timeout=self.conn_timeout,
                                original_prompt=r"[#>%$]")
            if self.password:
                login_kwargs["password"] = self.password
            elif self.key_filename:
                login_kwargs["ssh_key"] = self.key_filename
            _ssh.login(**login_kwargs)
            _ssh.setwinsize(100, 1000)
            _ssh.set_unique_prompt()
            _ssh.prompt(timeout=0.5)

        except Exception as e:
            if retry <= 0:
                return 0
            logging.exception(e)
            logging.error("========== login {} failed =========".format(self.hostname))
            return self.create(retry=retry - 1)
        else:
            logging.info("========== login {} succeed ========".format(self.hostname))
            return _ssh
