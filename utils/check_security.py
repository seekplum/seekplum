#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#=============================================================================
#     FileName: check_security.py
#         Desc: 根据安全规则调整系统参数
#                命令: `python check_security.py`
#                描述: 根据绿盟软件评分规则,调整系统参数
#                        1. 备份
#                            1. 备份整个etc目录
#                            2. 备份每个独立的文件
#
#                        2. 依次修改文件
#
#                    若修改后有问题,可以进行回退 `python check_security.py -b`
#                        1. 把修改的备份到 /tmp 目录下
#                        2. 把之前备份的文件恢复到相应目录
#       Author:
#        Email:
#     HomePage:
#      Version: 0.0.1
#   LastChange: 2018-03-02
#      History:
#=============================================================================
"""
import getopt
import logging
import logging.handlers
import os
import socket
import subprocess
import sys

from datetime import datetime

# ========================= commands =========================
XINETD_COMMAND = "/etc/init.d/xinetd restart"
SSHD_COMMAND = "/etc/init.d/sshd restart"

NEWALIASES_COMMAND = "/usr/bin/newaliases"

# ========================= file path =========================
ETC_LOGIN_DEFS = "/etc/login.defs"
ETC_PAMD_SYSTEM_AUTH = "/etc/pam.d/system-auth"
ETC_PROFILE = "/etc/profile"
ETC_LILI_CONF = "/etc/lilo.conf"
ETC_SECURITY_LIMITS_CONF = "/etc/security/limits.conf"
ETC_HOSTS_DENY = "/etc/hosts.deny"
ETC_ALIASES = "/etc/aliases"
ETC_MAIL_ALIASES = "/etc/mail/aliases"  # 文件不存在
ETC_CSH_CSHRS = "/etc/csh.cshrc"
ETC_CSH_LOGIN = "/etc/csh.login"
ETC_BASHRC = "/etc/bashrc"
ETC_SSH_SSHD_CONFIG = "/etc/ssh/sshd_config"
ETC_PAMD_LOGIN = "/etc/pam.d/login"
ETC_PAMD_SU = "/etc/pam.d/su"
ETC_SHADOW = "/etc/shadow"
ETC_PASSWD = "/etc/passwd"
ETC_PAMD_SSHD = "/etc/pam.d/sshd"
ETC_HOST_CONF = "/etc/host.conf"
ETC_HOSTS_ALLOW = "/etc/hosts.allow"
ETC_GROUP = "/etc/group"
ETC_GSHADOW = "/etc/gshadow"
ETC_SNMP_CONF = "/etc/snmp/snmpd.conf"

USR_BIN_CHAGE = "/usr/bin/chage"
USER_BIN_GPASSWD = "/usr/bin/gpasswd"
USER_BIN_WALL = "/usr/bin/wall"
USER_BIN_CHFN = "/usr/bin/chfn"
USER_BIN_CHSH = "/usr/bin/chsh"
USER_BIN_NEWGRP = "/usr/bin/newgrp"
USER_BIN_WRITE = "/usr/bin/write"
USER_BIN_USERNETCTL = "/usr/sbin/usernetctl"
USER_BIN_TRACEROUTE = "/usr/sbin/traceroute"  # 文件不存在
BIN_MOUNT = "/bin/mount"
BIN_UMOUNT = "/bin/umount"
BIN_PING = "/bin/ping"
SBIN_NETREPPORT = "/sbin/netreport"

BOOT_GRUB_MENU_LST = "/boot/grub/menu.lst"

PROC_SYS_NET_SEND = "/proc/sys/net/ipv4/conf/all/send_redirects"
PROC_SYS_NET_ACCEPT = "/proc/sys/net/ipv4/conf/all/accept_redirects"

VAR_LOG_PACCT = "/var/log/pacct"
ETC_SSH_BANNER = "/etc/ssh_banner"

# ========================= 需要备份的文件 =========================
BACKUP_PATH = [
    "/etc",
    BOOT_GRUB_MENU_LST,
    PROC_SYS_NET_SEND,
    PROC_SYS_NET_ACCEPT,

    USR_BIN_CHAGE,
    USER_BIN_GPASSWD,
    USER_BIN_WALL,
    USER_BIN_CHFN,
    USER_BIN_CHSH,
    USER_BIN_NEWGRP,
    USER_BIN_WRITE,
    USER_BIN_USERNETCTL,
    # USER_BIN_TRACEROUTE,
    BIN_MOUNT,
    BIN_UMOUNT,
    # BIN_PING,
    SBIN_NETREPPORT
]
# ========================= 回退后需要操作的命令 =========================
BACK_COMMANDS = [
    XINETD_COMMAND,
    NEWALIASES_COMMAND,
    SSHD_COMMAND
]

SHADOW_ASSWORD = [
    ETC_PASSWD,
    ETC_SHADOW,
    ETC_GROUP,
    ETC_GSHADOW
]
# ========================= 需要删除的文件 =========================
DELETE_PATH = [
    VAR_LOG_PACCT,
    ETC_SSH_BANNER
]

# ========================= config =========================
CHK_ROOT_KIT = "chkrootkit-0.49-9.el6.x86_64.rpm"
GRUB_PASSWORD = "password"  # grub 密码
LILO_PASSWORD = "password"  # lilo 密码
TEMP_FOLDER = "/tmp"  # 修改后文件备份路径
BACKUP_FOLDER = "/root"  # 源文件备份路径
LOG_PATH = "/tmp/update_security.log"  # 日志路径


def get_logger(level):
    """设置日志格式,路径
    """
    logger_ = logging.getLogger("check_security")
    file_formatter = logging.Formatter('[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                                       datefmt='%Y-%m-%d %H:%M:%S')
    # 只保留一份日志,最大20M
    log_file_handle = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=20 * 1024 * 1024, backupCount=1)
    log_file_handle.setFormatter(file_formatter)
    logger_.addHandler(log_file_handle)

    logger_.setLevel(level)
    return logger_


logger = get_logger(logging.INFO)


def get_color(c, s):
    return "\033[3%sm%s\033[0m" % (c, s)


def get_red(s):
    logger.info(s)
    return get_color(1, s)


def get_green(s):
    return get_color(2, s)


def get_yellow(s):
    return get_color(3, s)


def get_blue(s):
    return get_color(4, s)


def print_info(text):
    """打印普通信息
    """
    print text


def print_ok(text):
    """打印正确信息,绿色
    """
    # fmt = get_green("[   OK   ]    %s" % text)
    fmt = get_green(text)
    print fmt


def print_warn(text):
    """打印警告信息,黄色
    """
    # fmt = get_yellow("[  WARN  ]    %s" % text)
    fmt = get_yellow(text)
    print fmt


def print_error(text):
    """打印错误信息,红色
    """
    # fmt = get_red("[ ERROR ]    %s" % text)
    fmt = get_red(text)
    print fmt


def print_title(title, length=80):
    """打印标题,蓝色
    """
    print "\n"
    len_title = len(title)
    len_flag = int((length - len_title - 2) / 2)
    flag = "=" * len_flag
    fmt = "%s %s %s" % (flag, title, flag)
    print get_blue(fmt)


class RunCmdError(Exception):
    """执行系统命令异常
    """
    pass


def get_now_time():
    """查询当前时间

    :rtype str
    :return 当前系统时间的字符串
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def run_cmd(cmd, write_input=None):
    """运行一个系统命令

    :param cmd: str 要执行的系统命令
    :param write_input: str 输入的字符

    :rtype str
    :return 命令的执行结果
    """
    std_input = None
    if write_input:
        std_input = subprocess.PIPE

    p = subprocess.Popen(cmd, stdin=std_input, shell=True, close_fds=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if write_input:
        p.stdin.write(write_input)
    out_msg = p.stdout.read()
    err_msg = p.stderr.read()
    err_code = p.wait()
    logger.info("cmd: %s\n\n\t output: %s\n\n\t error message: %s\n" % (cmd, out_msg, err_msg))
    if err_code:
        print_error("run `%s` failed, %s" % (cmd, err_msg))
        # raise RunCmdError("run `%s` failed, %s" % (cmd, err_msg))

    return out_msg


def get_eth_ip():
    """查询以太网ip
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        eth_ip, port = s.getsockname()
    except socket.error:
        try:
            eth_ip_list = run_cmd("hostname -I")
            for eth_ip in eth_ip_list.split():
                if eth_ip.startswith("10.") or eth_ip.startswith("192."):
                    eth_ip = eth_ip
                    break
            else:
                eth_ip = eth_ip_list.split()[0]
        except Exception as e:
            logger.exception(e)
            eth_ip = '127.0.0.1'
    finally:
        s.close()
    return eth_ip


def check_str_to_content(file_path, pattern):
    """检查字符串是否在文件中

    :param file_path: str 文件全路径
    :param pattern: str 字符串或正则表达式
    """
    cmd = 'cat %s | grep -ie "%s"|grep -v grep | wc -l' % (file_path, pattern)
    count = int(run_cmd(cmd))
    result = False
    if count > 0:
        result = True
    return result


def replace_str_to_content(file_path, old_pattern, new_str):
    """替换文件中的字符串

    :param file_path: str 文件全路径
    :param old_pattern: str 字符串或正则表达式
    :param new_str: str 要替换的字符串
    """
    # grep 短匹配
    # grep -iP '^root:.*?:'
    # 在 sed 中, `?` 不生效
    cmd = "sed -ie 's/%s/%s/' %s" % (old_pattern, new_str, file_path)
    run_cmd(cmd)


def insert_str_to_content(file_path, old_pattern, new_str, head=True):
    """在指定字符前面或者后面插入字符串

    :param file_path: str 文件全路径
    :param old_pattern: str 字符串或正则表达式
    :param new_str: str 要替换的字符串
    :param head: bool 是否在匹配字符前面插入
    """
    if head:
        cmd = 'sed -ie "s/%s/%s&/" %s' % (old_pattern, new_str, file_path)
    else:
        cmd = 'sed -ie "s/%s/&%s/" %s' % (old_pattern, new_str, file_path)
    run_cmd(cmd)


def get_first_line_number(file_path, pattern):
    """查询字符第一次出现的行号

    :param file_path: str 文件全路径
    :param pattern: str 字符串或正则表达式

    :rtype str
    :return 所在的行号

    未找到内容则返回空
    """
    # cmd = "cat -n %s |grep -ie '%s' |awk '{print $1}'|sed -n \"1\"p" % (file_path, pattern)
    cmd = "sed -n '/%s/=' %s |sed -n \"1\"p" % (pattern, file_path)
    return run_cmd(cmd).strip()


def insert_line_to_content(file_path, old_pattern, new_str, head=True):
    """在指定字符前面或者后面插入新行

    :param file_path: str 文件全路径
    :param old_pattern: str 字符串或正则表达式
    :param new_str: str 要替换的字符串
    :param head: bool 是否在匹配字符前面插入
    """
    number = get_first_line_number(file_path, old_pattern)
    if head:
        # cmd = 'sed -ie "/%s/i\\%s" %s' % (old_pattern, new_str, file_path)  # 匹配的所有行都会插入
        cmd = 'sed -ie "%si\%s" %s' % (number, new_str, file_path)  # 只插入一次
    else:
        # cmd = 'sed -ie "/%s/a\\%s" %s' % (old_pattern, new_str, file_path)
        cmd = 'sed -ie "%sa\%s" %s' % (number, new_str, file_path)
    run_cmd(cmd)


def append_str_to_content(file_path, text):
    """在文件末尾追加字符串

    :param file_path: str 文件全路径
    :param text: str 要追加字符串
    """
    cmd = 'echo "%s" >> %s' % (text, file_path)
    run_cmd(cmd)


def delete_str_to_content(file_path, text):
    """在文件中删除字符串

    :param file_path: str 文件全路径
    :param text: str 要追加字符串
    """
    cmd = 'sed -ie "/%s/d" %s' % (text, file_path)
    run_cmd(cmd)


def replace_or_append_content(file_path, old_pattern, new_str):
    """替换或者追加字符串

    当字符串在文件中时,进行替换操作,不存在时进行追加

    :param file_path: str 文件全路径
    :param old_pattern: str 字符串或正则表达式
    :param new_str: str 要替换的字符串
    """
    if check_str_to_content(file_path, old_pattern):
        replace_str_to_content(file_path, old_pattern, new_str)
    else:
        append_str_to_content(file_path, new_str)


def copy_file(source_path, target_path):
    """复制文件

    需要输入 y 进行确认是否要覆盖文件

    :param source_path: str 源文件
    :param target_path: str 移动后的目标目录
    """
    cmd = "cp -avx %s %s" % (source_path, target_path)
    run_cmd(cmd, write_input="y")


def move_file(source_path, target_path):
    """移动文件

    需要输入 y 进行确认是否要覆盖文件

    :param source_path: str 源文件
    :param target_path: str 移动后的目标目录
    """
    cmd = "mv %s %s" % (source_path, target_path)
    run_cmd(cmd)


def delete_path_prefix(path):
    """删除全路径前面的 /

    处理成可以复制到某目录下的路径

    :rtype str
    :return 处理之后的目录
    """
    # 去掉目录前面的 /
    path = path[1:] if path.startswith(path) else path
    return path


def check_rpm_package_install(name):
    """检查rpm包是否安装

    :rtype bool
    :return
        True: 安装了该软件包
        False: 未安装该软件包
    """
    cmd = "rpm -qa | grep %s | wc -l" % name
    count = int(run_cmd(cmd))
    result = False
    if count > 0:
        result = True
    return result


def uninstall_rpm_package(name):
    """卸载rpm包
    """
    # 去除包名后缀
    if name.endswith(".rpm"):
        name = name[:-4]

    # 检查包是否安装
    if check_rpm_package_install(name):
        cmd = "rpm -qa | grep %s | xargs rpm -e --nodeps" % name
        run_cmd(cmd)


def install_rpm_package(name):
    """安装rpm包
    """
    cmd = "rpm -i %s" % name
    run_cmd(cmd)


def get_base_backup_path():
    """查询备份的路径

    :rtype str
    :return 备份目录
    """
    return os.path.join(BACKUP_FOLDER, "security_back_up")


class UpdateSystem(object):
    """修改安全策略
    """

    def __init__(self):
        self.base_backup_path = get_base_backup_path()  # 备份根目录

    @staticmethod
    def _update_password():
        """帐号口令相关
        """
        print_ok("修改帐号口令相关配置")
        replace_str_to_content(ETC_LOGIN_DEFS, "^PASS_MAX_DAYS.*", "PASS_MAX_DAYS 90")  # 口令生存周期
        replace_str_to_content(ETC_LOGIN_DEFS, "^PASS_MIN_DAYS.*", "PASS_MIN_DAYS 6")  # 口令更改最小间隔天数
        replace_str_to_content(ETC_LOGIN_DEFS, "^PASS_MIN_LEN.*", "PASS_MIN_LEN 6")  # 口令最小长度
        replace_str_to_content(ETC_LOGIN_DEFS, "^PASS_WARN_AGE.*", "PASS_WARN_AGE 30")  # 口令过期前警告天数

        # 检查设备密码复杂度策略 大小写/数字等限制只需要改一次即可
        replace_or_append_content(ETC_PAMD_SYSTEM_AUTH,
                                  "password\s*requisite\s*pam_cracklib.so.*",
                                  "password requisite pam_cracklib.so try_first_pass retry=3  "
                                  "ucredit=-1 lcredit=-1 dcredit=-1 ocredit=-1")

    @staticmethod
    def _update_other_security():
        """其它安全相关
        """
        print_ok("修改其它安全相关配置")
        # 检查是否设置命令行界面超时退出
        replace_or_append_content(ETC_PROFILE, "^export\s*TMOUT.*", "export TMOUT=600")

        # 系统引导器的类型为grub
        # 检查是否设置 grub 密码
        replace_or_append_content(BOOT_GRUB_MENU_LST, "^password\s*=.*", "password=%s" % GRUB_PASSWORD)

        # 检查系统core dump设置
        append_str_to_content(ETC_SECURITY_LIMITS_CONF, "* hard core 0")
        append_str_to_content(ETC_SECURITY_LIMITS_CONF, "* soft core 0")

        # 检查历史命令设置
        replace_or_append_content(ETC_PROFILE, "^HISTFILESIZE.*", "HISTFILESIZE=5")
        replace_or_append_content(ETC_PROFILE, "^HISTSIZE.*", "HISTSIZE=5")

        # 使用PAM认证模块禁止wheel组之外的用户su为root
        replace_or_append_content(ETC_PAMD_SU, "#*\s*auth\s*sufficient\s*pam_rootok.so.*",
                                  "auth sufficient pam_rootok.so")
        replace_or_append_content(ETC_PAMD_SU, "#*\s*auth\s*required\s*pam_wheel.so.*",
                                  "auth required pam_wheel.so group=wheel")

        # 把seekplum用户加到wheel组
        cmd = "usermod -G wheel seekplum"
        run_cmd(cmd)

        # 对系统账号进行登录限制 TODO: 做完之后任何人都会无法登录了 分数: 1
        # cmd = "cat %s |awk -F'[:]' '{print $1}'" % ETC_SHADOW
        # names = run_cmd(cmd).splitlines()
        # for name in names:
        #     name = name.strip()
        #     if name:
        #         replace_str_to_content(ETC_SHADOW, "^%s:[^:]*" % name, "%s:!!:" % name)

        # 密码重复使用次数限制
        replace_or_append_content(
            ETC_PAMD_SYSTEM_AUTH,
            "^password\s*sufficient\s*pam_unix.so\s*md5\s*shadow\s*nullok\s*try_first_pass\s*use_authtok.*",
            "password sufficient pam_unix.so md5 shadow nullok try_first_pass use_authtok remember=5"
        )

        # 账户认证失败次数限制 # TODO: su - root 报 `su: incorrect password` 错误 分数: 1
        # insert_line_to_content(ETC_PAMD_SYSTEM_AUTH,
        #                        "^auth",
        #                        "auth required pam_tally.so deny=5")
        # insert_line_to_content(ETC_PAMD_SYSTEM_AUTH,
        #                        "^account",
        #                        "account required pam_tally.so")

        append_str_to_content(ETC_PAMD_SSHD, "auth required pam_tally.so deny=5 unlock_time=600 no_lock_time"
                                             "\naccount required pam_tally.so ")

        # 检查是否关闭IP伪装和绑定多IP功能
        append_str_to_content(ETC_HOST_CONF, "nospoof on")
        replace_or_append_content(ETC_HOST_CONF, "multi.*", "multi off")

        # 检查是否限制远程登录IP范围
        eth_ip = get_eth_ip()
        append_str_to_content(ETC_HOSTS_ALLOW, "sshd:%s.:allow" % (eth_ip.rsplit(".", 1)[0]))
        run_cmd(XINETD_COMMAND)

        append_str_to_content(ETC_HOSTS_DENY, "all:all")
        run_cmd(XINETD_COMMAND)

        # 检查别名文件/etc/aliase 配置
        names = [
            "games",
            "ingres",
            "system",
            "toor",
            "uucp",
            "manager",
            "dumper",
            "operator",
            "decode",
            "root"
        ]
        for name in names:
            delete_str_to_content(ETC_ALIASES, "^%s\s*:.*" % name)
        run_cmd(NEWALIASES_COMMAND)

        # 检查别名文件 /etc/mail/aliases 配置
        if os.path.exists(ETC_MAIL_ALIASES):
            for name in names:
                delete_str_to_content(ETC_MAIL_ALIASES, "^%s\s*:.*" % name)
            run_cmd(NEWALIASES_COMMAND)

        # 检查拥有suid和sgid权限的文件 TODO: 调整后非 sudo 权限无法使用ping命令 分数 1
        # ping命令在运行中采用了ICMP协议，需要发送ICMP报文。但是只有root用户才能建立ICMP报文.
        # 而正常情况下，ping命令的权限应为-rwsr-xr-x，即带有suid的文件，一旦该权限被修改，则普通用户无法正常使用该命令。
        # 解决方案： 使用root用户执行“chmod u+s /bin/ping”。或者sudo ping xxx.xxx.xxx.xxx
        names = [
            USR_BIN_CHAGE,
            USER_BIN_GPASSWD,
            USER_BIN_WALL,
            USER_BIN_CHFN,
            USER_BIN_CHSH,
            USER_BIN_NEWGRP,
            USER_BIN_WRITE,
            USER_BIN_USERNETCTL,
            # USER_BIN_TRACEROUTE,
            BIN_MOUNT,
            BIN_UMOUNT,
            # BIN_PING,
            SBIN_NETREPPORT
        ]

        cmd = "find %s -type f -perm +6000 2>/dev/null" % " ".join(names)
        output = run_cmd(cmd).strip()
        for name in output.splitlines():
            cmd = "chmod 755 %s" % name
            run_cmd(cmd)

        # 检查是否配置定时自动屏幕锁定（适用于具备图形界面的设备）
        cmd_list = [
            "gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.mandatory "
            " --type bool  --set /apps/gnome-screensaver/idle_activation_enabled true",
            "gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.mandatory "
            "--type bool --set /apps/gnome-screensaver/lock_enabled true",
            "gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.mandatory "
            "--type string --set /apps/gnome-screensaver/mode blank-only",
            "gconftool-2 --direct --config-source xml:readwrite:/etc/gconf/gconf.xml.mandatory "
            "--type int --set /apps/gnome-screensaver/idle_delay 15"
        ]
        for cmd in cmd_list:
            run_cmd(cmd)

        # 检查是否安装chkrootkit进行系统监测
        install_rpm_package(CHK_ROOT_KIT)

        # 检查系统内核参数配置
        cmd_list = [
            'sysctl -w net.ipv4.conf.all.accept_redirects="0"',
            "echo 0 > %s " % PROC_SYS_NET_ACCEPT,
            'sysctl -w net.ipv4.conf.all.send_redirects="0"',
            "echo 0 > %s" % PROC_SYS_NET_SEND,
        ]
        for cmd in cmd_list:
            run_cmd(cmd)

    @staticmethod
    def _update_auth():
        """认证授权
        """
        print_ok("修改认证授权相关配置")
        # 检查用户umask设置
        replace_str_to_content(ETC_CSH_CSHRS, "umask\s*002", "umask 077")
        replace_str_to_content(ETC_CSH_LOGIN, "for login setup", "for login setup\\numask 077")
        replace_str_to_content(ETC_BASHRC, "umask\s*002", "umask 077")
        replace_str_to_content(ETC_PROFILE, "umask\s*002", "umask 077")

        # 检查重要目录或文件权限设置
        cmd_list = [
            "chmod 600 /etc/security",
            "chmod 750 /etc/rc6.d",
            "chmod 750 /etc/rc0.d/",
            "chmod 750 /etc/rc1.d/",
            # "chmod 750 /etc/",  # TODO: 这步做了会导致 paramiko 无法使用, /etc目录权限必须大于等于 755  分数: 5
            "chmod 750 /etc/rc4.d",
            "chmod 750 /etc/rc5.d/",
            "chmod 750 /etc/rc3.d",
            "chmod 750 /etc/rc.d/init.d/"
        ]
        for cmd in cmd_list:
            run_cmd(cmd)

        # 检查重要文件属性设置
        # 隐藏属性 i: 设定文件不能被删除、改名、设定链接关系，同时不能写入或新增内容。
        # 通过 lsattr 查看
        for file_name in SHADOW_ASSWORD:
            cmd = "chattr +i %s" % file_name
            run_cmd(cmd)

        # 检查用户目录缺省访问权限设置
        replace_str_to_content(ETC_LOGIN_DEFS, "^UMASK.*", "UMASK 027")

        # 检查是否设置ssh登录前警告Banner
        cmd_list = [
            "touch %s" % ETC_SSH_BANNER,
            "chown bin:bin %s" % ETC_SSH_BANNER,
            "chmod 644 %s" % ETC_SSH_BANNER,
            'echo " Authorized only. All activity will be monitored and reported " > %s' % ETC_SSH_BANNER
        ]
        for cmd in cmd_list:
            run_cmd(cmd)

        append_str_to_content(ETC_SSH_SSHD_CONFIG, "Banner %s" % ETC_SSH_BANNER)

        run_cmd(SSHD_COMMAND)

    @staticmethod
    def _update_driver():
        """协议安全
        """
        print_ok("修改协议安装相关配置")
        # 检查是否禁止root用户远程登录
        append_str_to_content(ETC_PAMD_LOGIN, "auth required pam_securetty.so")

        replace_str_to_content(ETC_SSH_SSHD_CONFIG, "#*\s*PermitRootLogin.*", "PermitRootLogin no")
        run_cmd(SSHD_COMMAND)

        # 检查是否修改snmp默认团体字
        uninstall_rpm_package("snmp")
        insert_str_to_content(ETC_SNMP_CONF, "^\w.*public", "#")

    @staticmethod
    def _update_log():
        """日志审计
        """
        print_ok("修改日志审计相关配置")
        # TODO: 检查是否配置远程日志功能  分数: 1

        # 检查是否记录用户对设备的操作
        cmd_list = [
            "touch %s" % VAR_LOG_PACCT,
            "accton %s" % VAR_LOG_PACCT,
            "lastcomm seekplum –f %s" % VAR_LOG_PACCT
        ]
        for cmd in cmd_list:
            run_cmd(cmd)

            # TODO: 检查安全事件日志配置  分数: 1

    def _update_backup(self):
        """对文件进行备份
        """
        # 对文件进行备份
        print_ok("对文件进行备份")
        for file_path in BACKUP_PATH:
            if os.path.isdir(file_path):
                path = ""
            else:
                path = os.path.dirname(file_path)
            path = delete_path_prefix(path)

            # 把文件放到备份目录
            backup_path = os.path.join(self.base_backup_path, path)

            # 创建备份目录
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            copy_file(file_path, backup_path)
        print_ok("完成了对文件的备份")

    def _back_backup(self):
        """回退时,对修改过的文件进行备份
        """
        now_time = get_now_time()
        # 备份根目录
        print_ok("对修改的文件进行回退")
        for file_path in BACKUP_PATH:
            path = delete_path_prefix(file_path)
            backup_path = os.path.join(self.base_backup_path, path)
            # 这两个文件 加上x 后就没有权限移动
            if file_path in [PROC_SYS_NET_SEND, PROC_SYS_NET_ACCEPT]:
                cmd = "cat %s > %s" % (backup_path, file_path)
                run_cmd(cmd, write_input='y')
                continue
            # 修改过的文件放到 临时目录
            temp_path = os.path.join(TEMP_FOLDER, "security_%s" % now_time, path)

            # 创建临时目录
            if not os.path.exists(temp_path):
                os.makedirs(temp_path)

            # 把修改过的文件放到临时目录
            move_file(file_path, temp_path)

            # 把之前备分的文件进行恢复
            # 修改过的文件放到 临时目录
            move_file(backup_path, file_path)

    @staticmethod
    def _back_delete_attr():
        """删除文件隐藏权限
        """
        print_ok("修改文件的隐藏权限")
        # 修改文件的隐藏权限
        for file_name in SHADOW_ASSWORD:
            cmd = "chattr -i %s" % file_name
            run_cmd(cmd)

    def _back_delete_file(self):
        """删除创建的文件
        """
        print_ok("删除创建的文件")
        # 删除创建的文件
        for file_path in DELETE_PATH:
            cmd = "rm -f %s" % file_path
            run_cmd(cmd)

        # 删除备份文件目录
        print_ok("删除备份文件目录")
        if BACKUP_FOLDER in self.base_backup_path:
            cmd = "rm -rf %s" % self.base_backup_path
            run_cmd(cmd)

    @staticmethod
    def _back_uninstall_package():
        """卸载安装的包
        """
        print_ok("卸载安装的chkroot包")
        uninstall_rpm_package(CHK_ROOT_KIT)

    @staticmethod
    def _back_restart_server():
        """重启服务
        """
        # 重启相关服务
        print_ok("重启相关服务")
        for cmd in BACK_COMMANDS:
            run_cmd(cmd)

    def back(self):
        """对修改的文件进行回退
        """
        print_ok("检查备份文件是否存在")
        # 还没开始操作无法进行回退
        if not os.path.exists(self.base_backup_path):
            logger.error("backup path %s not exists" % self.base_backup_path)
            print_error("没有对系统经修改过配置,不需要执行回退操作")
            sys.exit(1)
        self._back_backup()
        self._back_delete_file()
        self._back_delete_attr()
        self._back_uninstall_package()
        self._back_restart_server()

    def update(self):
        """对操作系统进行更改
        """
        print_ok("检查备份文件是否存在")
        # 已经操作过,不需要重复操作
        if os.path.exists(self.base_backup_path):
            logger.error("backup path is: %s, don't try again" % self.base_backup_path)
            print_error("已经修改过配置,不需要重复操作,备份路径: %s" % self.base_backup_path)
            sys.exit(1)
        self._update_backup()
        self._update_password()
        self._update_other_security()
        self._update_auth()
        self._update_driver()
        self._update_log()


def print_help():
    """打印帮助信息
    """
    info_message = """
    usage: check_security.py [-h] [-b]

    optional arguments:
      -h, --help      show this help message and exit.
      -b, --fallback  The operation that is done back.
    """
    print_info(info_message)

    warn_message = """

    无法进行调整的:
        1. [分数: 1] (等级: 可选) 检查是否配置远程日志功能
                     原因:/etc/syslog-ng/syslog-ng.conf配置文件不存在
        2. [分数: 1] (等级: 可选) 检查安全事件日志配置
                     原因: /etc/syslog-ng/syslog-ng.conf配置文件不存在

    脚本运行后注意事项:
        1. 只有同网段的机器可以进行登录
        2. root 用户无法再远程进行登录,可以用其它 wheel 组的用户登录后 su 到 root 用户

    """
    print_warn(warn_message)

    error_message = """
    不允许调整的:
        1. [分数: 5] (等级: 一般) 检查重要目录或文件权限设置
                     原因: /etc 目录权限必须大于等于 755,否则会导致程序无法ssh到其他主机
        2. [分数: 1] (等级: 可选) 检查是否对系统账号进行登录限制
                     原因: 修改后所有帐户都无法进行登录
        3. [分数: 1] (等级: 可选) 检查账户认证失败次数限制
                     原因: 修改后 wheel 组用户无法 su 到 root
        4. [分数: 1] (等级: 可选) 检查拥有suid和sgid权限的文件
                     原因: 调整后非 sudo 权限无法使用ping命令,导致程序无法正常显示节点的状态
    """
    print_error(error_message)


def confirm_input(prompt):
    """确认是否继续执行
    """
    confirm = raw_input(get_yellow(prompt))
    if str(confirm).lower() not in ["y", "yes"]:
        print_error("\n您选择了退出!\n")
        sys.exit(1)


def parse_args():
    """解析输入参数

    python2.6.6没有 argparse模块
    """
    # import argparse
    # parser = argparse.ArgumentParser()
    # # 修改print help信息
    # setattr(parser, "print_help", print_help)
    # parser_fallback = parser.add_mutually_exclusive_group(required=False)
    # parser_fallback.add_argument("-b", "--fallback",
    #                              required=False,
    #                              action="store_true",
    #                              dest="fallback",
    #                              default=False,
    #                              help="The operation that is done back.")
    #
    # args = parser.parse_args()
    # fallback = args.fallback
    fallback = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hb", ["help", "fallback"])
    except getopt.GetoptError:
        print_help()
        sys.exit(1)
    else:
        # 严格模式,只运行命令行参数
        if args:
            print_help()
            sys.exit(1)
        for opt, arg in opts:
            if opt in ["-h", "--help"]:
                print_help()
                sys.exit(0)
            elif opt in ["-b", "--fallback"]:
                fallback = True
                break
    return fallback


def main():
    """调整系统设置
    """
    manager = UpdateSystem()
    fallback = parse_args()
    print_ok("日志路径: %s\n" % LOG_PATH)
    # 执行恢复操作
    if fallback:
        confirm_input("注意:执行该脚本会对调整过的系统参数进行还原,请确认是否继续? [N/Y]: ")
        print_title("Back")
        manager.back()
    # 执行修改操作
    else:
        print_warn("注意: chkrootkit-0.49-9.el6.x86_64.rpm 包需要放在和本脚本同级目录下\n")
        confirm_input("注意:执行该脚本会调整系统相关参数,请确认是否继续? [N/Y]: ")
        print_title("Update")
        manager.update()


if __name__ == '__main__':
    main()
