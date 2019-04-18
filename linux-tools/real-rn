#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#     FileName: rn.py
#         Desc: 上传文件到服务器
                命令: rn -s monitor -p seekplum -k
                描述: 上传rn_sync中指定项目的文件到ssh_config中配置的服务器,当增加了 -k 参数时,会每隔一秒同步一次
#       Author:
#        Email:
#     HomePage:
#      Version: 0.0.1
#   LastChange: 2016-02-24 09:37:42
#      History:
#=============================================================================
"""

import argparse
import re
import logging
import os
import sys
import time
import yaml
import paramiko

from copy import copy
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

formatter = '[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s'
datefmt = '%y%m%d %H:%M:%S'
logging.basicConfig(level=logging.INFO, format=formatter, datefmt=datefmt)

home = os.environ['HOME']


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_ssh(host, port, username, key=None, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if key:
        if isinstance(key, paramiko.rsakey.RSAKey):
            key = key
        else:
            pkfile = key
            key = paramiko.RSAKey.from_private_key_file(pkfile)
        ssh.connect(host,
                    port=port,
                    username=username,
                    pkey=key,
                    look_for_keys=False,
                    )
    elif password:
        ssh.connect(host,
                    port=port,
                    username=username,
                    password=password,
                    look_for_keys=False,
                    )
    else:
        msg = "Plearse Specify a password or private_key"
        raise Exception(msg)
    return ssh


class Sftp(object):
    def __init__(self, host, username, port, password, key):
        self.host = host
        self.username = username
        self.password = password
        self.key = key
        self.port = port
        self._sftp = None
        self._ssh = None
        self.local_root = None
        self.remote_root = None

    def set_root(self, local_root, remote_root):
        self.local_root = local_root
        self.remote_root = remote_root

    @property
    def ssh(self):
        if self._ssh:
            return self._ssh
        try:
            ssh = get_ssh(self.host, port=self.port, username=self.username, key=self.key, password=self.password)
            self._ssh = ssh
            return self._ssh
        except Exception as e:
            logging.exception("ssh connect failed, {}!".format(e))

    @property
    def sftp(self):
        if self._sftp:
            if self._sftp.sock.closed:
                self._sftp = None
                self._ssh = None
            else:
                return self._sftp
        while True:
            try:
                transport = self.ssh.get_transport()
                sftp = paramiko.SFTPClient.from_transport(transport)
                if not sftp.sock.closed:
                    self._sftp = sftp
                    return sftp
                else:
                    logging.error("ssh channel closed, try again...")
            except KeyboardInterrupt:
                sys.exit(1)
            except Exception as e:
                logging.exception("ssh channel closed, try again..., {}".format(e))

    def upload_folder(self, folder, preserver_perm=True):
        """
        folder: "a/b/c"
        """
        logging.info("upload folder: {}".format(folder))
        ex_folders = folder.split(os.sep)
        ok_folder = []
        for f in ex_folders:
            ok_folder.append(f)
            path = os.path.join(self.remote_root, *ok_folder)
            try:
                self.sftp.chdir(path)
            except IOError as e:
                l_folder = os.path.join(self.local_root, *ok_folder)
                mode = os.stat(l_folder).st_mode & 777 if preserver_perm else 0777
                self.sftp.mkdir(path, mode=mode)
            except Exception as e:
                logging.error("create folder {} failed".format(path))
                logging.exception(e)

    def upload_file(self, filename, preserver_perm=True):
        """
        filename: "a/b/c/d.py"
        """
        logging.info("upload file: {}".format(filename))
        remote_file = os.path.join(self.remote_root, filename)
        local_file = os.path.join(self.local_root, filename)

        try:
            self.sftp.put(local_file, remote_file)
        except IOError as e:
            self.upload_folder(os.path.dirname(filename), preserver_perm)
            self.sftp.put(local_file, remote_file)
        except Exception as e:
            logging.error("translate {} to {} failed".format(local_file, remote_file))
            logging.exception(e)

    def remove(self, path):
        logging.info("remove path: {}".format(path))

        def rm(path_):
            try:
                files = self.sftp.listdir(path=path_)
            except Exception as e_:
                logging.error("rm path failed! {}".format(e_.message))
                self.sftp.remove(path_)
                return

            for f in files:
                file_path_ = os.path.join(path_, f)
                if not os.path.isfile(file_path_):
                    rm(file_path_)
                else:
                    self.sftp.remove(file_path_)
            self.sftp.rmdir(path_)

        dest_path = os.path.join(self.remote_root, path)
        try:
            self.sftp.lstat(dest_path)
        except Exception as e:
            logging.warning(e.message)
        else:
            rm(dest_path)

    def rename(self, old_path, new_path):
        # TODO: 创建的是软连接
        root_old_path = os.path.join(self.local_root, old_path)
        root_new_path = os.path.join(self.local_root, new_path)
        is_link = os.path.islink(root_new_path)
        old_path = os.path.join(self.remote_root, old_path)
        new_path = os.path.join(self.remote_root, new_path)
        if not is_link:
            logging.info("rename path: {} ---> {}".format(old_path, new_path))
            self.ssh.exec_command("mv {} {}".format(old_path, new_path))
        else:
            logging.info("link path: {} ---> {}".format(old_path, new_path))
            self.ssh.exec_command("ln -s {} {}".format(old_path, new_path))


class MyHandler(PatternMatchingEventHandler):
    def __init__(self,
                 sftp,
                 local_root,
                 patterns=None,
                 ignore_patterns=None,
                 ignore_directories=False,
                 case_sensitive=False):
        super(self.__class__, self).__init__(patterns,
                                             ignore_patterns,
                                             ignore_directories,
                                             case_sensitive)
        self.local_root = local_root
        self.sftp = sftp

    def on_any_event(self, event):
        """
        event.event_type: 'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory: True | False
        event.src_path: path/to/observed/file
        event.dest_path: dest path if the event name is moved

        for each event, we alse can define a function to handler the event: `def on_{event_type}(event)`
        """
        logging.info("{}: {}".format(event.event_type, event.src_path))
        root_length = len(self.local_root) + 1
        src_path = event.src_path[root_length:]
        if event.event_type == "moved":
            dest_path = event.dest_path[root_length:]
            logging.info("{}: from {} to {}".format(event.event_type, src_path, dest_path))
            try:
                self.sftp.rename(src_path, dest_path)
            except Exception as e:
                logging.exception(e)
        elif event.event_type == "created":
            logging.info("{}: {}".format(event.event_type, src_path))
            try:
                if os.path.isfile(event.src_path):
                    self.sftp.upload_file(src_path)
                else:
                    self.sftp.upload_folder(src_path)
            except Exception as e:
                logging.exception(e)
        elif event.event_type == "deleted":
            logging.info("{}: {}".format(event.event_type, src_path))
            if not os.path.exists(event.src_path):
                try:
                    # todo: remote file exist?
                    self.sftp.remove(src_path)
                except Exception as e:
                    logging.exception(e)


def get_rsync(key, exclude=None, delete=False):
    if exclude is None:
        exclude = []
    option = ["rsync -rtv",
              "-e 'ssh -i {} "
              "-o \"UserKnownHostsFile=/dev/null\" "
              "-o \"StrictHostKeyChecking no\" "
              "-o \"ConnectTimeout=2\"'".format(key)]
    if delete:
        option.append(" --delete")
    exclude_file = [".git", "*.pyc"]
    exclude_file.extend(exclude)
    for file_name in set(exclude_file):
        option.append("--exclude {}".format(file_name))
    option_string = " ".join(option)
    return option_string


def translate(ip, src, dest, identityfile, user, exclude=None, delete=False):
    if exclude is None:
        exclude = []
    rsync = get_rsync(identityfile, exclude, delete)
    # pv = "|pv -lep -s 117 >/dev/null"
    pv = ""
    cmd = "{rsync} {src} {user}@{ip}:{dest}{pv}".format(
        rsync=rsync, src=src, user=user, ip=ip, dest=dest, pv=pv)
    cmd = cmd.replace("~", home)
    result = os.system(cmd)
    if result != 0:
        raise Exception(cmd)


def get_host_ip(hostname):
    """
    对传入的 ip 进行组合,获取完整的 ip
    :param hostname: 31: 返回10.10.10.20.31
    :return:
    """
    if re.search(r"^\d+$", hostname):  # 31
        host = "10.10.20.{}".format(hostname)
    elif re.search(r"^\d+\.\d+$", hostname):  # 90.31
        host = "10.10.{}".format(hostname)
    else:
        host = hostname
    return host


def get_all_rsync_conf():
    """
    读取yaml配置文件,本地文件路径,远程目录路径
    :return:
    """
    yaml_file = os.path.join(home, ".rsync.yaml")
    with open(yaml_file) as f:
        conf_str = f.read()
        rsync_conf = yaml.load(conf_str)
    return rsync_conf


def get_all_host_conf():
    """
    从config中读取 主机的信息, 包括用户名\密码等
    :return:
    """
    sections = []
    config_file = os.path.join(home, ".ssh/config")
    with open(config_file) as f:
        lines = f.readlines()
        section = []
        for line in lines:
            if line.startswith("Host"):
                if section:
                    sections.append(section)
                section = [line]
            elif line.strip():
                section.append(line)
        if section:
            sections.append(section)

    result = {}
    for section in sections:
        info = {}
        hostname = None
        for line in section:
            # 匹配指定字段开头的细心能
            if line.lower().strip().startswith("hostname"):
                info["ip"] = line.split()[-1]
            elif line.lower().strip().startswith("host "):
                hostname = line.split()[-1]
            elif line.lower().strip().startswith("user"):
                info["user"] = line.split()[-1]
            elif line.lower().strip().startswith("identityfile"):
                info["identityfile"] = line.split()[-1]
            elif line.lower().strip().startswith("port"):
                info["port"] = line.split()[-1]
        result[hostname] = info
    return result


def get_rn_conf(host, project):
    """
    在 ~/.ssh/config中查找主机
    :param host:
    :param project:
    :return:
    """
    all_host_conf = get_all_host_conf()
    all_rn_conf = get_all_rsync_conf()
    prj_conf = all_rn_conf.get("projects", {}).get(project)
    if not prj_conf:
        print "no project: {}".format(project)
        sys.exit(1)
    default_host_conf = all_rn_conf["default_host_conf"]
    host_conf = all_host_conf.get(host)
    if not host_conf:
        host_conf = copy(default_host_conf)
    if not host_conf.get("ip"):
        host_conf["ip"] = host
    host_conf.update(prj_conf)
    return host_conf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--servers",
                        required=True,
                        action="store",
                        dest="server",
                        help="specify server"
                        )
    parser.add_argument("-p", "--project",
                        required=False,
                        action="store",
                        dest="project",
                        default="default",
                        help="specify project",
                        )

    parser.add_argument("-k", "--keep",
                        default=False,
                        action="store_true",
                        dest="keep",
                        help="keep sync",
                        )

    args = parser.parse_args()
    host = args.server
    project = args.project
    keep = args.keep
    ip = get_host_ip(host)
    conf = get_rn_conf(ip, project)
    patterns = ["*"]
    ignore_patterns = conf.get("exclude", [])
    ignore_directories = False

    local_root = conf["src"]
    if local_root.endswith("/"):
        local_root = local_root[:-1]
    local_root = os.path.expanduser(local_root)

    remote_root = conf["dest"]
    if remote_root.endswith("/"):
        remote_root = remote_root[:-1]

    print("{}[    remote ip  ]{}: {}".format(bcolors.OKGREEN, bcolors.ENDC, conf["ip"]))
    print("{}[   local path  ]{}: {}".format(bcolors.OKGREEN, bcolors.ENDC, local_root))
    print("{}[  remote path  ]{}: {}".format(bcolors.OKGREEN, bcolors.ENDC, remote_root))

    try:
        translate(conf["ip"], conf["src"], conf["dest"], conf["identityfile"], conf["user"], conf["exclude"],
                  conf.get("delete", False))
    except Exception as e:
        print("{}[ ERROR ]{}: {}".format(bcolors.FAIL, bcolors.ENDC, e))
    else:
        print("{}[ ok ]{}: transfor finished".format(bcolors.OKGREEN, bcolors.ENDC))

    if not keep:
        return

    sftp = Sftp(
        host=conf["ip"],
        username=conf.get("user", "root"),
        port=conf.get("port", 22),
        password=conf.get("password", None),
        key=conf.get("identityfile", None),
    )
    sftp.set_root(local_root, remote_root)

    handler = MyHandler(
        sftp=sftp,
        local_root=local_root,
        patterns=patterns,
        ignore_patterns=ignore_patterns,
        ignore_directories=ignore_directories,
        case_sensitive=True,
    )
    observer = Observer()
    # handler = LoggingEventHandler()
    observer.schedule(handler,
                      path=local_root,
                      recursive=True,
                      )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
