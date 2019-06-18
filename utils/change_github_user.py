# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import tempfile

from datetime import datetime
from textwrap import dedent
from contextlib import contextmanager
from itertools import chain


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


class RunCmdTimeout(Exception):
    """执行系统命令超时
    """
    pass


def run_cmd(cmd, is_raise_exception=True, timeout=None):
    """执行系统命令

    :param cmd 系统命令
    :type cmd str
    :example cmd hostname

    :param is_raise_exception 执行命令失败是否抛出异常
    :type is_raise_exception bool
    :example is_raise_exception False

    :param timeout 超时时间
    :type timeout int
    :example timeout 1

    :rtype str
    :return 命令执行结果
    :example hostname

    :raise RunCmdError 命令执行失败
    :raise RunCmdTimeout 命令执行超时
    """

    def raise_timeout_exception(*_):
        """通过抛出异常达到超时效果
        """
        raise RunCmdTimeout("run `%s` timeout, timeout is %s" % (cmd, timeout))

    # 设置指定时间后出发handler
    if timeout:
        signal.signal(signal.SIGALRM, raise_timeout_exception)
        signal.alarm(timeout)

    p = subprocess.Popen(cmd, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_msg = p.stdout.read()
    err_msg = p.stderr.read()
    exit_code = p.wait()

    # 解除触发handler
    if timeout:
        signal.alarm(0)

    if is_raise_exception and exit_code != 0:
        message = "run `%s` fail" % cmd
        raise RunCmdError(message, out_msg=out_msg, err_msg=err_msg)
    return out_msg


@contextmanager
def make_temp_file(suffix="", prefix="plum_tools_", clean=True, dir_=None):
    """
    创建临时文件
    clean: True 在with语句之后删除文件夹
    """
    temp_file = tempfile.mktemp(suffix=suffix, prefix=prefix, dir=dir_)
    try:
        yield temp_file
    finally:
        if clean and os.path.isfile(temp_file):
            os.remove(temp_file)


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


def backup_directory(path):
    if os.path.exists(path):
        os.renames(path, "%s.bak.%s" % (path, datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))


class ChangeUser(object):
    def __init__(self, github_user, github_base, old_email, correct_name, correct_email, temp_root="/tmp"):
        self._github_user = github_user
        self._github_base = github_base
        self._old_email = old_email
        self._correct_name = correct_name
        self._correct_email = correct_email
        self._temp_root = temp_root

    def _clone(self, repo_name):
        cmd = "git clone --bare %s:%s/%s" % (self._github_base, self._github_user, repo_name)
        run_cmd(cmd)

    @contextmanager
    def _get_tem_script(self, dir_):
        context = dedent("""\
                #!/bin/sh

                git filter-branch --env-filter '

                OLD_EMAIL="%s"
                CORRECT_NAME="%s"
                CORRECT_EMAIL="%s"

                if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
                then
                    export GIT_COMMITTER_NAME="$CORRECT_NAME"
                    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
                fi
                if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
                then
                    export GIT_AUTHOR_NAME="$CORRECT_NAME"
                    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
                fi
                ' --tag-name-filter cat -- --branches --tags
                """ % (self._old_email, self._correct_name, self._correct_email))
        with make_temp_file(prefix="change_github_user", suffix=".sh", dir_=dir_, clean=False) as tmp_file:
            with open(tmp_file, "w+") as f:
                f.write(context)
            yield tmp_file

    def _change_user_and_email(self, repo_path):
        with self._get_tem_script(repo_path) as script:
            run_cmd("bash %s" % script)

    @staticmethod
    def _push_force():
        cmd = "git push --force --tags origin 'refs/heads/*'"
        run_cmd(cmd)

    def change(self, repo_name):
        repo_path = os.path.join(self._temp_root, repo_name)
        with cd(self._temp_root):
            backup_directory(repo_path)
            self._clone(repo_name)
            with cd(repo_path):
                self._change_user_and_email(repo_path)
                self._push_force()


def main():
    github_user = "seekplum"
    github_base = "git@github.com"
    correct_name = "seekplum"
    correct_email = "1131909224@qq.com"
    temp_root = "/tmp/change-user"
    old_emails = []
    for old_email in old_emails:
        c = ChangeUser(github_user, github_base, old_email, correct_name, correct_email, temp_root)
        projects_path = [
        ]
        repos = [os.listdir(project_path) for project_path in projects_path]
        repos = list(chain(*repos))

        new_repos = [repo_name for repo_name in repos if repo_name.startswith(".git")] + \
                    map(lambda x: x + ".git", [repo_name for repo_name in repos if not repo_name.startswith(".git")])
        for repo_name in set(new_repos):
            c.change(repo_name)


if __name__ == '__main__':
    main()
