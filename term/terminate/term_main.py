#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import unicode_literals

import logging
import os
import sys

from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.history import FileHistory
from prompt_toolkit.filters import Always
from prompt_toolkit.interface import AbortAction
from terminate.completer import QCompleter
from terminate.style import QSTYLE, QSTYLE_NOCOLOR
from pygments.token import Token

from conf import TERM_HISTORY_FILE
from conf import COMMAND_CONF
from conf import COMMAND_MEDIA
from conf import COMMAND_QLINKADM
from conf import VERSION, TERM_NAME, COPYRIGHT
from utils.util import enter_shell
from utils.log import error_logger
from utils.print_result import print_result, print_red
from utils.util import get_project_path, run_cmd

from bin.bin_conf import TermConf
from bin.bin_media import TermMedia


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

        self.get_xterm()
        # 命令提示
        self.completer = QCompleter()

    def get_run_function(self, command, oneline=False):
        if command in self.func_hook.keys():
            return self.func_hook[command]
        else:
            if command in self.cs_map.keys():
                obj = self.cs_map[command]()
                func = obj.main
                self.func_hook[command] = func
                return func

    def get_xterm(self):
        try:
            result = run_cmd("echo $TERM").strip()
            if "xterm" in result.lower():
                self.xterm = True
        except:
            pass

    def help(self):
        print "{} subcommand includes:\n".format(TERM_NAME)
        for command, klass in self.cs_map.iteritems():
            help_doc = klass.__doc__
            print_result(command, help_doc, "", {}, msg_len=50)

    def get_prompt_tokens(self, cli):
        return [
            (Token.Username, TERM_NAME),
            (Token.At, self.at),
            (Token.Host, self.current_command),
            (Token.Pound, '> '),
        ]

    def run_command(self, command, args_list):
        func = self.get_run_function(command)
        func(args_list)

    def run_command_in_one(self):
        try:
            argv = sys.argv
            command = argv[1]
            length = len(argv)
            if command not in self.cs_map.keys() and command:
                self.help()
                return
            sub_main = self.get_run_function(command, oneline=True)
            if length == 2:
                sub_main(["-h"])
            else:
                sub_main(argv[2:])
        except SystemExit:
            pass
        except Exception as e:
            print_red("Invalid Operation...")
            error_logger.exception("exception")

    def main(self):
        introduction = "{term}(version {version})\nType \"help\", \"copyright\" for more information.\n{copyright}".format(
            term=TERM_NAME, version=VERSION, copyright=COPYRIGHT)
        argv = sys.argv
        length = len(argv)
        if length >= 2:
            subcommand = argv[1]
            subcommand_list = self.cs_map.keys()
            if subcommand in subcommand_list and length == 2:
                self.current_command = argv[1].strip()
                self.completer.update(self.current_command)
                self.at = "@"
            elif subcommand in subcommand_list and length > 2:
                self.run_command_in_one()
                return
            else:
                print_red("Unrecognized command '{}'".format(subcommand))
                return
        print introduction
        # history = InMemoryHistory()
        project_path = get_project_path()
        history_file = os.path.join(project_path, TERM_HISTORY_FILE)
        history = FileHistory(history_file)

        while True:
            try:
                self.completer.update(self.current_command)
                if self.xterm:
                    text = get_input(
                        completer=self.completer,
                        get_prompt_tokens=self.get_prompt_tokens,
                        style=QSTYLE,
                        history=history,
                        enable_history_search=Always(),
                        on_abort=AbortAction.RETRY,
                        display_completions_in_columns=True,
                    )
                else:
                    text = get_input(
                        get_prompt_tokens=self.get_prompt_tokens,
                        history=history,
                        style=QSTYLE_NOCOLOR,
                        enable_history_search=Always(),
                        on_abort=AbortAction.RETRY,
                        display_completions_in_columns=True,
                    )

                text = text.strip()
                if not text:
                    continue

                # print help when type "help" or "?" or "h"
                if text in ["help", "?", "h"]:
                    if not self.current_command:
                        self.help()
                    else:
                        self.run_command(self.current_command, ["-h"])

                # print "exit/quite" to exit the current command or exit
                elif text in ["exit", "quite"]:
                    if self.current_command:
                        self.current_command = ""
                        self.at = ""
                        continue
                    else:
                        break

                # print version
                elif text in ["version", "v"]:
                    print "{}({})".format(TERM_NAME, VERSION)
                    continue

                # copyright
                elif text == "copyright":
                    print COPYRIGHT
                    continue

                # run cmd
                elif text.startswith("!"):
                    # ssh在本地执行命令
                    enter_shell(text[1:])
                    continue

                else:
                    # get the command
                    text_list = text.split()
                    command = text_list[0]

                    if len(text_list) == 1 and command in self.cs_map.keys():
                        self.current_command = command
                        self.at = "@"
                        continue

                    # new subcommand
                    elif command in self.cs_map.keys() and len(text_list) > 1:
                        if text_list[-1] == "?":
                            self.run_command(command, ["-h"])
                        elif text_list[-1] != "?":
                            self.run_command(command, text_list[1:])
                        continue
                    else:
                        # use old subcommand
                        if self.current_command:
                            if text_list[-1] == "?":
                                self.run_command(self.current_command, [command, "-h"])
                            else:
                                self.run_command(self.current_command, text_list)
                        # unknow subcommand
                        else:
                            print_red("Unrecognized command '{}'".format(text))
            except SystemExit:
                continue
            except EOFError:
                break
            except KeyboardInterrupt:
                error_logger.exception("exception operation cancel")
                print_red("Operation cancelled!")
            except Exception as e:
                logging.error(e.message)
                print_red("Invalid Operation...")
                error_logger.exception("exception")
