#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import re
import sys
import os
import time
import subprocess
import threading
import logging

color = lambda c, s: "\033[3%sm%s\033[0m" % (c, s)
black = lambda s: color(0, s)
red = lambda s: color(1, s)
green = lambda s: color(2, s)
yellow = lambda s: color(3, s)
blue = lambda s: color(4, s)
purple = lambda s: color(5, s)
cyan = lambda s: color(6, s)
gray = lambda s: color(7, s)
blink = lambda s: "\033[5m%s\033[25m" % s
underline = lambda s: "\033[4m%s\033[24m" % s


def print_ok(check_status):
    fmt = green("[  OK  ]    %s" % check_status)
    print fmt


def print_error(check_status, recomm=''):
    if not check_status.endswith("."):
        check_status += "."
    fmt = red("[  ERROR  ]    %s %s" % (check_status, recomm))
    print fmt


def print_warn(check_status, recomm=''):
    if not check_status.endswith("."):
        check_status += "."
    fmt = yellow("[  WARN  ]    %s %s" % (check_status, recomm))
    print fmt


def print_title(title):
    print "\n"
    t = "%s  %s  %s" % ("=" * 30, title, "=" * 30)
    print t


def get_logger():
    logging.basicConfig(filename='install.log',
                        level=logging.DEBUG,
                        mode="w",
                        format='%(asctime)s %(levelname)s  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    _logger = logging.getLogger("seekplum.install")
    _logger.setLevel(logging.INFO)
    return _logger


logger = get_logger()


def run(cmd):
    logging.info("cmd: %s" % cmd)
    p = subprocess.Popen(cmd,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    stdout, stderr = p.communicate()
    if stderr:
        logger.info("cmd stderr: %s" % stderr)
        raise Exception("cmd: %s, stderr: %s" % (cmd, stderr))
    else:
        logger.info("cmd result: %s" % stdout)
        return stdout


class Seekplum_Install(object):
    def __init__(self):
        self.check_pass = 0
        self.check_error = 0
        self.check_warn = 0
        self.env_name = "seekplum-dev-env"
        self.port_list = ["9307", "6379", "8011", "11088", "11099", "80"]
        self.file_list = ["dbpool", "seekplum-web", "seekplum-auth"]
        self.username = "seekplum"
        self.mysql_user = "pig"
        self.mysql_passwd = "p7tiULiN0xSp2S03ZHJmHoVBaEYg3NYoRF0h4O7TIEk="
        self.mysql_ok = False
        self.mysql_tar_ok = False
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.MYSQL_NAME = os.path.join(self.env_name, "packages/mysql-5.7.15-linux-glibc2.5-x86_64.tar.gz")
        self.log_dir = "logs"  # 保留seekplum cloud log的目录名称
        self.log_sub_dirs = ["dbpool", "mysql", "nginx", "seekplum-auth", "seekplum-web", "redis", "supervisor"]

    # ==========================  属性设置 ======================
    @property
    def home(self):
        return os.path.join("/home", self.username)

    @property
    def env_path(self):
        return os.path.join(self.home, self.env_name)

    @property
    def log_path(self):
        return os.path.join(self.home, self.log_dir)

    @property
    def mysql_home(self):
        return os.path.join(self.env_path, "packages", "mysql")

    @property
    def mysql(self):
        return os.path.join(self.mysql_home, "bin", "mysql")

    @property
    def mysql_sock(self):
        return os.path.join(self.mysql_home, "tmp", "mysql.sock")

    @property
    def mysqld(self):
        return os.path.join(self.mysql_home, "bin/mysqld")

    @property
    def mysql_conf(self):
        return os.path.join(self.env_path, "packages", "conf/my.cnf")

    @property
    def mysql_server(self):
        return os.path.join(self.mysql_home, "support-files/mysql.server")

    # ===================   基础函数  ===================
    def flash(self):
        """
        清空相关参数，以重新使用
        """
        self.check_pass = 0
        self.check_error = 0
        self.check_warn = 0

    def yes_or_no(self):
        result = raw_input("Ignore warnings？(yes/no):")
        result = result.lower()
        while True:
            if result == 'no' or result == 'n':
                print("your choice is no, install cancled")
                sys.exit(1)
            elif result == 'yes' or result == 'y':
                break
            else:
                result = raw_input("ignore warnings？(yes/no):")

    def print_result(self, operation):
        """
        打印汇总结果
        :param operation:操作名称
        :param is_ok:成功次数
        :param is_warn:警告次数
        :param is_error:失败次数
        :return:
        """
        is_ok = green(self.check_pass)
        is_warn = yellow(self.check_warn) if self.check_warn > 0 else self.check_warn
        is_error = red(self.check_error) if self.check_error > 0 else self.check_error

        print '\n\n*******************************************************************\n\n'
        print "\t\t %s passed: %s\n" % (operation, is_ok)
        print "\t\t %s warnning: %s\n" % (operation, is_warn)
        print "\t\t %s error: %s" % (operation, is_error)
        print '\n\n*******************************************************************'
        if self.check_error > 0:
            sys.exit(1)
        if self.check_warn > 0:
            self.yes_or_no()

    # ======================  check ==================
    def check_os_version(self):
        """
        检查系统版本
        """
        cmd = "cat /etc/issue"
        os_host = run(cmd).strip().splitlines()[0]
        os_version = "check OS version: Your OS is %s" % os_host
        recomm = "Recommended OS is CentOS 6.x"
        match = re.search(r"(\d+\.?\d*)", os_host)
        if match:
            version = match.group(1)
        else:
            version = ""
        if "centos" in os_host.lower() and version.startswith("6."):
            print_ok(os_version)
            self.check_pass += 1
        elif (
                    "rehl" in os_host.lower() or "redhat" in os_host.lower() or "red hat" in os_host.lower()) and version.startswith(
                "6."):
            print_warn(os_version, recomm)
            self.check_warn += 1
        else:
            print_error(os_version, recomm)
            self.check_error += 1

    def check_os_bit(self):
        """
        检查32bit还是64bit
        """
        cmd = "getconf LONG_BIT"
        result = run(cmd).strip()
        if result == "64":
            print_ok("check os 64 bit")
            self.check_pass += 1
        else:
            print_error("check os 64 bit")
            self.check_error += 1

    def check_os_disk(self):
        """
        检查home目录大小是否超过512G
        """
        cmd = """df -Pm /home|sed -n '2p'|awk '{print $4}'"""
        check_result = run(cmd).strip()
        os_home_size = float(check_result) / 1024
        check_status = "Check disk space for /home directory"
        recomm = "The /home directory has %s GB space available, at least 512GB space is required" % round(os_home_size,
                                                                                                           1)
        if int(os_home_size) >= 512:
            self.check_pass += 1
            print_ok(check_status=check_status)
        else:
            self.check_warn += 1
            print_warn(check_status=check_status, recomm=recomm)

    def check_os_cpu(self):
        """
        检查cpu数量是否大于4个,如果小于4个，进行warn提示
        """
        cmd = '''lscpu |grep "^CPU(s):"|cut -d':' -f2'''
        result = run(cmd).strip()
        cpu_num = int(result)
        check_status = "Check CPU number"
        recomm = "Need no less 4 cpus ,Now cpu is %s cpus" % cpu_num
        if cpu_num >= 4:
            self.check_pass += 1
            print_ok(check_status=check_status)
        else:
            self.check_warn += 1
            print_warn(check_status=check_status, recomm=recomm)

    def check_os_mem(self):
        """
        检查操作系统内存是否大于4G
        """
        cmd = "cat /proc/meminfo"
        result = run(cmd).lower()
        mem_total = "0 kb"
        for line in result.splitlines():
            if line.startswith("memtotal"):
                mem_total = line.split(":")[-1].strip()
                break

        mem_size = int(mem_total.split()[0])

        if mem_total.endswith("kb"):
            mem_size = mem_size / 1024 / 1024
        elif mem_total.endswith("mb"):
            mem_size = mem_size / 1024
        elif mem_total.endswith("gb"):
            mem_size = mem_size

        check_status = "Check total memory"
        recomm = "need no less 4G Memory ,Now Memory is %s G" % mem_size
        if mem_size >= 4:
            self.check_pass += 1
            print_ok(check_status=check_status)
        else:
            self.check_warn += 1
            print_warn(check_status=check_status, recomm=recomm)

    def check_os_user(self):
        """
        检查用户是否存在，不存在则创建
        """
        cmd_check = "id %s" % self.username
        user_ok = False
        try:
            run(cmd_check).strip()
            if os.path.exists(self.home):
                run("sudo chown -R %s:%s %s" % (self.username, self.username, self.home))
            else:
                run("sudo mkdir %s" % self.home)
                run("sudo chown -R %s:%s %s" % (self.username, self.username, self.home))
            print_ok("Check user %s" % self.username)
            self.check_pass += 1
            user_ok = True
        except Exception as e:
            # print_warn("no user %s, now create" % self.username)
            # self.check_warn += 1
            cmd_add = "sudo useradd -m %s" % self.username
            try:
                run(cmd_add)
            except Exception as e:
                pass
            if os.path.exists(self.home):
                print_ok("create user %s" % self.username)
                self.check_pass += 1
            else:
                print_error("create user %s" % self.username)
                self.check_error += 1
        if not user_ok:
            try:
                # 再次检查
                run(cmd_check).strip()
                print_ok("check user %s exist" % self.username)
                self.check_pass += 1
            except Exception as e:
                print_error("check user %s exist" % self.username)
                self.check_error += 1

    def check_os_port(self):
        """
        检测端口是否被占用
        """
        cmd = "sudo netstat -lnpa | grep LISTEN"
        output = run(cmd)
        all_post = '|'.join(self.port_list)
        use_port = re.findall(r':(%s)\s+.*LISTEN\s+(\d+)/(\S+)\s' % all_post, output)
        use_port = list(set(use_port))
        for port in use_port:
            print_error("port: %s, pid:%s, program:%s in use" % (port[0], port[1], port[2]))
            self.check_error += 1
            if port[0] in self.port_list:
                self.port_list.remove(port[0])
        for port in self.port_list:
            print_ok("check port %s ok" % port)
            self.check_pass += 1

    def do_check(self):
        """
        check部分主函数
        """
        print_title("check")
        self.check_os_version()
        self.check_os_bit()
        self.check_os_disk()
        self.check_os_cpu()
        self.check_os_mem()
        self.check_os_user()
        self.check_os_port()
        self.print_result("check")

    #  ============================    copy ========================
    def get_exist_files(self):
        """
        返回file_list中创建成功的目录
        """
        exist_file = []
        for file in self.file_list:
            file_path = os.path.join(self.home, file)
            if os.path.exists(file_path):
                exist_file.append(file)
        return exist_file

    def copy_project_config(self, project_name, cmd_list):
        for info in cmd_list:
            cmd = info["cmd"]
            name = info["name"]
            try:
                run(cmd)
                self.check_pass += 1
                print_ok("copy %s config %s " % (project_name, name))
                sys.stdout.flush()
            except Exception as e:
                print_error("copy %s config %s: %s" % (project_name, name, str(e)))
                self.check_error += 1

    def cp_seekplum_web_config(self):
        conf_seekplum = os.path.join(self.home, "seekplum-web/settings")

        conf_supervisor_dest = os.path.join(self.env_path,
                                            "packages/conf/supervisor/conf.d/supervisor_seekplum_web.conf")
        conf_supervisor_src = os.path.join(self.home, "seekplum-web/conf/supervisor_seekplum_web.conf")

        conf_nginx_dest = os.path.join(self.env_path, "packages/conf/nginx/sites-enabled/nginx_seekplum_web.conf")
        conf_nginx_src = os.path.join(self.home, "seekplum-web/conf/nginx_seekplum_web.conf")

        cmd_yaml = "cd %s && rm -f db.yaml && cp db.yaml.simple db.yaml" % conf_seekplum
        cmd_super = "rm -rf %s && cp %s  %s" % (conf_supervisor_dest, conf_supervisor_src, conf_supervisor_dest)
        cmd_nginx = "rm -rf %s && cp %s -f %s" % (conf_nginx_dest, conf_nginx_src, conf_nginx_dest)
        cmd_list = [{"name": "db.yaml", "cmd": cmd_yaml},
                    {"name": "supervisor", "cmd": cmd_super},
                    {"name": "nginx", "cmd": cmd_nginx},
                    ]
        self.copy_project_config("seekplum", cmd_list)

    def cp_dbpool_config(self):
        conf_dbpool = os.path.join(self.home, "dbpool/src/settings")
        conf_supervisor_dest = os.path.join(self.env_path, "packages/conf/supervisor/conf.d/supervisor_dbpool.conf")
        conf_supervisor_src = os.path.join(self.home, "dbpool/src/settings/supervisor_dbpool.conf")
        conf_nginx_dest = os.path.join(self.env_path, "packages/conf/nginx/sites-enabled/nginx_dbpool.conf")
        conf_nginx_src = os.path.join(self.home, "dbpool/src/settings/nginx_dbpool.conf")

        cmd_yaml = "cd %s && rm -f db.yaml && cp db.yaml.simple db.yaml" % conf_dbpool
        cmd_super = "rm -rf %s && cp %s %s" % (conf_supervisor_dest, conf_supervisor_src, conf_supervisor_dest)
        cmd_nginx = "rm -rf %s && cp  %s %s" % (conf_nginx_dest, conf_nginx_src, conf_nginx_dest)
        cmd_list = [{"name": "db.yaml", "cmd": cmd_yaml},
                    {"name": "supervisor", "cmd": cmd_super},
                    {"name": "nginx", "cmd": cmd_nginx},
                    ]
        self.copy_project_config("dbpool", cmd_list)

    def cp_seekplum_auth_config(self):
        conf_auth = os.path.join(self.home, "seekplum-auth/settings")
        conf_supervisor_dest = os.path.join(self.env_path,
                                            "packages/conf/supervisor/conf.d/seekplum_auth.conf")
        conf_supervisor_src = os.path.join(self.home, "seekplum-auth/conf/supervisor/seekplum_auth.conf")
        conf_nginx_dest = os.path.join(self.env_path, "packages/conf/nginx/sites-enabled/seekplum_auth.conf")
        conf_nginx_src = os.path.join(self.home, "seekplum-auth/conf/nginx/seekplum_auth.conf")

        cmd_yaml = "cd %s && rm -f db.yaml && cp db.yaml.simple db.yaml" % conf_auth
        cmd_super = "rm -rf %s  && cp %s %s" % (conf_supervisor_dest, conf_supervisor_src, conf_supervisor_dest)
        cmd_nginx = "rm -rf %s && cp  %s %s" % (conf_nginx_dest, conf_nginx_src, conf_nginx_dest)
        cmd_list = [{"name": "db.yaml", "cmd": cmd_yaml},
                    {"name": "supervisor", "cmd": cmd_super},
                    {"name": "nginx", "cmd": cmd_nginx},
                    ]
        self.copy_project_config("seekplum auth", cmd_list)

    def cp_mysql_config(self):
        conf_src = os.path.join(self.home, self.env_name, "packages/my.cnf")
        conf_dest = os.path.join(self.home, self.env_name, "packages/conf/my.cnf")
        try:
            run("rm -f %s && cp %s %s" % (conf_dest, conf_src, conf_dest))
            self.check_pass += 1
            print_ok("copy mysql config success")
            sys.stdout.flush()
        except Exception as e:
            print_error(str(e))
            self.check_error += 1

    def cp_projects(self):
        if self.current_path != self.home:
            is_env_exits = os.path.exists(self.env_path)
            env_bak = os.path.join(self.home, "seekplum-dev-env.bak")
            if is_env_exits:
                run("mv {} {}".format(self.env_path, env_bak))
            senv = os.path.join(self.current_path, self.env_name)
            run("cp -R %s %s" % (senv, self.home))
            is_exists = os.path.exists(self.env_path)
            if is_exists:
                print_ok("copy seekplum-dev-env success")
                sys.stdout.flush()
                self.check_pass += 1
            else:
                print_error("copy seekplum-dev-env failed")
                sys.stdout.flush()
                self.check_error += 1
        else:
            print_ok("seekplum-dev-env no need to copy")
            sys.stdout.flush()
            self.check_pass += 1
        for file in self.file_list:
            file_src = os.path.join(self.current_path, "cloud", file)
            file_dest = os.path.join(self.home, file)
            run("cp -R %s %s" % (file_src, file_dest))
        copied_files = self.get_exist_files()
        not_copied_files = []
        for file in self.file_list:
            if file not in copied_files:
                not_copied_files.append(file)
        if not_copied_files:
            print_error("copy failed file: %s" % (" ".join(not_copied_files)))
            sys.stdout.flush()
            self.check_error += 1
        else:
            print_ok("copy file %s success" % (" ".join(copied_files)))
            sys.stdout.flush()
            self.check_pass += 1

    def create_log_dir(self):
        run("sudo mkdir -p %s" % self.log_path)
        not_exists_log_dir = []
        for sub_dir in self.log_sub_dirs:
            log_path = os.path.join(self.log_path, sub_dir)
            run("sudo mkdir -p %s" % log_path)
            if not os.path.exists(log_path):
                not_exists_log_dir.append(log_path)
        if not_exists_log_dir:
            print_error("create %s failed." % (" ".join(not_exists_log_dir)))
            sys.stdout.flush()
            self.check_error += 1
        else:
            print_ok("create log dir success")
            sys.stdout.flush()
            self.check_pass += 1

    def change_usermode(self):
        try:
            run("sudo chown -R %s:%s %s" % (self.username, self.username, self.home))
        except:
            print_error("change file owner to %s in %s" % (self.username, self.home))
            sys.stdout.flush()
            self.check_error += 1
        else:
            print_ok("change file owner to %s in %s" % (self.username, self.home))
            sys.stdout.flush()
            self.check_pass += 1

    def copy_files(self):
        """拷贝文件"""

        # 在home目录下，seekplum-dev-env则不用进行拷贝
        def _copy_files():
            self.cp_projects()
            self.cp_seekplum_web_config()
            self.cp_dbpool_config()
            self.cp_seekplum_auth_config()
            self.cp_mysql_config()

        t = threading.Thread(target=_copy_files)
        t.start()
        while t.isAlive():
            a = ["|", "/", "-", "\\"]
            for i in a:
                sys.stdout.write("\b{0}\b".format(i))
                sys.stdout.flush()
                time.sleep(0.03)

    def do_copy(self):
        """
        copy部分主函数
        """
        print_title("copy files")
        self.flash()
        self.copy_files()
        self.create_log_dir()
        self.change_usermode()
        self.print_result("copy file")

    # ========================== install mysql  ====================

    def decompress_mysql(self):
        """mysql解压进度"""

        def tar_mysql():
            packages = os.path.join(self.env_path, "packages")
            tar_mysql = os.path.join(self.home, self.MYSQL_NAME)
            tar_cmd = "tar zxvf %s -C %s" % (tar_mysql, packages)
            try:
                run(tar_cmd)
                self.mysql_tar_ok = True
            except Exception as e:
                print_error(str(e))
                self.check_error += 1

        def mysql_size():
            mysql_path = os.path.join(self.env_path, "packages/mysql-5.7.15-linux-glibc2.5-x86_64")
            cmd = "du -s %s" % mysql_path
            try:
                result = run(cmd)
                size = result.split('\t')[0]
                size = int(size)
            except Exception as e:
                size = 0
            return size

        # 解压前删除老的mysql
        cmd = "rm -rf %s" % self.mysql_home
        run(cmd)

        # 开启线程解压mysql
        t = threading.Thread(target=tar_mysql)
        t.start()
        output = sys.stdout
        size = mysql_size()
        SIZE = 2579548
        while t.isAlive():
            percent = (size * 100) / SIZE
            count = int(percent) if percent > 0 else 0
            output.write('\rdecompress mysql: %s%%' % count)
            output.flush()
            time.sleep(1)
            size = mysql_size()
        output.write('\rdecompress mysql: 100%\n')
        output.flush()

        # 重命名
        name_mysql = os.path.join(self.env_path, "packages", "mysql-5.7.15-linux-glibc2.5-x86_64")
        cmd = "mv %s %s" % (name_mysql, self.mysql_home)
        run(cmd)

    def install_mysql(self):
        """
        安装mysql
        """
        cmd_list = list()
        # 在mysql目录下创建logs,一定要创建，否则无法安装
        logs_cmd = "mkdir %s" % os.path.join(self.mysql_home, "logs")
        cmd_list.append(logs_cmd)
        # 修改文件夹权限
        dir_cmd = "chown -R %s:%s %s" % (self.username, self.username, self.mysql_home)
        cmd_list.append(dir_cmd)
        # 初始化mysql， MYSQL_HOME中创建data目录
        init_cmd = "%s  --defaults-file=%s --initialize-insecure" % (self.mysqld, self.mysql_conf)
        cmd_list.append(init_cmd)
        for cmd in cmd_list:
            try:
                run(cmd)
            except Exception as e:
                print_error(str(e))
                print_error("mysql initialize failed")
                self.check_error += 1
                sys.exit(1)
        print_ok("initialize mysql")
        self.check_pass += 1

    def set_mysql_autostart(self):
        """设置mysql服务， 开机自启动 """
        mysql_init = "/etc/init.d/mysql"
        profile_file = "/etc/profile"

        start_list = list()
        # 1.删除/etc/init.d中原本的mysql
        rm_on = "rm -f %s" % mysql_init
        start_list.append(rm_on)

        # 2.重新复制mysql.server
        cp_on = "cp %s %s" % (self.mysql_server, mysql_init)
        start_list.append(cp_on)
        # 设置执行权限
        chmod_mysql = "chmod +x %s" % mysql_init
        start_list.append(chmod_mysql)

        # 3.检查是否添加过环境变量
        file_home = "export MYSQL_HOME=%s" % self.mysql_home
        file_path = "export PATH=$PATH:$MYSQL_HOME/bin"
        with open(profile_file) as f:
            file_content = f.read()
        with open(profile_file, "a") as f:
            if file_home not in file_content:
                f.write(file_home)
                f.write("\n")
            if file_path not in file_content:
                f.write(file_path)
                f.write("\n")

        # 4.设置开机启动
        chkconfig = "chkconfig --add mysql"
        start_list.append(chkconfig)
        chkconfig_on = "chkconfig --level 2345 mysql on"
        start_list.append(chkconfig_on)

        # 将mysql的lib目录加入到/etc/ld.so.d/mysql-seekplum.conf中, 否则python中的MySQLdb包不能使用
        cmd = "echo %s > /etc/ld.so.conf.d/mysql-seekplum.conf" % (os.path.join(self.mysql_home, "lib"))
        start_list.append(cmd)
        cmd = "ldconfig"
        start_list.append(cmd)
        is_ok = True
        for cmd in start_list:
            try:
                run(cmd)
                self.check_pass += 1
            except Exception as e:
                print_error(str(e))
                print_error("set mysql auto start on boot failed")
                self.check_error += 1
                is_ok = False
        if is_ok:
            print_ok("set mysql boot start success")
            self.check_pass += 1
        else:
            print_error("set mysql boot start failed")
            self.check_error += 1
            sys.exit(1)

    def start_mysql(self):
        """启动mysql"""
        # 启动前，先杀死老的mysql进程
        cmd = "pkill -9 mysql"
        run(cmd)
        # 启动
        cmd_start = "service mysql start > /dev/null"
        os.system(cmd_start)
        logger.info("cmd: %s" % cmd_start)
        cmd_status = "service mysql status"
        output = run(cmd_status)

        T = 60
        while "MySQL is not running, but " in output and T >= 0:
            print "\rwaitting for mysql start up %s" % "." * (60 - T)
            sys.stdout.flush()
            time.sleep(1)
            output = run(cmd_status)
            T -= 1

        if "not running" in output:
            print_error("start mysql failed: %s " % output)
            self.check_error += 1
            sys.exit(1)
        else:
            self.check_pass += 1
            print_ok("start mysql server")

    def set_mysql_user(self):
        """
        连接mysql，初始密码为空，并添加用户
        """
        grant_cmd = "GRANT ALL PRIVILEGES ON *.* TO 'pig'@'%' IDENTIFIED BY 'p7tiULiN0xSp2S03ZHJmHoVBaEYg3NYoRF0h4O7TIEk=';flush privileges;"
        sock_cmd = '%s -uroot -S %s -e "%s"' % (self.mysql, self.mysql_sock, grant_cmd)
        try:
            run(sock_cmd)
            print_ok("set mysql user success")
            self.check_pass += 1
        except Exception as e:
            print_error("set mysql user failed")
            self.check_error += 1
            sys.exit(1)

    def create_database(self):
        """
        创建seekplum,dbpool数据库
        """
        mysqld = '%s -upig -pp7tiULiN0xSp2S03ZHJmHoVBaEYg3NYoRF0h4O7TIEk= -S %s' % (self.mysql, self.mysql_sock)
        create_sql = lambda x: "create database if not exists %s;" % x
        cmd_list = list()
        # 创建seekplum,dbpool数据库
        create_seekplum_cmd = '%s -e "%s"' % (mysqld, create_sql("seekplum"))
        cmd_list.append(create_seekplum_cmd)
        create_dbpool_cmd = '%s -e "%s"' % (mysqld, create_sql("dbpool"))
        cmd_list.append(create_dbpool_cmd)
        is_ok = True
        for cmd in cmd_list:
            try:
                run(cmd)
            except Exception as e:
                # 这里可能会报警告出来，如果其中有error，则认为是错误
                if "error" in str(e):
                    print_error(str(e))
                    self.check_error += 1
                    is_ok = False
        if is_ok:
            print_ok("create db success")
            self.check_pass += 1
        else:
            print_error("create db success")
            self.check_error += 1
            sys.exit(1)

    def create_tables(self):
        """
        初始化数据库表
        """
        dbpool = os.path.join(self.home, "dbpool/src")
        seekplum_web = os.path.join(self.home, "seekplum-web")
        python_path = os.path.join(self.env_path, "bin/python")
        mysql_lib = os.path.join(self.env_path, "packages/mysql/lib")
        dbpool_path = "export PYTHONPATH=%s" % dbpool
        seekplum_web_path = "export PYTHONPATH=%s" % seekplum_web
        library_path = "export LD_LIBRARY_PATH=%s" % mysql_lib
        cmd_doc = []
        cmd_list = []
        cmd_doc.append('set library path')
        cmd_list.append(library_path)
        cmd_doc.append('init dbpool database ...')
        cmd_list.append("%s &&  cd %s && %s bin/init_models.pyc" % (dbpool_path, dbpool, python_path))
        cmd_doc.append('init seekplum-web database ...')
        cmd_list.append("%s && cd %s && %s bin/init_models.pyc" % (seekplum_web_path, seekplum_web, python_path))
        is_ok = True
        for cmd_title, cmd in zip(cmd_doc, cmd_list):
            try:
                run(cmd)
                print_ok(cmd_title)
                self.check_pass += 1
            except Exception as e:
                print_error("%s: %s" % (cmd_title, str(e)))
                self.check_error += 1
                is_ok = False
        if not is_ok:
            sys.exit(1)

    def do_mysql(self):
        """
        mysql部分主函数
        """
        print_title("install mysql")
        self.decompress_mysql()
        self.install_mysql()
        self.set_mysql_autostart()
        self.start_mysql()
        self.set_mysql_user()
        self.create_database()
        self.create_tables()

    # =========================  setting ================
    def set_hostname(self, check_again=False):
        """
        检测/etc/hosts是否有相应的设置，如果没有，则进行设置
        :param check_again: True再次检查
        :return:
        """
        cmd = "hostname"
        hostname = run(cmd).strip()
        with open("/etc/hosts") as f:
            lines = f.read()
        pattern = re.compile("127.0.0.1\s+%s" % hostname, re.M)
        match = pattern.search(lines)
        if not match:
            if check_again:
                line = "127.0.0.1   %s" % hostname
                print_error("set hostname in /etc/hosts failed, please add line %s at the end of file %s" % (
                    blink(underline(line)), blink(underline("/etc/hosts"))))
                self.check_error += 1
                return
            else:
                run("echo 127.0.0.1 `hostname` >> /etc/hosts")
                self.set_hostname(True)
        else:
            print_ok("check hostname setting in /etc/hosts")
            self.check_pass += 1

    def set_firewall(self):
        """设置防火墙，开启80端口"""
        try:
            run("/sbin/iptables -I INPUT -p tcp --dport 80 -j ACCEPT && /etc/rc.d/init.d/iptables save")
            self.check_pass += 1
            print_ok("Set firewall，start 80 port success")
        except Exception as e:
            self.check_error += 1
            print_error(str(e))

    def set_alias(self):
        """设置alias"""
        supervisord = os.path.join(self.env_path, "bin/supervisord")
        supervisord_conf = os.path.join(self.env_path, "packages/conf/supervisor/supervisord.conf")
        supervisorctl = os.path.join(self.env_path, "bin/supervisorctl")
        alias_list = list()
        mystart = "alias mystart=\\'%s -c %s\\'" % (supervisord, supervisord_conf)
        alias_list.append(mystart)
        mysuper = "alias mysuper=\\'%s -c %s\\'" % (supervisorctl, supervisord_conf)
        alias_list.append(mysuper)
        senv = "alias senv=\\'source %s\\'" % os.path.join(self.env_path, "bin/activate")
        alias_list.append(senv)
        try:
            now_home = run("echo $HOME").strip()
            no_such_home = False
        except Exception as e:
            print_error(str(e))
            self.check_error += 1
            no_such_home = True
            now_home = ''
        if not no_such_home:
            bashrc = os.path.join(now_home, ".bashrc")
            with open(bashrc) as f:
                alias_content = f.read()
            set_alias_ok = True
            for alias in alias_list:
                res = alias.split("=")
                if res[0] not in alias_content:
                    alias_bash = "echo %s >> %s" % (alias, bashrc)
                    try:
                        run(alias_bash)
                    except Exception as e:
                        print_error(str(e))
                        set_alias_ok = False
                        self.check_error += 1
                        print_error(str(alias_bash))
                        self.check_error += 1
            if set_alias_ok:
                self.check_pass += 1
                print_ok("set alias success")

    def do_settings(self):
        """
        setting 部分的主函数
        """
        print_title("do settings")
        self.flash()
        self.set_hostname()
        self.set_firewall()
        self.set_alias()
        # self.print_result("do settings")

    # =============================   start supervisor =====================
    def start_supervisor(self):
        """ 启动superviord """
        # 清除supervisor.sock文件
        cmd = "pkill -9 supervisord"
        try:
            run(cmd)
        except:
            pass
        try:
            sock = run("find / -name *supervisor.sock")
            ret = sock.split('\n')
            unlink_ok = True
            for res in ret:
                if res:
                    unlink = "unlink %s" % res
                    try:
                        run(unlink)
                    except Exception as e:
                        print_error(str(e))
                        self.check_error += 1
                        unlink_ok = False
            if unlink_ok:
                self.check_pass += 1
                print_ok("unlink supervisor.sock success!")
        except Exception as e:
            print_error(str(e))
            self.check_error += 1
        supervisord = os.path.join(self.env_path, "bin/supervisord")
        supervisord_conf = os.path.join(self.env_path, "packages/conf/supervisor/supervisord.conf")
        start_supervisor = "%s -c %s" % (supervisord, supervisord_conf)
        try:
            run(start_supervisor)
            self.check_pass += 1
            print_ok("start supervisor success")
        except Exception as e:
            self.check_error += 1
            print_error("start supervisor failed: %s" % str(e))

    def set_supervisor_autostart(self):
        """
        supervisor 开机自启动
        """
        supervisord = """#!/bin/sh
#
# /etc/rc.d/init.d/supervisord
#
# Supervisor is a client/server system that
# allows its users to monitor and control a
# number of processes on UNIX-like operating
# systems.
#
# chkconfig: - 64 36
# description: Supervisor Server
# processname: supervisord

# Source init functions
. /etc/rc.d/init.d/functions

prog="supervisord"

prefix="/home/seekplum/seekplum-dev-env"
exec_prefix="${prefix}"
prog_bin="${exec_prefix}/bin/supervisord"
conf=/home/seekplum/seekplum-dev-env/packages/conf/supervisor/supervisord.conf
prog_stop_bin="${exec_prefix}/bin/supervisorctl"

PIDFILE="/tmp/seekplum_supervisord.pid"


start()
{
       echo -n $"Starting $prog: "
       daemon $prog_bin --pidfile $PIDFILE -c $conf
       [ -f $PIDFILE ] && success $"$prog startup" || failure $"$prog startup"
       echo
}

stop()
{
       [ -f $PIDFILE ] && action "Stopping $prog"  $prog_stop_bin -c $conf shutdown || success $"$prog shutdown"
       echo
}

case "$1" in

 start)
   start
 ;;

 stop)
   stop
 ;;

 status)
       status $prog
 ;;

 restart)
   stop
   start
 ;;

 *)
   echo "Usage: $0 {start|stop|restart|status}"
 ;;

esac

"""
        supervisord_path = '/etc/rc.d/init.d/supervisord'
        with open(supervisord_path, 'w') as f:
            f.write(supervisord)
            f.close()
        cmd_list = list()
        chmod_x = "chmod +x %s" % supervisord_path
        cmd_list.append(chmod_x)
        chkconfig_add = "chkconfig --add supervisord"
        cmd_list.append(chkconfig_add)
        chkconfig_on = "chkconfig supervisord on"
        cmd_list.append(chkconfig_on)
        supervisor_boot_start = True
        for cmd in cmd_list:
            try:
                run(cmd)
            except Exception as e:
                print_error(str(e))
                self.check_error += 1
                supervisor_boot_start = False
        if supervisor_boot_start:
            self.check_pass += 1
            print_ok("set supervisor auto start boot success")
        else:
            print_error("set supervisor auto start on boot failed")
            self.check_error += 1

    def do_supervisor(self):
        """
        supervisor部分主函数
        """
        print_title("supervisor")
        self.set_supervisor_autostart()
        self.start_supervisor()


if __name__ == "__main__":
    help = "usage: %s [check|copy|mysql|settings|supervisor]" % sys.argv[0]
    install = Seekplum_Install()
    if len(sys.argv) == 1:
        install.do_check()
        install.do_copy()
        install.do_mysql()
        install.do_settings()
        install.do_supervisor()
    elif len(sys.argv) == 2:
        args = sys.argv[1]
        if args in ["-h", "--help"]:
            print help
        args_func = {"check": install.do_check,
                     "copy": install.do_copy,
                     "mysql": install.do_mysql,
                     "settings": install.do_settings,
                     "supervisor": install.do_supervisor,
                     }
        func = args_func.get(args)
        if func:
            func()
        else:
            print help
    else:
        print help
