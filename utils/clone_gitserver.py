#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import re
import subprocess

from threading import Lock

import requests

from urlparse import urljoin
from concurrent.futures import ThreadPoolExecutor


def get_logger(level=None):
    """设置日志格式,路径
    """
    if level is None:
        level = logging.INFO
    file_name = os.path.basename(__file__).rsplit(".", 1)[0]
    _logger = logging.getLogger(file_name)
    _logger.setLevel(level)
    formatter = logging.Formatter(
        '[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # log_file_name = "%s.log" % file_name
    # log_file_handle = logging.handlers.RotatingFileHandler(
    #     log_file_name, maxBytes=10 * 1024 * 1024, backupCount=10)
    # log_file_handle.setFormatter(formatter)
    # _logger.addHandler(log_file_handle)

    # 把输出打印到终端
    stdout_handle = logging.StreamHandler()
    stdout_handle.setFormatter(formatter)
    _logger.addHandler(stdout_handle)
    return _logger


logger = get_logger()


class cd(object):
    """进入目录执行对应操作后回到目录
    """

    def __init__(self, new_path):
        """初始化

        :param new_path: 目标目录
        :type new_path str
        :example new_path "/tmp"
        """
        self._new_path = new_path
        self._current_path = None

    def __enter__(self):
        self._current_path = os.getcwd()
        os.chdir(self._new_path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._current_path)


class Clone(object):
    def __init__(self, host, username, password, target_dir):
        """初始化
        """
        self._username = username  # 邮箱用户名
        self._password = password  # 邮箱密码
        self._host = host
        self._base_url = "https://{}".format(self._host)
        self._target_dir = target_dir
        self._req_session = requests.Session()

    def _get_csrf_token(self):
        """查询token

        :return token
        :rtype str
        """
        url = urljoin(self._base_url, "user/login")
        response = self._req_session.get(url=url)
        content = response.text
        pattern = re.compile(r'<meta name="_csrf" content="(.+)" />')
        match = pattern.search(content)
        if match:
            token = match.group(1)
            return token
        raise Exception("查询token失败")

    def _login(self):
        """进行登录操作
        """
        url = urljoin(self._base_url, "user/login")
        data = {
            "_csrf": self._get_csrf_token(),
            "user_name": self._username,
            "password": self._password
        }
        response = self._req_session.post(url=url, data=data)
        status_code = response.status_code
        logger.info("status_code: %s" % status_code)

    def _query_for_user(self):
        """查询所有的用户

        :rtype list
        """
        url = urljoin(self._base_url, "explore/users")
        pattern = re.compile(r'<span class="header"><a href="/.*">(.*)</a>')
        response = self._req_session.get(url=url)
        content = response.text
        return pattern.findall(content)

    def _query_for_organization(self):
        """查询所有的组织

        :rtype list
        """
        url = urljoin(self._base_url, "explore/organizations")
        pattern = re.compile(
            r'<span class="header">\n\s+<a href="/.*">(.*)</a> ', re.MULTILINE)
        response = self._req_session.get(url=url)
        content = response.text
        return pattern.findall(content)

    def query_target_project(self, target):
        url = urljoin(self._base_url, target)
        response = self._req_session.get(url=url)
        content = response.text
        page_number = self._get_target_page(content)
        projects = self._get_current_page_project_name(target, content)
        for page in range(2, page_number + 1):
            url = urljoin(self._base_url,
                          "{}?page=2&sort=recentupdate&q=&tab=".format(target,
                                                                       page))
            response = self._req_session.get(url=url)
            result = self._get_current_page_project_name(target, response.text)
            projects.extend(result)
        return projects

    def query_projects(self):
        """查询项目

        :return ["test/test", "test/test1"]
        :rtype list
        """
        targets = self._query_for_user()
        targets.extend(self._query_for_organization())
        projects = []
        for target in targets:
            result = self.query_target_project(target)
            projects.extend(map(lambda x: "{}/{}".format(target, x), result))
        return projects

    @staticmethod
    def _get_target_page(content):
        """查询共有多少页

        :return 3
        :rtype int
        """
        pattern = re.compile(r'<a class=" item" href="/.+\?page=(\d+)&'
                             r'sort=recentupdate&amp;q=&amp;tab=">\d+</a>')
        pages = pattern.findall(content)
        pages = [int(i) for i in pages]
        page = max(pages) if pages else 1
        return page

    def _clone_project(self, lock, project):
        """执行克隆操作

        克隆可以指定 `分支`， 最后几次commit id等，可以提高速度
        """
        repository = self._get_git_url(project)
        target_dir = os.path.join(self._target_dir, project)
        if os.path.exists(target_dir):
            cmd = (
                'if [ `git branch -a | grep "origin/master" | wc -l` == 0 ]; '
                'then '
                'branch="origin/`git rev-parse --abbrev-ref HEAD`"; '
                'else '
                'branch="origin/master"; fi; '
                'if [ $? != 0 ]; '
                'then echo "\033[33m`pwd` get branch failed \033[0m";'
                'else '
                'if [ `git status -s | wc -l` == 0 ]; '
                'then git branch --set-upstream-to="$branch" >/dev/null 2>&1; '
                'git pull --rebase >/dev/null 2>&1; '
                'else echo "\033[33m`pwd` has been modified \033[0m"; fi;'
                'if [ $? != 0 ]; '
                'then echo "\033[33m`pwd` pull failed \033[0m"; fi;'
                'fi;'
            )
            with cd(target_dir):
                # logger.info("cmd: %s" % cmd)
                subprocess.call(cmd, shell=True)
                return

        # 避免目录重复创建
        with lock:
            parent_dir = os.path.dirname(target_dir)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)

        cmd = "git clone {} {}".format(repository, target_dir)
        # logger.info("cmd: %s" % cmd)
        subprocess.call(cmd, shell=True)

    def clone_projects(self, projects):
        """克隆项目

        :param projects 项目列表
        :type projects list
        :example projects ["test/test", "test/test1"]
        """
        lock = Lock()
        thread_pool = ThreadPoolExecutor(max_workers=5)
        futures = [thread_pool.submit(self._clone_project, lock, project) for
                   project in projects]
        map(lambda future: future.result(), futures)

    @staticmethod
    def _get_current_page_project_name(target, content):
        """查询项目信息
        """
        pattern = re.compile(r'<a class="name" href="/{}/.*">\n\s+'
                             r'(.*)\n\s+</a>'.format(target), re.MULTILINE)
        projects = pattern.findall(content)
        return projects

    def _get_git_url(self, project):
        """组合git远程路径
        """
        repository = "git@{}:{}.git".format(self._host, project)
        return repository

    def do_clone(self):
        self._login()
        projects = self.query_projects()
        self.clone_projects(projects)


def main():
    username = ""
    password = ""
    host = ""
    target_dir = ""
    manager = Clone(host, username, password, target_dir)
    manager.do_clone()


if __name__ == '__main__':
    main()
