#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import subprocess

from threading import Lock
from textwrap import dedent

import requests

from urllib.parse import urljoin
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
    def __init__(self, host, token, target_dir):
        """初始化
        """
        self._token = token
        self._host = host
        self._base_url = "https://{}/api/v1/".format(self._host)
        self._target_dir = target_dir
        self._req_session = requests.Session()
        self._is_running = True
        self.fork_projects = []

    def _request(self, url, **kwargs):
        headers = {"Authorization": f"token {self._token}", "Content-Type": "application/json"}
        response = self._req_session.get(urljoin(self._base_url, url), headers=headers, timeout=3, **kwargs)
        if response.status_code != 200:
            raise Exception(f"接口响应错误, {response.text}")
        return response.json()

    def _query_for_user(self):
        """查询所有的用户

        :rtype list
        """
        params = {
            "page": 1,
            "limit": 1000,
        }
        data = self._request("users/search", params=params)
        usernames = [user["username"] for user in data["data"]]
        projects = []
        for username in usernames:
            resp_data = self._request(f"users/{username}/repos", params=params)
            self.fork_projects.extend([p["full_name"] for p in resp_data if p["fork"]])
            projects.extend([p["full_name"] for p in resp_data if not p["fork"]])
        return sorted(set(projects))

    def _query_for_organization(self):
        """查询所有的组织

        :rtype list
        """
        params = {
            "page": 1,
            "limit": 1000,
        }
        data = self._request("orgs", params=params)
        org_names = [org["username"] for org in data]
        projects = []
        for org in org_names:
            projects.extend([
                project["full_name"]
                for project in self._request(f"orgs/{org}/repos", params=params)
            ])
        return sorted(set(projects))

    def query_projects(self):
        """查询项目

        :return ["test/test", "test/test1"]
        :rtype list
        """
        user_projects = self._query_for_user()
        org_projects = self._query_for_organization()
        return sorted(set(user_projects + org_projects))

    def _clone_project(self, lock, project):
        """执行克隆操作

        克隆可以指定 `分支`， 最后几次commit id等，可以提高速度
        """
        if not self._is_running:
            return
        repository = self._get_git_url(project)
        target_dir = os.path.join(self._target_dir, project)
        if os.path.exists(target_dir):
            cmd = dedent("""\
                if [ `git rev-list -n 1 --all | wc -l` != 0 ]; then
                    if [ `git status -s | wc -l` == 0 ]; then
                        remote=`git remote | tail -n 1`
                        branch=`git rev-parse --abbrev-ref HEAD`
                        git fetch ${remote} && git pull ${remote} ${branch} --rebase >/dev/null 2>&1;
                        if [ $? != 0 ]; then
                            echo "\033[31m`pwd` pull failed \033[0m";
                        else
                            echo "\033[32m`pwd` pull success \033[0m";
                        fi;
                    else
                        echo "\033[33m`pwd` has been modified \033[0m";
                    fi;
                else
                    echo "\033[33m`pwd` is an empty repository \033[0m";
                fi;
                """)
            with cd(target_dir):
                # logger.info("director: {}".format(target_dir))
                try:
                    # logger.info("cmd: %s" % cmd)
                    subprocess.check_call(cmd, shell=True)
                except subprocess.CalledProcessError:
                    self._is_running = False
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

    def _get_git_url(self, project):
        """组合git远程路径
        """
        repository = "git@{}:{}.git".format(self._host, project)
        return repository

    def do_clone(self):
        projects = self.query_projects()
        print("-" * 100)
        print("\n".join(self.fork_projects))
        print("-" * 100)
        self.clone_projects(projects)


def main():
    token = ""
    host = ""
    target_dir = ""
    manager = Clone(host, token, target_dir)
    manager.do_clone()


if __name__ == '__main__':
    main()
