#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import traceback


def log_traceback(ex, ex_traceback=None):
    """
    替代 logging.exception()，打印异常堆栈
    :param ex: 异常类信息
    :param ex_traceback: 异常类的traceback信息
    python 3中ex_traceback为空即可
    :return:
    """
    if not ex_traceback:
        ex_traceback = ex.__traceback__
    tb_lines = traceback.format_exception(ex.__class__, ex, ex_traceback)
    tb_text = "".join(tb_lines)
    print tb_text


def test():
    try:
        1 / 0
    except Exception as e:
        _, _, e_traceback = sys.exc_info()
        log_traceback(e, e_traceback)


if __name__ == '__main__':
    test()
