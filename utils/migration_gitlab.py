#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import shutil
import subprocess
import uuid

from datetime import datetime
from multiprocessing import Process

color = lambda c, s: "\033[3%sm%s\033[0m" % (c, s)
red = lambda s: color(1, s)
green = lambda s: color(2, s)


def print_ok(check_status):
    fmt = green("[  OK  ]    %s" % check_status)
    print fmt


def print_error(check_status):
    fmt = red("[  ERROR  ]    %s" % check_status)
    print fmt


def get_logger(level=None):
    """设置日志格式,路径
    """
    if level is None:
        level = logging.INFO
    file_name = os.path.basename(__file__).rsplit(".", 1)[0]
    log_file_name = "%s.log" % file_name
    _logger = logging.getLogger(file_name)
    formatter = logging.Formatter('[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    log_file_handle = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=10 * 1024 * 1024, backupCount=10)
    log_file_handle.setFormatter(formatter)
    _logger.addHandler(log_file_handle)
    _logger.setLevel(level)
    return _logger


logger = get_logger()

temp_dir = "/tmp"  # 临时目录


def run_cmd(cmd, force=True):
    """执行系统命令

    :param cmd: str 系统命令
    :param force: bool 执行命令出错是否抛出异常

    :rtype str
    :return 执行 `cmd` 命令的输出结果
    """
    logger.info("cmd: %s" % cmd)
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    stdout, stderr = p.communicate()
    if stderr:
        logger.error("cmd stderr: %s" % stderr)
        if not force:
            raise Exception("cmd: %s, stderr: %s" % (cmd, stderr))
    else:
        logger.info("cmd result: %s" % stdout)
        return stdout


def md5sum(file_name):
    """计算文件的md5值

    :param file_name:  str 文件路径
    """
    cmd = "md5sum {}".format(file_name)
    file_md5 = run_cmd(cmd).split(" ")[0].strip()
    return file_md5


def get_time_str():
    """日期字符串

    :rtype str
    :return
    2017-01-05_10-45-00
    """
    _str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return _str


def update(group, project):
    """执行克隆重新推送到新仓库操作

    1. 执行克隆操作
    2. 重新推送到新的地址

    :param group: str 组名
    :param project: str 项目名
    """
    path = os.path.join(temp_dir, project, get_time_str())  # 克隆到本地的项目路径
    try:
        # 执行克隆操作
        cmd1 = "git clone --bare git@192.168.1.121:{group}/{project}.git {path}".format(project=project,
                                                                                        path=path,
                                                                                        group=group)
        run_cmd(cmd1)

        # 重新推送到新的地址
        cmd2 = "cd {path} && git push --mirror git@gitlab.woqutech.com:{group}/{project}.git".format(path=path,
                                                                                                     project=project,
                                                                                                     group=group)
        run_cmd(cmd2)
    except Exception as e:
        print_error(e.message)
    else:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=False)


def check(group, project):
    """检查log/branch/tag是否一致

    把 git log / git branch -a / git tag 三条命令的执行结果重定向到文件中.看文件md5值是否一致
    """
    check_cmd = [
        "git log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) "
        "%C(bold blue)<%an>%Creset' --abbrev-commit",
        "git branch -a",
        "git tag"
    ]
    hosts = [
    ]
    file_name = "{}_commit.txt".format(project)
    file_md5 = set()
    for host in hosts:
        path = os.path.join(temp_dir, "{}_{}_{}".format(project, host, get_time_str()))  # 克隆到本地的项目路径
        md5 = uuid.uuid4().hex
        try:
            cmd1 = "git clone git@{host}:{group}/{project}.git {path}".format(project=project,
                                                                              path=path,
                                                                              host=host,
                                                                              group=group
                                                                              )
            run_cmd(cmd1)

            file_path = os.path.join(path, file_name)
            # 把检查命令的结果重定向到文件中
            for cmd in check_cmd:
                cmd2 = "cd {} && {} >> {}".format(path, cmd, file_path)
                run_cmd(cmd2)

        except Exception as e:
            print_error(e.message)
        else:
            md5 = md5sum(file_path)
        finally:
            file_md5.add(md5)
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=False)

    # 在后面打印的 . 数
    count = 80 - (len(group) + len(project))
    count = count if count > 0 else 0
    text = count * "."

    # 对比两个文件的md5值是否一致
    if len(file_md5) == 1:
        print_ok("{}/{} {}".format(group, project, text))
    else:
        print_error("{}/{} {}".format(group, project, text))


def run(group, project):
    """执行克隆重新推送到新仓库操作

    :param group: str 组名
    :param project: str 项目名
    """
    # update(group, project)
    check(group, project)


def main():
    projects = [
        {
            "group": "",
            "projects": [

            ]
        }
    ]
    process_list = []
    for info in projects:
        projects = info["projects"]  # 项目名
        group = info["group"]  # 组名
        for project in projects:
            process = Process(target=run, args=(group, project,))
            process.start()
            process_list.append(process)
    for process in process_list:
        process.join()


if __name__ == '__main__':
    main()
