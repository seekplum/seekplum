#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
project name: seekplum
file name: mgr_conf
author: hjd
create time:  2017-03-31 20:12

┏┓ ┏┓
┏┛┻━━━┛┻┓
┃ ☃ ┃
┃ ┳┛ ┗┳ ┃
┃ ┻ ┃
┗━┓ ┏━┛
┃ ┗━━━┓
┃ 神兽保佑 ┣┓
┃　永无BUG ┏┛
┗┓┓┏━┳┓┏┛
┃┫┫ ┃┫┫
┗┻┛ ┗┻┛
"""
import copy
import random
import uuid

import conf
from conf import return_format
from model import db
from model.table import Server

from utils.printer import printer
from utils import util
from utils import print_result


class ServerConfig(object):
    @classmethod
    def get_server_list(cls):
        with db.open_session() as session:
            return session.query(Server).all()

    @classmethod
    def update_or_insert(cls, params):
        result = copy.copy(return_format)
        try:
            with db.open_session() as session:
                # 获取cluster_uuid
                cluster_uuid = uuid.uuid4().hex
                params["cluster_uuid"] = cluster_uuid
                params["ibcard_ip"] = str(["10.10.10.10"])
                params["name"] = random.randint(1, 10)
                node_id = random.randint(1, 100)
                params["id"] = node_id
                # 检测是否有相同的node_id
                same_id_server_obj = session.query(Server).filter_by(id=node_id, type=params["type"]).first()
                if same_id_server_obj:
                    result["success"] = False
                    result["message"] = "Node ID conflicts! The ID "
                    return result
                server = Server(**params)
                session.merge(server)
            result["success"] = True
        except Exception as e:
            result["message"] = e
        return result

    @classmethod
    def delete_by_name_ip(cls, arguments):
        ip = arguments.ip
        server_name = arguments.hostname
        try:
            with db.open_session() as session:
                if server_name:
                    record = session.query(Server).filter(Server.name.in_(server_name)).one()
                else:
                    record = session.query(Server).filter(Server.ip.in_(ip)).one()
                session.delete(record)
            return True
        except Exception as e:
            printer.print_error(e.message)
            return False

    @classmethod
    def show(cls):
        """
        Show server info.
        """
        head_list = Server.table_columns()
        if not conf.API:
            head_list.remove("cluster_uuid")
        server_list = ServerConfig.get_server_list()
        show_list = [head_list]
        for server in server_list:
            if conf.API:
                server.ibcard_ip = server.ibcard_ip.split(",")
            else:
                server.ibcard_ip = "\n".join(str(server.ibcard_ip).split(","))

            item_list = []
            for item in head_list:
                item_list.append(server[item])
            show_list.append(item_list)

        if conf.API:
            show_list = util.stringit(show_list)
            print util.list_to_jsonstr(show_list)
        else:
            util.show(show_list, net=True)


class DiffFile(object):
    @classmethod
    def get_base_info(cls, files, param):
        default_file = files[0]
        diff_file = files[1]
        cmd = "diff {} {} {}".format(diff_file, default_file, param)
        result = util.run_cmd(cmd)
        return result

    @classmethod
    def print_file_info(cls, files):
        param = "-u"
        try:
            result = cls.get_base_info(files, param)
            if not result:
                print_result.print_green("两个文件一样")
        except util.RunCMDError as e:
            output = e.message
            result = output.splitlines()
            default_info = " ".join(result[0].split(" ")[1:])
            diff_info = " ".join(result[1].split(" ")[1:])
            result_info = result[3:]
            print_result.print_white("diff {} {}".format(files[0], files[1]))
            print_result.print_white(default_info)
            print_result.print_white(diff_info)
            for info in result_info:
                if info.startswith("+"):
                    print_result.print_green(info)
                elif info.startswith("-"):
                    print_result.print_red(info)
                elif info.startswith("?"):
                    print_result.print_yellow(info)
                elif info.startswith(" "):
                    print info
                else:
                    print info

    @classmethod
    def check_file(cls, files):
        param = "-q"
        try:
            result = cls.get_base_info(files, param)
            if not result:
                print_result.print_green("两个文件一样")
        except util.RunCMDError as e:
            result = e.message
            if "differ" in result or "不同" in result:
                print_result.print_green(result)
            else:
                print_result.print_red(result)
