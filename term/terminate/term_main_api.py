#!/usr/bin/env python
# -*- coding: utf-8 -*-

import conf
conf.API = True  # set global API

import sys

from bin.bin_conf import TermConf
from bin.bin_media import TermMedia
from conf import COMMAND_CONF
from conf import COMMAND_MEDIA
from conf import COMMAND_QLINKADM
from utils.print_result import print_red
from utils.log import error_logger, info_logger


class Terminate(object):

    def __init__(self):
        self.current_command = ""
        self.xterm = False
        self.at = ""
        self.func_hook = {}
        # command: class map
        self.cs_map = {
            COMMAND_CONF: TermConf,
            COMMAND_MEDIA: TermMedia,
            COMMAND_QLINKADM: TermAdmin,
        }

        # if not is_hp:
        #     self.cs_map[COMMAND_RAID] = RaidCli

    def get_run_function(self, command):
        if command in self.func_hook.keys():
            return self.func_hook[command]
        else:
            if command in self.cs_map.keys():
                obj = self.cs_map[command]()
                func = obj.main
                self.func_hook[command] = func
                return func

    def run_command_in_one(self):
        try:
            argv = sys.argv
            command = argv[1]
            length = len(argv)
            if command not in self.cs_map.keys():
                msg = "ERROR: invalid command format: {}".format(argv)
                print msg
                error_logger.error(msg)
                return
            sub_main = self.get_run_function(command)
            if length == 2:
                sub_main(["-h"])
            else:
                sub_main(argv[2:])
        except SystemExit:
            pass
        except:
            print_red("Invalid Operation...")
            info_logger.exception("exception")
            error_logger.exception("exception")

    def main(self):
        argv = sys.argv
        length = len(argv)
        if length > 2:
            self.run_command_in_one()
            return
        else:
            msg = "ERROR: invalid command format: {}".format(argv)
            print msg
            error_logger.error(msg)
