#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import os
import re
from threading import Thread

import requests
import subprocess

from urlparse import urljoin


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

    # 把输出打印到终端
    stdout_handle = logging.StreamHandler()
    stdout_handle.setFormatter(formatter)
    _logger.addHandler(stdout_handle)
    return _logger


logger = get_logger()


def run_cmd(cmd, force=False):
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


class Clone(object):
    def __init__(self, host, username, password):
        """gitlab帐号登录
        """
        self.username = username  # 邮箱用户名
        self.password = password  # 邮箱密码
        self.host = host
        self.base_url = "http://{}".format(self.host)
        self.req_session = requests.Session()

    def get_csrf_token(self):
        """查询token
        :return SOnhdNkmMbSXPoSeJw492b2I/o3vctKu4HyzzUy5toU=
        :rtype str
        <meta content="SOnhdNkmMbSXPoSeJw492b2I/o3vctKu4HyzzUy5toU=" name="csrf-token" />
        """
        url = urljoin(self.base_url, "users/sign_in")
        response = self.req_session.get(url=url)
        content = response.text
        pattern = re.compile(r'<meta content="(.+)" name="csrf\-token" />')
        match = pattern.search(content)
        if match:
            token = match.group(1)
            return token
        raise Exception("查询token失败")

    def login(self):
        """进行登录操作
        """
        url = urljoin(self.base_url, "users/sign_in")
        data = {
            "utf8": "",
            "authenticity_token": self.get_csrf_token(),
            "user[login]": self.username,
            "user[password]": self.password,
            "user[remember_me]": 0
        }
        response = self.req_session.post(url=url, data=data)
        status_code = response.status_code
        logger.info("status_code: %s" % status_code)

    def query_projects(self):
        """查询项目
        :return ["test/test", "test/test1"]
        :rtype list
        """
        url = urljoin(self.base_url, "dashboard/projects")
        response = self.req_session.get(url=url)
        content = response.text
        page_number = self.get_page(content)
        projects = self.get_project_info(content)
        for page in range(2, page_number + 1):
            url = urljoin(self.base_url, "dashboard/projects?page={}".format(page))
            response = self.req_session.get(url=url)
            result = self.get_project_info(response.text)
            projects.extend(result)
        return projects

    def get_page(self, content):
        """查询共有多少页
        :return 3
        :rtype int
        <a href="/dashboard/projects?page=3">3</a>
        """
        pattern = re.compile(r'<a href="/dashboard/projects\?page=\d+">(\d+)</a>')
        pages = pattern.findall(content)
        pages = [int(i) for i in pages]
        page = max(pages)
        return page

    def _clone_project(self, repository):
        """执行克隆操作

        克隆可以指定 `分支`， 最后几次commit id等，可以提高速度
        """
        cmd = "git clone {}".format(repository)
        logger.info("{}".format(cmd))

    def _download_projects(self, project, pattern, pattern_download, ):
        """执行下载操作

        注意： 下载操作只是把文件下载下来，仓库中的 .git  并不会下载

        <a href="/test/test/tree/release-1.0.0">Files</a>
        <a href="/test/test/repository/archive.tar.gz?ref=release-1.0.0">
        """
        url = urljoin(self.base_url, project)
        response = self.req_session.get(url=url)
        # pattern_download = re.compile('<a href="(.+(zip|tar\.gz|tar\.bz2|tar)\?.+)">')
        match = pattern.search(response.text)
        if match:
            # 找到默认的分支名
            href = match.group(1)
            url = urljoin(self.base_url, href)
            response = self.req_session.get(url=url)
            # 找到下载链接地址
            match = pattern_download.search(response.text)
            if match:
                url = match.group(1)
                download_url = urljoin(self.base_url, url)
                logger.info(download_url)
                return download_url
        return None

    def download_projects(self, projects, file_type="zip"):
        """下载项目
        """
        pattern = re.compile(r'<a href="(.+)">Files</a>')
        pattern_download = re.compile('<a href="(.+{}\?.+)">'.format(file_type))
        thread_list = []
        for project in projects:
            thread = Thread(target=self._download_projects, args=(project, pattern, pattern_download,))
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()

    def clone_projects(self, projects):
        """克隆项目
        """
        thread_list = []
        for project in projects:
            repository = self.get_git_url(project)
            thread = Thread(target=self._clone_project, args=(repository,))
            thread.start()
            thread_list.append(thread)
        for thread in thread_list:
            thread.join()

    def get_project_info(self, content):
        """查询项目信息

        <a class="project" href="/test/test">
        """
        pattern = re.compile(r'<a class="project" href="(.+)">')
        projects = pattern.findall(content)
        return projects

    def write_html(self, file_name, content):
        """把内容写入html
        """
        content = content.encode("utf-8") if isinstance(content, unicode) else content
        with open(file_name, "w") as f:
            f.write(content)

    def get_git_url(self, project):
        """组合git远程路径
        """
        repository = "git@{}:{}.git".format(self.host, project)
        return repository

    def do_clone(self):
        self.login()
        projects = self.query_projects()
        self.clone_projects(projects)
        self.download_projects(projects)


def main():
    username = ""
    password = ""
    host = ""
    manager = Clone(host, username, password)
    manager.do_clone()


if __name__ == '__main__':
    main()
