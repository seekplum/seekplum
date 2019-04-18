#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import glob
import os
from get_info.info_cluster import get_nodetype, get_serveritem, get_qlinkitem, get_extqlinkitem
from conf import COMMAND_CONF, COMMAND_MEDIA, COMMAND_QLINKADM
from prompt_toolkit.completion import Completer, Completion
from terminate.completer_path import PathCompleter
from terminate import settings


class QCompleter(Completer):
    def __init__(self, ignore_case=True, WORD=False, match_middle=False):
        super(self.__class__, self).__init__()
        self.node_type = get_nodetype()
        self.words = set()
        self.commands = set([COMMAND_CONF, COMMAND_MEDIA, COMMAND_QLINKADM, "help", ])
        self.commanddata = {
            COMMAND_CONF: set(
                ["add_host", "del_host", "import", "export", "create_cfile", "add_ext", "del_ext", "show", "sync",
                 "clear"]),
            COMMAND_MEDIA: set(
                ["lighton", "lightoff", "show", "show_flash", "show_disk", "attach_disk", "detach_disk", "mkpart",
                 "format_flash", "set_cache"]),
            COMMAND_QLINKADM: set(["show", ""]),
        }
        if self.node_type == "storage":
            self.commanddata[COMMAND_QLINKADM].update(
                ["add_target", "del_target", "add_lun", "del_lun", "set_acl", "start", "stop"])
        else:
            self.commanddata[COMMAND_QLINKADM].update(["load", "unload"])

        self.meta_dict = {}
        self.ignore_case = ignore_case
        self.WORD = None
        self.match_middle = match_middle
        self._path_completer_grammar_cache = None
        self._path_completer = PathCompleter()

    def set_meta_dict(self, command):
        info = getattr(settings, command, {})
        for sub_command, info_subcmd in info.iteritems():
            self.meta_dict[sub_command] = info_subcmd["desc"]

    def update(self, current_command=None):
        self.current_command = current_command

    def get_words(self, document):
        # set words belongs to the current_command
        self.words = set()
        current_command = self.current_command
        self.set_meta_dict(current_command)

        text = document.text_before_cursor
        if text.startswith("!"):
            return
        text_list = text.split()

        # when type nothing
        if not text_list:
            if current_command:  # such as conf
                info = getattr(settings, current_command, {})
                sub_commands = []  # add_ext, show
                for sub_command, sub_info in info.iteritems():
                    if self.node_type in sub_info["node"]:
                        sub_commands.append(sub_command)
                self.words = set(sub_commands)
            else:
                self.words = self.commands
            return

        # if the first word is new subcommand, update current_command
        text_0 = text_list[0]
        if text_0 != self.current_command and text_0 in self.commands:
            current_command = text_0  # such as conf
            self.set_meta_dict(current_command)

        # get the sub_command, such as add_host/del_host ...
        sub_commands = set()
        if current_command:
            info = getattr(settings, current_command, {})
            for sub_command, sub_info in info.iteritems():
                if self.node_type in sub_info["node"]:
                    sub_commands.add(sub_command)

        # set the self.words
        if len(text_list) == 1:  # at the begining
            self.words = sub_commands | self.commands  # add commands
            return
        elif len(text_list) > 1:
            self.words = set()
            if len(text_list) == 2:
                if current_command != self.current_command:
                    self.words = sub_commands  # such as add_ext/show
                    return
                else:
                    # add options
                    sub_command = text_list[0]
                    info = getattr(settings, current_command, {})  # node and items infomation
                    info_subcmd = info.get(sub_command)
                    options = []
                    if self.node_type in info_subcmd.get("node", []):
                        options_dict = info_subcmd.get("items", {})
                        for option, info_option in options_dict.iteritems():
                            if self.node_type in info_option[1].split("#"):  # '#'区分node type
                                options.append(option)
                                self.meta_dict[option] = info_option[0]
                    self.words = set(options) - set(text_list)
            else:  # text word >= 3
                # add options completer
                if current_command != self.current_command:
                    sub_command = text_list[1]
                else:
                    sub_command = text_list[0]  # add_host
                info = getattr(settings, current_command, {})  # node and items infomation
                info_subcmd = info.get(sub_command)
                options = []
                if self.node_type in info_subcmd.get("node", []):
                    options_dict = info_subcmd.get("items", {})
                    for option, info_option in options_dict.iteritems():
                        if self.node_type in info_option[1].split("#"):
                            options.append(option)
                            self.meta_dict[option] = info_option[0]
                self.words = set(options) - set(text_list)

                # add completer belongs to current option
                current_option = ""
                for option in reversed(text_list):
                    if option in options:
                        current_option = option  # -n
                        info_option = options_dict[option]  # ["hostname", "<hostname>"]
                        break
                if current_option:
                    try:
                        description = info_option[0]
                        if self.node_type in info_option[1].split("#"):
                            words_list = info_option[2:]
                        else:
                            words_list = []
                    except:
                        words_list = []
                    self.get_option_words(words_list)
                    return

    def get_option_words(self, words_list):
        # add /dev/qdisk/* if -s/--slot specified
        result = []
        for word in words_list:
            if word == "<ip>":  # get the ip from server table
                ip_list = get_serveritem(ip=True)
                result.extend(ip_list)
            elif word == "<hostname>":  # get hostname from server table
                host_list = get_serveritem(hostname=True)
                result.extend(host_list)
            elif word == "<target>":  # get target from qlink table
                target_list = get_qlinkitem()
                result.extend(target_list)
            elif word == "<ext_ip>":  # get the ip from external tabale
                ip_list = get_extqlinkitem(ip=True)
                result.extend(ip_list)
            elif word == "<ext_target>":  # get target from external table
                target_list = get_extqlinkitem(target=True)
                result.extend(target_list)
            elif word == "<ext_set>":
                result.extend(["YES", "NO"])
            else:
                result.append(word)
        self.words.update(result)

    def _complete_path_while_typing(self, document):
        try:
            text = document.text_before_cursor
            if text.startswith("!"):
                text = text[1:]
            path = text.split()[-1]
            if path.startswith(("./", "/", "~/")):
                return True
            else:
                return False
        except:
            return False

    def get_completions(self, document, complete_event):
        try:
            word_before_cursor = document.get_word_before_cursor(WORD=self.WORD)
            if self.ignore_case:
                word_before_cursor = word_before_cursor.lower()

            self.get_words(document)

            if complete_event.completion_requested and self._complete_path_while_typing(document):
                for c in self._path_completer.get_completions(document, complete_event):
                    yield c

            # match seekplummgr command
            def word_matches(word):
                """ True when the word before the cursor matches. """
                if self.match_middle:
                    return word_before_cursor in word
                else:
                    return word.startswith(word_before_cursor)

            for a in sorted(list(self.words)):
                if word_matches(a.lower()):
                    display_meta = self.meta_dict.get(a, '')
                    yield Completion(a, -len(word_before_cursor), display_meta=display_meta)
        except:
            pass
