#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: deploy
#         Desc: 交互式ssh
#       Author: hjd
#     HomePage: seekplum.github.io
#   LastChange: 2018-04-03 20:09
#=============================================================================
"""
import argparse
import time
import logging
import re
import subprocess

import paramiko
import pexpect

from pexpect.pxssh import pxssh

root_logger = logging.getLogger()  # 或使用未公开的 logging.root
root_logger.level = logging.DEBUG  # 修改日志级别


def get_ssh(ip, port=22, conn_timeout=3, username="root", password="letsg0", key_filename=None):
    """获取一个ssh连接对象

    :param ip: 主机ip
    :param username: 登录用户名
    :param port: 端口号
    :param conn_timeout:　超时时间
    :param password: 登录密码
    :param key_filename: 登录密钥路径
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ip, port=port, timeout=conn_timeout, username=username, key_filename=key_filename,
                password=password)
    return ssh


def get_sshpx(ip, port=22, conn_timeout=3, username="root", password="letsg0", key_filename=None):
    """获取一个　交互式的ssh　连接对象

    :param ip: 主机ip
    :param username: 登录用户名
    :param port: 端口号
    :param conn_timeout:　超时时间
    :param password: 登录密码
    :param key_filename: 登录密钥路径
    """
    ssh_config = dict(ip=ip,
                      username=username,
                      port=port,
                      conn_timeout=conn_timeout)
    if password:
        ssh_config["password"] = password
    elif key_filename:
        ssh_config["key_filename"] = key_filename
    pool = PXSSH_Factory(**ssh_config)
    sshpx = pool.create()
    return sshpx


def run(cmd, ssh):
    """执行系统命令
    """
    logging.info("cmd: {}".format(cmd))
    result = {}
    try:
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            stdin.close()
            stdout.flush()
            out_msg = stdout.read()
            err_msg = stderr.read()
            exit_code = 0
        else:
            p = subprocess.Popen(cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out_msg = p.stdout.read()
            err_msg = p.stderr.read()
            exit_code = p.wait()

        result["stdout"] = out_msg
        result["stderr"] = err_msg
        result["exit_code"] = exit_code
        logging.info("cmd output:\n" + out_msg)
        if err_msg:
            logging.exception("cmd error msg:\n" + err_msg)
        return result
    except Exception as e:
        logging.exception("exception at run {}: {}".format(cmd, e))
        result["stdout"] = ""
        result["stderr"] = e
        result["exit_code"] = 1
        return result


class RunCMDError(Exception):
    """raise when run cmd error
    """
    pass


def run_cmd(cmd, ssh=None):
    """执行系统命令或远程机器命令
    """
    result = run(cmd=cmd, ssh=ssh)
    if result["exit_code"] != 0:
        msg = result["stderr"].strip() if result["stderr"] else result["stdout"].strip()
        raise RunCMDError(msg)
    else:
        return result["stdout"]


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


def install(host):
    """安装脚本
    """
    ssh = get_ssh(host)
    # 查询主机名
    cmd = "hostname"
    hostname = run_cmd(cmd, ssh=ssh)
    logging.info(hostname)

    sshpx = get_sshpx(host)
    sshpx.timeout = 60 * 10  # 10分钟没有执行完抛超时异常

    # 执行安装脚本
    cmd = "cd /root/seekplum_cloud && python install.py"
    sshpx.sendline(cmd)
    sshpx.expect("Ignore\s*warnings\?\(yes\/no\):")

    sshpx.sendline("yes")
    logging.info(sshpx.before)

    while True:
        index = sshpx.expect(["OK", sshpx.PROMPT, pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            logging.info(sshpx.before)
        else:
            break
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-s" "--server",
                        action="store",
                        required=False,
                        dest="server",
                        default="192.168.1.157",
                        help="The host to be deployed."
                        )
    args = parser.parse_args()
    install(args.server)
