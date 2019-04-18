#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import argparse

from bin.basic_parser import BasicParser
from conf import COMMAND_MEDIA


class RatioAction(argparse.Action):
    """check if the ratio is legal"""

    def __call__(self, parser, namespace, values, option_string=None):
        pattern = re.compile("(\d+)/(\d+)")
        match = pattern.search(values)
        if match:
            read = int(match.group(1))
            write = int(match.group(2))
            if (read + write) != 100:
                parser.error("the readcache pluse wirtecache is not equal 100")
        else:
            parser.error("the ratio is illegal, example: 0/100, 20/80, 30/70...")
        setattr(namespace, self.dest, values)


class TermMedia(BasicParser):
    """
    Media Tool
    """

    def __init__(self, prog=COMMAND_MEDIA):
        super(self.__class__, self).__init__(prog)
        self.subcommands = {}

    def get_subcommand_parser(self):
        parser = self.get_base_parser()
        subparsers = parser.add_subparsers(metavar="<subcommands>")

        # light_on
        parser_light_on = subparsers.add_parser("lighton",
                                                help="light on the disk in a slot")
        parser_light_on.add_argument("-s", "--slot",
                                     required=True,
                                     action="store",
                                     dest="slot",
                                     help="specify disk slot name"
                                     )
        parser_light_on.set_defaults(func=self.do_light_on)

        # light_off
        parser_light_off = subparsers.add_parser("lightoff",
                                                 help="light off the disk in a slot")
        parser_light_off.add_argument("-s", "--slot",
                                      required=True,
                                      action="store",
                                      dest="slot",
                                      help="specify disk slot name"
                                      )
        parser_light_off.set_defaults(func=self.do_light_off)

        # show_all
        parser_show = subparsers.add_parser("show",
                                            help="show all the disk/flash infomation")
        parser_show.set_defaults(func=self.do_show_all)

        # show_disk
        parser_show_disk = subparsers.add_parser("show_disk",
                                                 help="show the disk infomation")
        parser_show_disk.add_argument("-p", "--pdinfo",
                                      action="store_true",
                                      dest="pdisk_info",
                                      default=False,
                                      help="show the pyhiscs disks infomation")
        parser_show_disk.set_defaults(func=self.do_show_disk)

        # show flash
        parser_show_flash = subparsers.add_parser("show_flash",
                                                  help="show the flash infomation")
        parser_show_flash.set_defaults(func=self.do_show_flash)

        # attach_disk
        p = subparsers.add_parser("attach_disk",
                                  help="attach the disk in a slot from OS")
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("-s", "--slot",
                       required=False,
                       action="store",
                       dest="slot",
                       nargs="+",
                       help="slot name")
        p.add_argument("-c", "--cache",
                       required=False,
                       action="store_true",
                       dest="cache",
                       default=False,
                       help="enable cache")
        p.set_defaults(func=self.do_attach_disk)

        # detach_disk
        p = subparsers.add_parser("detach_disk",
                                  help="detach the disk in a slot from OS")
        p.add_argument("-f", "--force",
                       default=False,
                       required=False,
                       action="store_true",
                       dest="force",
                       help="force to detach disk")
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("-s", "--slot",
                       required=False,
                       action="store",
                       dest="slot",
                       nargs="+",
                       help="slot number")
        p.set_defaults(func=self.do_detach_disk)

        # mkpart
        parser_mkpart = subparsers.add_parser("mkpart",
                                              help="divide disk into equal parts if the volume is over 2T")
        parser_mkpart.add_argument("-d", "--disk",
                                   required=True,
                                   action="store",
                                   dest="disk",
                                   help="specify disk path"
                                   )
        parser_mkpart.add_argument("-n", "--num",
                                   required=False,
                                   action="store",
                                   type=int,
                                   dest="num",
                                   help="specify how many parts you want to make, default: each part less than 2TB"
                                   )
        parser_mkpart.add_argument("-l", "--log",
                                   required=False,
                                   action="store_true",
                                   dest="log",
                                   default=False,
                                   help="display the part disk log"
                                   )
        parser_mkpart.set_defaults(func=self.do_mkpart)

        # format_flash
        parser_format_flash = subparsers.add_parser("format_flash",
                                                    help="format flash disk")
        parser_format_flash.add_argument("-d", "--device",
                                         required=True,
                                         action="store",
                                         dest="device",
                                         help="specify flash device path"
                                         )
        parser_format_flash.add_argument("-b", "--block",
                                         required=False,
                                         action="store",
                                         dest="block",
                                         default=512,
                                         type=int,
                                         help="set the block size, default is 512"
                                         )
        parser_format_flash.set_defaults(func=self.do_format_flash)

        # set_cache
        p = subparsers.add_parser("set_cache", help="set the disk cache")
        g = p.add_mutually_exclusive_group(required=True)
        # 打开RAID卡写cache，即将写cache模式设置成WriteBack模式
        g.add_argument("--enable",
                       required=False,
                       action="store_true",
                       dest="enable",
                       default=False,
                       help="set write cache policy to WriteBack")
        # 关闭RAID卡写cache，即将写cache模式设置成WriteThrough模式
        g.add_argument("--disable",
                       required=False,
                       action="store_true",
                       dest="disable",
                       default=False,
                       help="set write cache policy to WriteThrough")

        p.add_argument("-s", "--slot",
                       required=True,
                       action="store",
                       dest="slot",
                       nargs="+",
                       help="specify slot name")

        p.set_defaults(func=self.do_set_cache)

        return parser

    def do_light_on(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_light_off(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_show_all(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_show_disk(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_show_flash(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_attach_disk(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_detach_disk(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_set_cache(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_mkpart(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def do_format_flash(self, arguments):
        result = sys._getframe(0).f_code.co_name
        print result, "arguments:", str(arguments)
        return result

    def main(self, argv):
        subcommand_parser = self.get_subcommand_parser()
        args = subcommand_parser.parse_args(argv)
        args.func(args)


# ================  test  =================
def test():
    test = TermMedia()
    argv = sys.argv[1:]
    # print argv
    test.main(argv)


if __name__ == "__main__":
    test()
