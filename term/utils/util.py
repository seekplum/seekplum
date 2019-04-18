#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import socket
import select
import conf
import re
import os
import json
import socket
from utils import texttable
import paramiko
import fcntl
import termios
import struct
import netifaces
import copy
import time
import stat
import glob
from pexpect import pxssh
from operator import itemgetter
from itertools import groupby
from utils.log import info_logger, error_logger
from conf import UNKNOWN_TYPE, SSH_CONF, Seekplum_DB_FILE


def layer_dict(dict_list, keyword_list):
    """
    The function is used for change the dimension,for example:
    dict_list = [
                {
                    'name': u'sto1.qlink3261.01',
                    'acl_address': u'172.16.128.0/24, 172.16.129.0/24',
                    'server': u'sto1',
                    'device_type': u'disk',
                    'port': 3261,
                    'lun': u'/dev/VolGroup/redo'
                },
                ....
            ]
    keyword_list: ["server", "port"]
    return: { u'sto1': {
                    3261: [ {...}, {...}],
                    3262: [{...}, {...}], },
              u'sto2': {...}
            }
    """
    result = {}
    local_list = copy.deepcopy(dict_list)
    if len(keyword_list) == 1:
        keyword = keyword_list[0]
        local_list.sort(key=itemgetter(keyword))
        for value, items in groupby(local_list, key=itemgetter(keyword)):
            sub_list = []
            for item in items:
                item.pop(keyword)
                sub_list.append(item)
            result[value] = sub_list
        return result
    else:
        keyword = keyword_list[0]
        keyword_list = keyword_list[1:]
        local_list.sort(key=itemgetter(keyword))
        for value, items in groupby(local_list, key=itemgetter(keyword)):
            sub_list = []
            for item in items:
                item.pop(keyword)
                sub_list.append(item)
            result[value] = layer_dict(sub_list, keyword_list)
    return result


def list_to_jsonstr(List):
    """
    List = [[head1, head2, ..], [args1, args2, ..]]
    return: [{head1: args1, head2: args2},
    """
    result = []
    head = List[0]
    if len(List) < 2:
        return json.dumps(result)
    for L in List[1:]:
        temp_dict = {}
        for i, value in enumerate(L):
            temp_dict[head[i]] = value.strip().replace("\n", " ") if isinstance(value, str) else value
        result.append(temp_dict)
    return json.dumps(result)


def run(cmd, filter_=False, ssh=None):
    """
    run a command
    """
    info_logger.info("cmd: " + str(cmd))
    result = {}
    out_msg = ''
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

        if filter_:
            out_list = out_msg.splitlines()
            if "Exit Code" in out_list[-1]:
                out_msg = "\n".join(out_list[:-1])
        result["stdout"] = out_msg
        result["stderr"] = err_msg
        result["exit_code"] = exit_code
        info_logger.info("cmd output:\n" + out_msg)
        if err_msg:
            info_logger.exception("cmd error msg:\n" + err_msg)
        return result
    except Exception as e:
        info_logger.exception("exception at run {}".format(cmd))
        error_logger.exception("exception at run {}".format(cmd))
        result["stdout"] = ""
        result["stderr"] = e
        result["exit_code"] = 1
        return result


class RunCMDError(Exception):
    """raise when run cmd error"""
    pass


def run_cmd(cmd, filter_=False, ssh=None):
    result = run(cmd=cmd, filter_=filter_, ssh=ssh)
    if result["exit_code"] != 0:
        # info_logger.error("run cmd '{}' return code: {}".format(cmd, result["exit_code"]))
        # error_logger.error("run cmd '{}' return code: {}".format(cmd, result["exit_code"]))
        msg = result["stderr"].strip() if result["stderr"] else result["stdout"].strip()
        raise RunCMDError(msg)
    else:
        return result["stdout"]


def run_remotecmd(cmd, ssh, printout=True, skip=0):
    EOF = "EOFCMD_WOQUCMD"
    channel = ssh.invoke_shell(width=200)
    timeout = 60  # timeout is in seconds
    channel.settimeout(timeout)
    newline = '\n'
    full_cmd = "{}; echo {};exit {}".format(cmd, EOF, newline)
    channel.send(full_cmd)
    print_flag = False
    line_buffer = ""
    result = []
    line_num = 0
    print_flag = 0
    while True:
        rl, wl, xl = select.select([channel], [], [], 180)
        # 当心这里，有时循环不退出，cpu会飙高
        if not channel.recv_ready() and channel.closed:
            break
        try:
            channel_buffer = channel.recv(1).decode('UTF-8')
            channel_buffer = channel_buffer.replace('\r', '')
        except socket.timeout:
            break
        if channel_buffer != '\n':
            line_buffer += channel_buffer
        else:
            # print line_buffer
            if print_flag == 2 and line_buffer:
                if EOF in line_buffer:
                    break
                if printout:
                    if line_num >= skip:
                        print line_buffer
                result.append(line_buffer)
                line_num += 1
            elif len(line_buffer) > 1 and full_cmd.strip().replace(" ", "") in str(line_buffer).replace(" ", ""):
                print_flag += 1
            line_buffer = ""
    return "\n".join(result)


def get_ssh(hostname, port=22, conn_timeout=None, username=None, password=None, key_filename=None, ):
    if not username:
        username = conf.SSH_CONF["username"]
    if not key_filename:
        key_filename = conf.SSH_CONF["key_filename"]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port, timeout=conn_timeout, username=username, key_filename=key_filename,
                password=password)
    return ssh


def get_ssh_config(hostname):
    ssh_config = copy.copy(SSH_CONF)
    ssh_config.update({"hostname": hostname})
    return ssh_config


def get_pexssh(hostname, port=22, conn_timeout=None, username=None, password="", key_filename=None):
    s = pxssh.pxssh()
    login = s.login(server=hostname, username=username, port=port, login_timeout=conn_timeout, password=password,
                    ssh_key=key_filename)
    if login:
        return s
    else:
        return


def add_error(error_msg, error):
    if error_msg:
        error_msg += "\n" + error
    else:
        error_msg = error
    return error_msg


def get_hostname():
    """get the host name"""
    return socket.gethostname()


def get_ip_list():
    '''
    Using netifaces to fetch the ip address of the current machine.
    '''
    ip_list = []
    pattern_iface = re.compile("^ib\d$")
    interfaces = netifaces.interfaces()
    for iface in interfaces:
        if pattern_iface.match(iface):
            if netifaces.AF_INET in netifaces.ifaddresses(iface):
                addrs = netifaces.ifaddresses(iface)[netifaces.AF_INET]  # mac addr: netifaces.AF_LINK
                for addr in addrs:
                    ip_list.append(addr['addr'])
    return ip_list


def get_project_path():
    """get the project path"""
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return project_path


def get_config_db_file():
    return os.path.join(get_project_path(), Seekplum_DB_FILE)


def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


def Hex(hex_string):
    """
    format the hex number, input a hex string such as
    0x00a76, 00a76, a76, reuturn 0xa76
    """
    if not hex_string:
        return ""
    else:
        if hex_string.endswith(("L", "l")):
            return hex(int(hex_string[:-1], 16))
        else:
            return hex(int(hex_string, 16))


def get_terminal_width():
    h, w, hp, wp = struct.unpack('HHHH',
                                 fcntl.ioctl(0, termios.TIOCGWINSZ,
                                             struct.pack('HHHH', 0, 0, 0, 0)))
    return w


def int2hex(s):
    # s = int(s)
    # return hex(s)[2:]
    return str(s)


def show(lists, net=False, shift=0, header=True, sort=True):
    """show in table format"""
    max_width = int(get_terminal_width())
    table = texttable.Texttable(max_width=max_width)
    table_width = len(lists[0])
    table.set_cols_align(["l"] * table_width)
    table.set_cols_valign(["m"] * table_width)
    if len(lists) > 1 and sort:
        lists[1:] = sorted(lists[1:], key=lambda l: l[0])
    if not net:
        table.set_deco(texttable.Texttable.HEADER)
    table.add_rows(lists, header)

    table_line = table.draw()
    if shift == 0:
        print(table_line)
    elif shift > 0:
        result = []
        for line in table_line.splitlines():
            result.append(" " * shift + line)

        print("\n".join(result))


def format_word(word):
    """used for sql word"""
    if isinstance(word, (int, float)):
        return word
    elif isinstance(word, (str, unicode)):
        if "'" in word:
            return '"{}"'.format(word)
        else:
            return "'{}'".format(word)
    else:
        return word


def get_kwargs(arguments):
    """used for arguparser."""
    kwargs = {}
    kw_set = arguments._get_kwargs()
    for key, value in kw_set:
        if key != "func":
            if isinstance(value, unicode):
                value = str(value)
            kwargs[key] = value
    return kwargs


def enter_shell(cmd=""):
    """
    使用前先确定ssh服务是否正常
    安装: sudo apt-get install openssh-server
    状态: service ssh status
    :param cmd:
    :return:
    """
    KEY = SSH_CONF["key_filename"]
    USER = SSH_CONF["username"]
    ip = "127.0.0.1"
    cmd = 'ssh -t -i {} -q -o "UserKnownHostsFile=/dev/null" -o "StrictHostKeyChecking no" -o  "ConnectTimeout=2" {}@{} {}'.format(KEY, USER, ip, cmd)
    os.system(cmd)


def time_now():
    return int(time.time())


def stringit(input):
    if isinstance(input, dict):
        return {stringit(key): stringit(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [stringit(element) for element in input]
    elif isinstance(input, unicode):
        return str(input)
    else:
        return input


