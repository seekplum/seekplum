#!/usr/bin/env python
# -*- coding: utf-8 -*-

import conf
import re
import fcntl
import termios
import struct

from termcolor import colored


def get_terminal_width():
    h, w, hp, wp = struct.unpack('HHHH', fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))
    return w


def print_result(title, msg, state, color_format, title_len=20, msg_len=90, state_len=10):
    """
    input:
    title,msg,state are the string format
    color_format: a dict such as {"color":"red", "on_color": "green", "attrs":["reverse"]}
                  **color** means text color, it can be: grey red green
                  yellow blue magenta cyan white.
                  **on_color** means text background color, it can be: on_grey on_red
                  on_green on_yellow on_blue on_magenta on_cyan on_white.
                  **attrs** is the color attributes, it can be: bold dark underline
                  blink reverse concealed
    """
    terminal_with = get_terminal_width()
    total_len = title_len + msg_len + state_len
    if total_len > terminal_with:
        title_len = int(terminal_with * title_len / total_len)
        msg_len = int(terminal_with * msg_len / total_len)
        state_len = int(terminal_with * state_len / total_len)
    if not title and not msg:
        return
    if msg:
        msg = msg.replace("\n", " ")
    else:
        title_len += msg_len
    if title:
        info = title.ljust(title_len)
    else:
        info = ""
        msg_len += title_len
    cut_flag = False
    while len(msg) > 0:
        # the msg is less than msg_len
        if len(msg) <= msg_len and not cut_flag:
            info += msg.ljust(msg_len)
            break
        elif len(msg) <= msg_len and cut_flag:  # the last cut part
            info += ' '.ljust(title_len) + msg.ljust(msg_len)
            break
        elif len(msg) > msg_len:
            cut_index = 0
            if " " in msg:
                cut_index = msg[:msg_len].rindex(" ") + 1
            else:
                pattern1 = re.compile(r"[\W_]")
                pattern2 = re.compile(r"[\d]")
                end1 = [m.end() for m in pattern1.finditer(msg[:msg_len])]
                end2 = [m.end() for m in pattern2.finditer(msg[:msg_len])]
                if end1:
                    cut_index = end1[-1]
                if end2:
                    cut_index2 = end2[-1]
                    if msg[cut_index2 + 1].isalpha():
                        cut_index = cut_index2
                if cut_index == 0:
                    cut_index = msg_len
            if not cut_flag:  # first cut
                cut_flag = True
                cut = msg[:cut_index]
            else:
                cut = " " * title_len + msg[:cut_index]
            info += cut + "\n"
            msg = msg[cut_index:]

    if conf.API:
        color_format = {}
    colored_state = colored(state, **color_format)
    colored_info = info + colored_state.rjust(state_len)
    print colored_info


def print_white(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "white"}
    colore_msg = colored(msg, **color_format)
    print colore_msg


def print_red(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "red"}
    colore_msg = colored(msg, **color_format)
    print colore_msg


def print_green(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "green"}
    colore_msg = colored(msg, **color_format)
    print colore_msg


def print_yellow(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "yellow"}
    colore_msg = colored(msg, **color_format)
    print colore_msg


def print_err(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "red"}
    head = colored("[ ERROR ]", **color_format)
    body = "{}:{}".format(head, msg)
    print body


def print_failed(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "red"}
    head = colored("[ FAILED ]", **color_format)
    body = "{}:{}".format(head, msg)
    print body


def print_ok(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "green"}
    head = colored("[ OK ]", **color_format)
    body = "{}:{}".format(head, msg)
    print body


def print_war(msg):
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "yellow"}
    head = colored("[ WARNING ]", **color_format)
    body = "{}:{}".format(head, msg)
    print body


def print_title(title, length=120):
    terminal_with = get_terminal_width()
    length = length if length < terminal_with else terminal_with
    title = title.strip()
    # grey red green yellow blue magenta cyan white.
    if conf.API:
        color_format = {}
    else:
        color_format = {"color": "blue", "on_color": "on_white", "attrs": ["reverse"]}
    len_title = len(title)
    len_head = int((length - len_title - 2) / 2)
    text_head = "=" * len_head
    text_title = " {} ".format(title)
    text_tail = "=" * len_head
    text = text_head + text_title + text_tail
    colored_text = colored(text, **color_format)
    print colored_text


# ==============   test  ====================


def test():
    msg = "a" * 20 * 5 + "1.33" * 50 + "a" * 50
    color_format = {"color": "red", "on_color": "on_green", "attrs": ["blink"]}
    print_result("[test]", msg, "[OK]", color_format, msg_len=64)
    title = " check asm"
    print_title(title)


if __name__ == "__main__":
    test()
