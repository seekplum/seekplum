# -*- coding: utf-8 -*-
import sys
import json
from abc import ABCMeta, abstractmethod
from termcolor import colored
import conf
from utils import print_result
from utils import util
from utils.util import get_terminal_width


class ReturnTerminate(Exception):
    """
    通过异常直接返回到终端, 避免一层层函数return
    """
    def __init__(self, exit_code, message=None):
        super(ReturnTerminate, self).__init__()
        self.exit_code = exit_code
        self.message = message


class Formatter(object):

    title_flag = "="

    @classmethod
    def title(cls, message, length=120):
        color_format = {"color": "blue", "on_color": "on_white", "attrs": ["reverse"]}
        try:
            terminal_width = get_terminal_width()
        except Exception:
            terminal_width = length
        if terminal_width < length:
            length = terminal_width

        flag_count = (length - len(message)) / 2 - 1

        text = "{flag} {message} {flag}".format(
            flag=cls.title_flag * flag_count, message=message)
        colored_text = colored(text, **color_format)
        return colored_text


def get_printer(exit_code=True):
    if conf.API:
        return JsonPrinter(exit_code)
    else:
        return ShellPrinter(exit_code)


class Printer(object):
    """
    统一之后所有的终端输出必须通过该类, 在执行过程中根据具体终端环境还是api环境自动转换
    目前有很多老的输出方式, 以及程序有很多地方都依赖老的api输出的json结构,
    所以在完全完成输出切换以及程序调用前必须跟老的api输出结果一致
    """
    __metaclass__ = ABCMeta

    def __init__(self, exit_code):
        self.exit_code = exit_code

    @abstractmethod
    def print_info(self, message, **kwargs):
        pass

    @abstractmethod
    def print_warning(self, message):
        pass

    @abstractmethod
    def print_error(self, message):
        pass

    @abstractmethod
    def print_ok(self, message):
        pass

    @abstractmethod
    def exit(self, status, message=None):
        pass

    @abstractmethod
    def print_table(self,  *args, **kwargs):
        pass

    @abstractmethod
    def print_data(self, data, **kwargs):
        pass

    @abstractmethod
    def print_title(self, title, **kwargs):
        pass


class ShellPrinter(Printer):

    def print_info(self, message, **kwargs):
        if kwargs.get("color"):
            message = colored(message, kwargs["color"])
        if kwargs.get("blank"):
            if kwargs["blank"] == "top":
                message = "\n" + message
            elif kwargs["blank"] == "bottom":
                message = message + "\n"
            elif kwargs["blank"] == "both":
                message = "\n" + message + "\n"
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def print_warning(self, message):
        print_result.print_war(message)

    def print_error(self, message):
        print_result.print_err(message)

    def print_ok(self, message):
        print_result.print_ok(message)

    def exit(self, exit_code, message=None):
        raise ReturnTerminate(exit_code, message)

    def print_table(self, data, **kwargs):
        util.show(data, **kwargs)

    def print_data(self, data, **kwargs):
        util.show(data, **kwargs)

    def print_title(self, title, length=120, **kwargs):
        self.print_info(Formatter.title(title, length), **kwargs)

    def print_red(self, message):
        print_result.print_red(message)

    def print_green(self, message):
        print_result.print_green(message)

class JsonPrinter(Printer):

    exit_message_print = True

    def print_title(sekf, title, **kwargs):
        pass

    def print_info(self, message, **kwargs):
        pass

    def print_red(self, message):
        pass

    def print_green(self, message):
        pass

    def print_warning(self, message):
        data = json.dumps({
            "warning": message
        })
        sys.stdout.write(data)
        sys.stdout.write("\n")

    def print_error(self, message):
        data = json.dumps({
            "error": message
        })
        sys.stdout.write(data)
        sys.stdout.write("\n")

    def print_ok(self, message):
        data = json.dumps({
            "ok": message
        })
        sys.stdout.write(data)
        sys.stdout.write("\n")

    def exit(self, exit_code, message=None):
        if JsonPrinter.exit_message_print:
            data = json.dumps({
                "exit_code": exit_code,
                "message": message
            })
            sys.stdout.write(data)
            sys.stdout.write("\n")
            sys.stdout.flush()

        JsonPrinter.exit_message_print = True
        sys.exit(exit_code)

    def print_data(self, data, **kwargs):
        json_data = {
            "data": data
        }
        sys.stdout.write(json.dumps(json_data))
        sys.stdout.write("\n")
        sys.stdout.flush()

    def print_table(self,  data, **kwargs):
        data = util.list_to_jsonstr(data)
        sys.stdout.write(data)
        sys.stdout.write("\n")
        sys.stdout.flush()

        # 打印json后 不打印退出码信息, 防止json解析出错
        JsonPrinter.exit_message_print = False

printer = get_printer()
