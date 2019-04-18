#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
import functools

from conf import COMMAND_QLINKADM
from conf import COM_TYPE
from conf import STO_TYPE
from conf import SANFREE_TYPE
from bin.basic_parser import BasicParser


def check_node_type(*node_types):
    """
    Check the node type
    """

    def _wrap(func):
        @functools.wraps(func)
        def _handle(*args, **kwargs):
            node_type = "compute"
            if node_type not in node_types:
                print "Only run on {} node, current type: {}".format("/".join(node_types).lower(), node_type)

            return func(*args, **kwargs)

        return _handle

    return _wrap


class PositiveIntAction(argparse.Action):
    """check if the target is larger than zero"""

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class NetworkAction(argparse.Action):
    """check if the target is larger than zero"""

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class WithTargetAction(argparse.Action):
    """the arguments only used if the 'target' value is set"""

    def __call__(self, parser, namespace, values, option_string=None):
        pass


class TermAdmin(BasicParser):
    """
    Qlink Admin Tool
    """

    def __init__(self, prog=COMMAND_QLINKADM):
        super(self.__class__, self).__init__(prog)

    def get_subcommand_parser(self):
        parser = self.get_base_parser()
        subparsers = parser.add_subparsers(metavar="<subcommands>")

        # show
        parser_show = subparsers.add_parser("show",
                                            help="show online target info")
        group_show = parser_show.add_mutually_exclusive_group(required=True)
        group_show.add_argument("-t", "--target",
                                required=False,
                                action="store_true",
                                dest="target",
                                default=False,
                                help="[sto]show target information")
        group_show.add_argument("-q", "--qlink",
                                required=False,
                                action="store_true",
                                dest="qlink",
                                default=False,
                                help="[sto]show running qlink")
        parser_show.add_argument("-p", "--port",
                                 required=False,
                                 action=WithTargetAction,
                                 dest="port",
                                 type=int,
                                 help="[sto]specify qlink port for target show")
        group_show.add_argument("-c", "--compute",
                                required=False,
                                action="store_true",
                                dest="compute_show",
                                default=False,
                                help="[com]show the loaded disk on computer node")

        parser_show.add_argument("-s", "--server",
                                 required=False,
                                 action="store",
                                 dest="server",
                                 help="[com]only show the targets info on storage server")

        parser_show.add_argument("-m", "--more",
                                 required=False,
                                 action="store_true",
                                 dest="more",
                                 default=False,
                                 help="show with more")

        parser_show.set_defaults(func=self.do_show)

        # load
        parser_load_target = subparsers.add_parser("load",
                                                   help="[com]load target on computer node")
        parser_load_target.add_argument("-t", "--target",
                                        required=False,
                                        dest="target",
                                        action="store",
                                        nargs="*",
                                        help="[com]specify target name", )

        parser_load_target.add_argument("-i", "--ip",
                                        required=False,
                                        dest="ip",
                                        action="store",
                                        help="specify the ip of ib card", )
        parser_load_target.add_argument("-p", "--port",
                                        required=False,
                                        type=int,
                                        dest="port",
                                        action="store",
                                        help="specify the port", )
        parser_load_target.add_argument("-s", "--server",
                                        required=False,
                                        dest="storage",
                                        action="store",
                                        help="specify the storage server", )
        parser_load_target.add_argument("-r", "--rescan",
                                        required=False,
                                        dest="rescan",
                                        action="store_true",
                                        default=False,
                                        help="rescan if already loaded.")
        parser_load_target.set_defaults(func=self.do_load_target)

        # unload
        parser_unload_target = subparsers.add_parser("unload",
                                                     help="[com]unload a target on computer node")
        parser_unload_target.add_argument("-t", "--target",
                                          required=False,
                                          dest="target",
                                          action="store",
                                          nargs="*",
                                          help="specify target", )
        parser_unload_target.add_argument("-i", "--ip",
                                          required=False,
                                          dest="ip",
                                          action="store",
                                          help="specify the ip of ib card", )
        parser_unload_target.add_argument("-p", "--port",
                                          required=False,
                                          type=int,
                                          dest="port",
                                          action="store",
                                          help="specify the port", )
        parser_unload_target.add_argument("-s", "--server",
                                          required=False,
                                          dest="storage",
                                          action="store",
                                          help="specify the storage server", )
        parser_unload_target.set_defaults(func=self.do_unload_target)

        # add_target
        parser_add_target = subparsers.add_parser("add_target",
                                                  help="[sto]add a target to qlink")
        parser_add_target.add_argument("-p", "--port",
                                       required=True,
                                       action="store",
                                       dest="port",
                                       default=3261,
                                       type=int,
                                       help="specify qlink port, default is 3261")
        parser_add_target.add_argument("-d", "--driver",
                                       required=False,
                                       action="store",
                                       dest="driver",
                                       default="iser",
                                       choices=("iser", "iscsi"),
                                       help="specify iscsi or iser")
        parser_add_target.add_argument("-e", "--external",
                                       action="store_true",
                                       dest="ext",
                                       default=False,
                                       help="specify the target used for external cluster")
        parser_add_target.set_defaults(func=self.do_add_target)

        # del_target
        parser_del_target = subparsers.add_parser("del_target",
                                                  help="[sto]delete a target to qlink")
        parser_del_target.add_argument("-p", "--port",
                                       required=True,
                                       dest="port",
                                       type=int,
                                       help="Specifies qlink admin port",
                                       )
        group_del_target = parser_del_target.add_mutually_exclusive_group(required=True)
        group_del_target.add_argument("-t", "--tid",
                                      required=False,
                                      dest="tid",
                                      type=int,
                                      action=PositiveIntAction,
                                      help="specify target id")
        group_del_target.add_argument("-n", "--name",
                                      required=False,
                                      dest="tname",
                                      action="store",
                                      help="specify target name")
        parser_del_target.set_defaults(func=self.do_del_target)

        # add_lun
        parser_add_lun = subparsers.add_parser("add_lun",
                                               help="[sto]add a lun to a target in qlink")
        parser_add_lun.add_argument("-p", "--port",
                                    required=True,
                                    dest="port",
                                    type=int,
                                    help="Specify qlink port",
                                    )
        parser_add_lun.add_argument("-t", "--tid",
                                    required=True,
                                    dest="tid",
                                    type=int,
                                    action=PositiveIntAction,
                                    help="Specify target id")
        parser_add_lun.add_argument("-b", "--blockdev",
                                    required=True,
                                    action="store",
                                    dest="path",
                                    nargs="*",
                                    help="Specify block device path, such as /dev/qdisk/PXBXXSXX"
                                    )
        parser_add_lun.set_defaults(func=self.do_add_lun)

        # del_lun
        parser_del_lun = subparsers.add_parser("del_lun",
                                               help="[sto]delete a lun from a target in qlink")
        parser_del_lun.add_argument("-p", "--port",
                                    required=True,
                                    dest="port",
                                    type=int,
                                    help="Specifies qlink admin port",
                                    )
        parser_del_lun.add_argument("-t", "--tid",
                                    required=True,
                                    dest="tid",
                                    type=int,
                                    action=PositiveIntAction,
                                    help="specify target id")
        parser_del_lun.add_argument("-b", "--blockdev",
                                    required=True,
                                    action="store",
                                    dest="path",
                                    nargs="*",
                                    help="Specify block device path, such as /dev/qdisk/QXBXXSXX"
                                    )
        parser_del_lun.set_defaults(func=self.do_del_lun)

        # set_acl
        parser_set_acl = subparsers.add_parser("set_acl",
                                               help="[sto]set a acl to a target")
        parser_set_acl.add_argument("-p", "--port",
                                    required=True,
                                    dest="port",
                                    type=int,
                                    help="Specifies qlink admin port",
                                    )
        parser_set_acl.add_argument("-t", "--tid",
                                    required=True,
                                    dest="tid",
                                    type=int,
                                    action=PositiveIntAction,
                                    help="specify target id")
        parser_set_acl.add_argument("-a", "--address",
                                    default=["172.16.128.0/24", "172.16.129.0/24"],
                                    dest="address",
                                    nargs="*",
                                    action=NetworkAction,
                                    help="specify a address for ACL, default is empty")
        parser_set_acl.set_defaults(func=self.do_set_acl)

        # start_qlink
        parser_start_qlink = subparsers.add_parser("start",
                                                   help="[sto]start qlink")
        group_start_qlink = parser_start_qlink.add_mutually_exclusive_group(required=True)
        group_start_qlink.add_argument("-p", "--port",
                                       required=False,
                                       dest="port",
                                       type=int,
                                       action=PositiveIntAction,
                                       help="specify a port on current node")
        group_start_qlink.add_argument("-a", "--all",
                                       required=False,
                                       dest="all_",
                                       action="store_true",
                                       default=False,
                                       help="start qlink on all ports"
                                       )
        parser_start_qlink.set_defaults(func=self.do_start_qlink)

        # stop_qlink
        parser_stop_qlink = subparsers.add_parser("stop",
                                                  help="[sto]stop qlink")
        group_stop_qlink = parser_stop_qlink.add_mutually_exclusive_group(required=True)
        group_stop_qlink.add_argument("-p", "--port",
                                      required=False,
                                      dest="port",
                                      type=int,
                                      action=PositiveIntAction,
                                      help="specify a port on curren node")
        group_stop_qlink.add_argument("-a", "--all",
                                      required=False,
                                      dest="all_",
                                      action="store_true",
                                      default=False,
                                      help="stop qlink on all ports"
                                      )
        parser_stop_qlink.set_defaults(func=self.do_stop_qlink)

        return parser

    def do_show(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(COM_TYPE, SANFREE_TYPE)
    def do_load_target(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(COM_TYPE, SANFREE_TYPE)
    def do_unload_target(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_add_target(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_del_target(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_add_lun(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_del_lun(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_set_acl(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_start_qlink(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    @check_node_type(STO_TYPE, SANFREE_TYPE)
    def do_stop_qlink(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def main(self, argv):
        subcommand_parser = self.get_subcommand_parser()
        args = subcommand_parser.parse_args(argv)
        args.func(args)


def test():
    test = TermAdmin()
    argv = sys.argv[1:]
    # print argv
    test.main(argv)


if __name__ == "__main__":
    test()
