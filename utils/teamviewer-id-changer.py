#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
问题描述: ⾃己MBP上的Teamviewer出现5分钟限制(即，只让我远程连接5 分钟，然而事实是1分钟左右便会自动断开，
         并且需要等待一段时间后才可以继续连接)，提示让我购买序列列号。
原因: 自己个人使用过于频繁，被怀疑为商业⾏为!!! PS:下述的解决方案本人已在自己的MBP上亲测通过，因此大家可以将其作为一个参考。
核⼼思路: 改变自己MBP上Teamviewer客户端的 ID。Teamviewer客户端ID展示:只需将YOUR ID改变即可

现具体阐述解决⽅方案:
1.关闭Teamviewer
2.以 `sudo` 权限运⾏当前脚本
3.重启电脑
4.重新打开Teamviewer，若上述操作成功，你便会发现此时Teamviewer客户端 的ID已经发生了变化。
  否则，可以多尝试几次。若还不行，那可能此方案并不适合你。
"""
from __future__ import print_function

import sys
import os
import datetime
import platform
import re
import random
import string

PY2 = sys.version_info[0] == 2


def program_exit(status=1):
    """退出程序
    """
    sys.exit(status)


def id_patch(path, plat, serial):
    with open(path, 'r+b') as f:
        binary = f.read()
    platform_pattern = "IOPlatformExpert.{6}"
    serial_pattern = "IOPlatformSerialNumber%s%s%sUUID"

    binary = re.sub(platform_pattern, plat, binary)
    binary = re.sub(serial_pattern % (chr(0), "[0-9a-zA-Z]{8,8}", chr(0)), serial_pattern % (chr(0), serial, chr(0)),
                    binary)
    with open(path, 'wb') as f:
        f.write(binary)
    return True


def random_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def check_system_type_and_current_user():
    """检查系统环境和当前用户
    """
    if not PY2:
        print("Wrong version")
        program_exit()

    if platform.system() != 'Darwin':
        print('This script can be run only on MAC OS.')
        program_exit()

    if os.geteuid() != 0:
        print('This script must be run form root.')
        program_exit()

    username = os.environ.get('SUDO_USER')
    if not username:
        print('Can not find user name. Run this script via sudo from regular user')
        program_exit()
    if username == 'root':
        print('Can not find user name. Run this script via sudo from regular user')
        program_exit()
    return username


def listdir_full_path(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


def get_team_viewer_configs(home_dir_lib):
    team_viewer_configs = []
    for file_path in listdir_full_path(home_dir_lib):
        if 'teamviewer'.lower() in file_path.lower():
            team_viewer_configs.append(file_path)

    if not team_viewer_configs:
        print("There is no TemViewer configs found.")
        print("Maybe you have deleted it manualy or never run TeamViewer after installation.")
        print("Nothing to delete.")
    # Delete config files
    else:
        print("Configs found:\n")
        for file_path in team_viewer_configs:
            print(file_path)

        print("This files will be DELETED permanently.")
        print("All TeamViewer settings will be lost")

        backup_path = "/tmp/teamviewer_backup"
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
        suffix = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        for file_path in team_viewer_configs:
            os.rename(file_path, os.path.join(backup_path, "%s.%s" % (os.path.basename(file_path), suffix)))
        print("Done.")


def check_team_viewer_binary():
    team_viewer_binary = [
        '/Applications/TeamViewer.app/Contents/MacOS/TeamViewer',
        '/Applications/TeamViewer.app/Contents/MacOS/TeamViewer_Service',
        '/Applications/TeamViewer.app/Contents/Helpers/TeamViewer_Desktop',
    ]

    for file_path in team_viewer_binary:
        if not os.path.exists(file_path):
            print("File not found: " + file_path)
            print("Install TeamViewer correctly")
            program_exit()

    random_serial = random_generator()
    random_platform = "IOPlatformExpert" + random_generator(6)

    print("PlatformDevice: " + random_platform)
    print("PlatformSerial: " + random_serial)

    for file_path in team_viewer_binary:
        try:
            id_patch(file_path, random_platform, random_serial)
        except Exception as e:
            print(e)
            print("Error: can not patch file ", file_path)
            print("Wrong version?")
            program_exit()


def main():
    print("--------------------------------")
    print("TeamViewer ID Changer for MAC OS")
    print("--------------------------------")

    username = check_system_type_and_current_user()
    home_dir_lib = '/Users/' + username + '/library/preferences/'

    get_team_viewer_configs(home_dir_lib)

    print("ID changed sucessfully.")
    print("!!! Restart computer before using TeamViewer !!!!")


if __name__ == '__main__':
    main()
