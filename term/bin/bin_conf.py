#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import argparse

from bin.basic_parser import BasicParser
from conf import TERM_NAME
from conf import COMMAND_CONF
from conf import STO_TYPE, COM_TYPE, SANFREE_TYPE, Seekplum_DB_FILE
from manager.mgr_conf import ServerConfig, DiffFile
from model.table import *
from utils.printer import printer
from utils.log import error_logger
from utils.util import get_project_path


class WithGetAction(argparse.Action):
    """the arguments only used if the 'target' value is set"""

    def __call__(self, parser, namespace, values, option_string=None):
        target = getattr(namespace, 'get', False)
        if not target:
            parser.error("Only use {} if -g/--get is set!".format(option_string))
        else:
            setattr(namespace, self.dest, values)


class TermConf(BasicParser):
    """
    Config Tool
    """

    def __init__(self, prog=COMMAND_CONF):
        super(self.__class__, self).__init__(prog)
        self.cluster_info = ""
        self.subcommands = {}

    def get_subcommand_parser(self):
        parser = self.get_base_parser()

        subparsers = parser.add_subparsers(metavar="<subcommands>")

        # ======================================================================
        #              server config
        # ======================================================================
        # add_host
        parser_add_host = subparsers.add_parser("add_host",
                                                help="Add a host into the {} config".format(TERM_NAME))
        parser_add_host.add_argument("-i", "--ip",
                                     required=True,
                                     action="store",
                                     dest="ip",
                                     help="specify the server ip")
        parser_add_host.add_argument("-t", "--type",
                                     required=True,
                                     action="store",
                                     dest="type",
                                     choices=(COM_TYPE, STO_TYPE, SANFREE_TYPE),
                                     help="specify the server type")
        parser_add_host.set_defaults(func=self.do_add_host)

        # del_host
        parser_del_host = subparsers.add_parser("del_host",
                                                help="Delete a host from the {} config".format(TERM_NAME))
        group_del_host = parser_del_host.add_mutually_exclusive_group(required=True)
        group_del_host.add_argument("-n", "--name",
                                    action="store",
                                    dest="hostname",
                                    nargs="*",
                                    help="the name of the server, server1 server2 ..")
        group_del_host.add_argument("-i", "--ip",
                                    action="store",
                                    dest="ip",
                                    nargs="*",
                                    help="the ip of the server, ip1 ip2 ..")
        parser_del_host.set_defaults(func=self.do_del_host)

        # ======================================================================
        #              qlink config
        # ======================================================================
        # import yaml file
        parser_importfile = subparsers.add_parser("import",
                                                  help="Apply the yaml file into the {} config".format(TERM_NAME))
        group_importfile = parser_importfile.add_mutually_exclusive_group(required=True)
        parser_importfile.add_argument("-f", "--file",
                                       action="store",
                                       dest="file",
                                       default=None,
                                       help="specify the yaml file path")
        group_importfile.add_argument("-i", "--inner",
                                      action="store_true",
                                      default=False,
                                      dest="inner",
                                      help="import yaml file to inner config setting")
        group_importfile.add_argument("-e", "--external",
                                      action="store_true",
                                      default=False,
                                      dest="ext",
                                      help="import yaml file to external config setting")
        parser_importfile.set_defaults(func=self.do_import)

        # export yaml file
        parser_exportfile = subparsers.add_parser("export",
                                                  help="export {} config settings to a file".format(TERM_NAME))
        group_exportfile = parser_exportfile.add_mutually_exclusive_group(required=True)
        group_exportfile.add_argument("-i", "--inner",
                                      action="store_true",
                                      default=False,
                                      dest="inner",
                                      help="export inner targte config setting to a file")
        group_exportfile.add_argument("-e", "--external",
                                      action="store_true",
                                      default=False,
                                      dest="ext",
                                      help="export external config setting to a file")
        parser_exportfile.add_argument("-f", "--file",
                                       action="store",
                                       dest="file",
                                       default=None,
                                       help="specify the file path")
        parser_exportfile.set_defaults(func=self.do_export)

        # create_cfile
        parser_create_cfile = subparsers.add_parser("create_cfile",
                                                    help="create yaml config file from settings or default rules")
        group_create_cfile = parser_create_cfile.add_mutually_exclusive_group(required=True)
        group_create_cfile.add_argument("-i", "--inner",
                                        action="store_true",
                                        default=False,
                                        dest="inner",
                                        help="generate target config file by default rules")
        group_create_cfile.add_argument("-e", "--external",
                                        action="store_true",
                                        default=False,
                                        dest="ext",
                                        help="create external target config file example")
        parser_create_cfile.add_argument("-f", "--file",
                                         # metavar="in-file",
                                         action="store",
                                         dest="file",
                                         default=None,
                                         help="specify the file path")
        parser_create_cfile.set_defaults(func=self.do_create_cfile)

        # ======================================================================
        #              qlink external config
        # ======================================================================
        # add external
        parser_add_qlink_ext = subparsers.add_parser("add_ext",
                                                     help="add the external {} target".format(TERM_NAME))
        parser_add_qlink_ext.add_argument("-i", "--ip",
                                          required=True,
                                          action="store",
                                          dest="ip",
                                          help="specify ip address")
        parser_add_qlink_ext.add_argument("-p", "--port",
                                          required=True,
                                          action="store",
                                          dest="port",
                                          type=int,
                                          help="specify port")
        parser_add_qlink_ext.add_argument("-t", "--target",
                                          required=True,
                                          action="store",
                                          dest="target",
                                          help="specify target name")
        parser_add_qlink_ext.add_argument("-d", "--driver",
                                          action="store",
                                          dest="type",
                                          default="iser",
                                          help="specify type, default is 'iser'")
        parser_add_qlink_ext.set_defaults(func=self.do_add_qlink_ext)

        # delate external
        parser_del_qlink_ext = subparsers.add_parser("del_ext",
                                                     help="delete the external target")
        group_del_qlink_ext = parser_del_qlink_ext.add_mutually_exclusive_group(required=True)

        group_del_qlink_ext.add_argument("-i", "--ip",
                                         required=False,
                                         action="store",
                                         dest="ip",
                                         nargs="*",
                                         help="specify ip address")
        group_del_qlink_ext.add_argument("-t", "--target",
                                         action="store",
                                         dest="target",
                                         nargs="*",
                                         help="specify target")
        parser_del_qlink_ext.set_defaults(func=self.do_del_qlink_ext)

        # set external
        parser_set_qlink_ext = subparsers.add_parser("set_ext",
                                                     help="set the target external attribute")
        parser_set_qlink_ext.add_argument("-t", "--targe",
                                          required=True,
                                          action="store",
                                          dest="targetname",
                                          help="specify target name")
        parser_set_qlink_ext.add_argument("-e", "--external",
                                          required=True,
                                          action="store",
                                          dest="external",
                                          choices=("YES", "NO"),
                                          help="specify external type")
        parser_set_qlink_ext.set_defaults(func=self.do_set_qlink_ext)

        # diff file
        parser_diff_file = subparsers.add_parser("diff",
                                                 help="View the differences between two files")
        parser_diff_file.add_argument("-f", "--filename",
                                      required=True,
                                      action="store",
                                      nargs="+",
                                      dest="filename",
                                      help="specify file name")
        parser_diff_file.add_argument("-p", "--print",
                                      default=False,
                                      required=False,
                                      action="store_true",
                                      dest="output",
                                      help="print file info")
        parser_diff_file.set_defaults(func=self.do_diff_file)

        # ======================================================================
        #              conmmon config
        # ======================================================================
        # show
        parser_show = subparsers.add_parser("show",
                                            help="show the config settings")

        group_show = parser_show.add_mutually_exclusive_group(required=True)
        group_show.add_argument("-s", "--server",
                                action="store_true",
                                dest="server",
                                default=False,
                                help="show server settings", )
        group_show.add_argument("-t", "--target",
                                action="store_true",
                                dest="target",
                                default=False,
                                help="show target settings", )
        group_show.add_argument("-e", "--external",
                                action="store_true",
                                dest="external",
                                default=False,
                                help="show qlink external settings", )
        parser_show.set_defaults(func=self.do_show)

        # sync
        parser_sync = subparsers.add_parser("sync",
                                            help="sync the config settings to all the servers")
        parser_sync.add_argument("-g", "--get",
                                 action="store_true",
                                 dest="get",
                                 help="update configuer setting from cluster node", )
        parser_sync.add_argument("-i", "--ip",
                                 action=WithGetAction,
                                 dest="ip",
                                 help="specify ip address to get the config setting", )
        parser_sync.set_defaults(func=self.do_sync)

        # clear
        parser_clear = subparsers.add_parser("clear",
                                             help="clear the config settings")
        group_clear = parser_clear.add_mutually_exclusive_group(required=True)
        group_clear.add_argument("-s", "--server",
                                 dest="server",
                                 action="store_true",
                                 default=False,
                                 help="clear the server settings")
        group_clear.add_argument("-t", "--target",
                                 dest="qlink",
                                 action="store_true",
                                 default=False,
                                 help="clear the qlink settings")
        group_clear.add_argument("-e", "--external",
                                 dest="qlink_ext",
                                 action="store_true",
                                 default=False,
                                 help="clear the external qlink settings")
        parser_clear.set_defaults(func=self.do_clear)

        return parser

    # ==========================================================================
    #              server table
    # ==========================================================================
    def do_add_host(self, arguments):
        ip, seekplum_type = (arguments.ip, arguments.type)
        server_info = {
            "ip": ip,
            "type": seekplum_type
        }
        result = ServerConfig.update_or_insert(server_info)
        if result["success"]:
            printer.print_ok("Add {}".format(ip))
        else:
            printer.print_error("Add {}, {}".format(ip, result["message"]))
            error_logger.error(result["message"])
        return result

    def do_del_host(self, arguments):
        result = ServerConfig.delete_by_name_ip(arguments)
        if result:
            printer.print_ok("删除成功")
        else:
            printer.print_error("删除失败")

    # ==========================================================================
    #              qlink table
    # ==========================================================================
    def do_import(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_create_cfile(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_export(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    # ==========================================================================
    #              diff file
    # ==========================================================================
    def do_diff_file(self, arguments):
        files = arguments.filename
        output = arguments.output
        if len(files) != 2:
            printer.print_error("参数错误")
            return
        if output:
            DiffFile.print_file_info(files)
        else:
            DiffFile.check_file(files)

    # ==========================================================================
    #              qlink_ext table
    # ==========================================================================
    def do_add_qlink_ext(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_del_qlink_ext(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_set_qlink_ext(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    # ==========================================================================
    #              common
    # ==========================================================================
    def do_show(self, arguments):
        server = arguments.server
        target = arguments.target
        ext = arguments.external
        db_path = os.path.join(get_project_path(), Seekplum_DB_FILE)
        if not os.path.exists(db_path):
            return
        if server:
            ServerConfig.show()

    def do_sync(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_clear(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def main(self, argv):
        subcommand_parser = self.get_subcommand_parser()
        args = subcommand_parser.parse_args(argv)
        args.func(args)


# ================  test  =================
def test():
    test = TermConf()
    argv = sys.argv[1:]
    # print argv
    test.main(argv)


if __name__ == "__main__":
    test()
