# !/usr/bin/python
# -*- coding: utf-8 -*-

import os
import uuid
import time
import commands

import netifaces


def run_cmd(cmd):
    """执行系统命令
    """
    print cmd
    # os.system(cmd)
    return commands.getoutput(cmd)


def get_hostid():
    """通过UUID查询mac地址
    """
    mac_address = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_address = ":".join([mac_address[e:e + 2] for e in range(0, 11, 2)])
    return mac_address.strip()


def get_interfaces():
    """获取所有的网卡
    """
    interfaces = netifaces.interfaces()
    return filter(lambda x: x.startswith("en"), interfaces)


def close_network():
    """关闭网络
    """
    cmd = "sudo /System/Library/PrivateFrameworks/Apple80211.framework/Resources/airport -z"
    run_cmd(cmd)

    cmd = "networksetup -setairportpower en0 off"
    run_cmd(cmd)


def open_network():
    """打开网络
    """
    cmd = "networksetup -detectnewhardware"
    run_cmd(cmd)

    cmd = "networksetup -setairportpower en0 on"
    run_cmd(cmd)


def generate_mac_address():
    """生成mac地址

    需要在连网的情况下操作
    """
    cmd = "openssl rand -hex 6 | sed 's/\(..\)/\\1:/g; s/.$//'"
    return run_cmd(cmd)


def update_mac_address(interfaces, addresss):
    """更新网卡的 mac 地址
    """
    for i, interface in enumerate(interfaces):
        cmd = "sudo ifconfig %s ether %s" % (interface, addresss[i])
        run_cmd(cmd)


def main():
    print get_hostid()

    # 保证网络正常
    open_network()
    time.sleep(3)

    # 为每个网卡生成mac地址
    interfaces = get_interfaces()
    addresss = [generate_mac_address() for _ in interfaces]

    # 关闭网络
    close_network()
    time.sleep(3)

    # 修改mac地址
    update_mac_address(interfaces, addresss)

    # 重新连接网络
    time.sleep(3)
    open_network()
    print get_hostid()


if __name__ == '__main__':
    main()