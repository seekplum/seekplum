#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import time
import sys
import socket
import datetime
import subprocess
import logging
import logging.handlers

import paramiko


def get_logger(level):
    """设置日志格式,路径

    :param level 日志级别
    :type level int
    :example level 20

    :rtype logging.Logger
    :return 日志对象
    """
    log_file_name = "%s.log" % os.path.basename(__file__).rsplit(".", 1)[0]
    logger_ = logging.getLogger("disk")
    formatter = logging.Formatter('[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    log_file_handle = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=10 * 1024 * 1024, backupCount=10)
    log_file_handle.setFormatter(formatter)

    # 把信息打印到终端
    stdout_handle = logging.StreamHandler()
    stdout_handle.setFormatter(formatter)

    # 把信息记录日志文件
    logger_.addHandler(stdout_handle)
    logger_.addHandler(log_file_handle)

    logger_.setLevel(level)
    return logger_


logger = get_logger(logging.INFO)


class SSHException(Exception):
    """ssh异常
    """
    pass


def get_ssh(host, username, port=22, conn_timeout=10, password=None, key_filename=None):
    """获取一个 ssh连接对象

    :param host: 主机ip
    :type host basestring
    :example host 10.10.100.1

    :param username: 登录用户名
    :type username basestring
    :example username root

    :param password: 登录密码
    :type password basestring
    :example password cljsl

    :param port: 端口号
    :type port int
    :example port 22

    :param conn_timeout:　超时时间
    :type conn_timeout int
    :example conn_timeout 10

    :param key_filename: 登录密钥路径
    :type key_filename basestring
    :example key_filename /root/.ssh/id_rsa

    :rtype ssh paramiko.SSHClient
    :return: ssh ssh连接对象
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host,
                    username=username,
                    password=password,
                    key_filename=key_filename,
                    port=port,
                    timeout=conn_timeout)
        return ssh
    except socket.timeout:
        msg = "连接超时(%s@%s:%s)." % (username, host, port)
        msg = "%s请检查用户名,IP地址,端口号是否正确" % msg
        raise SSHException(msg)
    except paramiko.ssh_exception.NoValidConnectionsError:
        msg = "连接出现异常(%s@%s:%s)." % (username, host, port)
        raise SSHException("%s请检查端口或IP地址是否正确" % msg)
    except paramiko.ssh_exception.AuthenticationException:
        msg = "连接出现异常(%s@%s:%s)." % (username, host, port)
        raise SSHException("%s请检查密码或密钥是否正确" % msg)
    except Exception as e:
        msg = "连接出现异常(%s@%s:%s) %s." % (username, host, port, e)
        raise SSHException(msg)


def generate_fio_script(lun):
    """生成fio压测脚本

    :param lun 磁盘路径
    :type lun basestring
    :example lun /dev/qdisk/P0B00S04

    :rtype fio_name basestring
    :return fio_name 文件名
    :example fio_name fio-P0B00S04.txt
    """
    content = """[global]
ioengine=libaio
iodepth=64
direct=1
runtime=60
time_based
refill_buffers
group_reporting=1

[rand-readwrite-fioa]
numjobs=16
rw=randrw
rwmixread=70
filename=%s
stonewall
bs=8k""" % lun
    fio_name = "fio-%s.txt" % os.path.basename(lun)
    with open(fio_name, "w+") as f:
        f.write(str(content))
    return fio_name


class RunCmdError(Exception):
    """执行命令异常
    """

    def __init__(self, message, out_msg, err_msg):
        """初始化参数

        :param message: 错误提示信息
        :param out_msg: 执行命令输出结果
        :param err_msg: 执行命令错误信息
        """
        super(RunCmdError, self).__init__(message)
        self.out_msg = out_msg
        self.err_msg = err_msg


class AnalogDiskFailure(object):
    """模拟磁盘故障
    """
    ACTIVE = "active"
    SLEEP_TIME = 600  # nvmf超时时间

    def __init__(self):
        self._curr_path = os.path.dirname(os.path.abspath(__file__))
        self._result_path = os.path.join(self._curr_path, str(self.SLEEP_TIME))
        self._api_mgr = "/usr/local/bin/api-seekplummgr"
        self._sto_lun = "/dev/qdisk/P0B00S07"  # 存储节点磁盘路径
        self._disk = os.path.basename(self._sto_lun)  # 磁盘名
        self._is_local = True
        self._port = 3261
        self._target_id = 1
        self._sto_id = 1
        self._ssh = None

    def run_cmd(self, cmd):
        """执行系统命令

        :param cmd 要执行的命令
        :type cmd basestring
        :example cmd ls -l /tmp
        """
        if self._is_local:
            logger.info("local cmd: %s" % cmd)
            p = subprocess.Popen(cmd,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)
            out_msg, err_msg = p.communicate()
            message = "执行本地命令: %s 失败，请确认该命令执行是否异常" % cmd
        else:
            logger.info("host: %s, cmd: %s" % (self._ssh.host, cmd))
            stdin, stdout, stderr = self._ssh.exec_command(cmd)
            stdin.close()
            stdout.flush()
            out_msg = stdout.read()
            err_msg = stderr.read()
            message = "在机器 %s 上执行 %s 命令失败，请确认该命令执行是否异常" % (self._ssh.host, cmd)
        logger.info("cmd result: %s" % out_msg)
        logger.info("cmd stderr: %s" % err_msg)
        if err_msg:
            raise RunCmdError(message, out_msg, err_msg)
        else:
            return out_msg

    @property
    def time(self):
        return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


class StorageAnalog(AnalogDiskFailure):
    """模拟磁盘故障

    以当前节点为计算节点，ssh要连接的节点为存储节点，模拟存储换盘load后测试是否可以读写
    """

    def __init__(self):
        super(StorageAnalog, self).__init__()
        self._ssh = get_ssh(host="10.10.100.10",
                            username="root",
                            password="password",
                            port=22)
        self._driver = "nvmf"  # qlink 协议
        self._is_local = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ssh.close()

    def detach_disk(self):
        """卸载磁盘
        """
        cmd = "%s media detach_disk -s %s -f" % (self._api_mgr, self._disk)
        self.run_cmd(cmd)

    def attach_disk(self):
        """挂载磁盘
        """
        cmd = "%s media attach_disk -s %s" % (self._api_mgr, self._disk)
        self.run_cmd(cmd)

    def del_lun(self):
        """从qlink中删除run
        """
        try:
            cmd = "%s qlink del_lun -p %s -t %s -b %s" % (self._api_mgr, self._port, self._target_id, self._sto_lun)
            self.run_cmd(cmd)
        except RunCmdError as e:
            # 第一次lun可能会不存在，忽悠删除失败
            logger.warning(e.message)

    def del_target(self):
        """从qlink中删除target
        """
        try:
            cmd = "%s qlink del_target -p %s -t %d" % (self._api_mgr, self._port, self._target_id)
            self.run_cmd(cmd)
        except RunCmdError as e:
            # 第一次target可能会不存在，忽悠删除失败
            logger.warning(e.message)

    def stop_port(self):
        """qlink停止
        """
        try:
            cmd = "%s qlink stop -p %s" % (self._api_mgr, self._port)
            self.run_cmd(cmd)
        except RunCmdError as e:
            # 第一次端口可能没有启动，忽悠删除失败
            logger.warning(e.message)

    def add_target(self):
        """在qlink中添加target
        """
        cmd = "%s qlink add_target -p %s" % (self._api_mgr, self._port)
        self.run_cmd(cmd)

    def start_port(self):
        """在qlink中启动端口
        """
        cmd = "%s qlink start -p %s -d %s" % (self._api_mgr, self._port, self._driver)
        self.run_cmd(cmd)

    def add_lun(self):
        """在qlink中添加run
        """
        cmd = "%s qlink add_lun -p %s -t %s -b %s" % (self._api_mgr, self._port, self._target_id, self._sto_lun)
        self.run_cmd(cmd)


class ComputeAnalog(AnalogDiskFailure):
    def __init__(self):
        super(ComputeAnalog, self).__init__()
        self._target_name = "s%02d.%s.%02d" % (self._sto_id, self._port, self._target_id)
        self._com_lun = "/dev/seekplum/mpath-%s.%s" % (self._target_name, self._disk)
        self._fio_path = generate_fio_script(self._com_lun)  # fio脚本路径

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self._fio_path):
            os.remove(self._fio_path)

    def fio(self):
        """fio压测
        """
        file_name = "fio-%s-%s.txt" % (self._disk, self.time)
        cmd = "fio %s > %s" % (self._fio_path, os.path.join(self._result_path, file_name))
        self.run_cmd(cmd)

    def check_target(self):
        """检查target是否正常

        :rtype bool
        """
        cmd = "%s qlink show -c" % self._api_mgr
        output = self.run_cmd(cmd)
        data = json.loads(output)
        for node in data:
            for qlink in node["qlink"]:
                # 找到指定端口
                if str(self._port) != qlink["port"]:
                    continue
                for target in qlink["targets"]:
                    # 找到指定target
                    if self._target_name != target["targetname"]:
                        continue
                    for lun_info in target["lun_list"]:
                        # 找到指定链路
                        if self._com_lun != lun_info["m_path"]:
                            continue
                        # 总链路状态
                        lun_status = [lun_info["m_status"]]

                        # 子链路状态
                        for sub_lun in lun_info["disks"]:
                            lun_status.append(sub_lun["status"])
                        # 所有lun的链路状态都正常
                        return all(map(lambda x: x == self.ACTIVE, lun_status))
        logger.info("lun: %s status is failed" % self._com_lun)
        return False

    def load_target(self):
        """加载taget
        """
        cmd = "%s qlink load -t %s" % (self._api_mgr, self._target_name)
        self.run_cmd(cmd)


def sto_option():
    """存储节点要做的操作
    """
    analog = StorageAnalog()
    sleep_time = analog.SLEEP_TIME + 10
    analog.detach_disk()

    # detach磁盘后等待，超过nvmf的超时时间
    logger.info("sleep time: %s" % sleep_time)
    time.sleep(sleep_time)

    analog.attach_disk()
    analog.del_lun()
    analog.add_lun()


def com_option():
    """计算节点要做的操作
    """
    analog = ComputeAnalog()
    # 链路不正常，先加载
    if not analog.check_target():
        analog.load_target()
    analog.fio()


def fatigue():
    """疲劳测试
    """
    while True:
        sto_option()
        com_option()
        time.sleep(5)


def test(args):
    """测试函数
    """
    analog = StorageAnalog()
    analog.detach_disk()
    # 等待时间
    sleep_time = int(args[0]) if len(args) > 0 else analog.SLEEP_TIME + 10
    time.sleep(sleep_time)
    analog.attach_disk()
    analog.del_lun()
    analog.add_lun()


def main():
    """主入口
    """
    if len(sys.argv) > 1:
        test(sys.argv[1:])
    else:
        if not os.path.exists(str(AnalogDiskFailure.SLEEP_TIME)):
            os.makedirs(str(AnalogDiskFailure.SLEEP_TIME))
        fatigue()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Exit")
