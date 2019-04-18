#!/usr/bin/env python
# -*- coding:utf-8 -*-

import itertools
import optparse
import os
import sys
import threading
import time
import zipfile
import logging
from log.logger import setup_logging

setup_logging(filename='words.txt', title='seekplum')
info_logger = logging.getLogger("seekplum")


def zip_file(start, end):
    """

    :param start:
    :param end:
    :return:
    """
    start_time = time.time()
    curr_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zfile = zipfile.ZipFile(os.path.join(curr_path, "zip.zip"))
    for i in range(start, end):
        try:
            zfile.extractall(pwd=str(i))
            all_time = time.time() - start_time
            print "用时：%s" % all_time
            sys.exit(0)
        except Exception as e:
            pass


def extract_file(zfile, password):
    """

    :param zfile:
    :param password:
    :return:
    """
    try:
        zfile.extractall(pwd=password)
        print "密码：", password
    except:
        pass


def iter_str():
    """
    组合暴力字典
    """
    upper_str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lower_str = upper_str.lower()
    number_str = "1234567890"
    special_str = "~!#$%^&*()_+-=[]{}\\,.?/';<>\""
    words = upper_str + lower_str + number_str + special_str
    length = len(words)
    threading_list = []
    for i in range(1, 17):
        t = threading.Thread(target=iter_product, args=(words, int(i)))
        threading_list.append(t)
    for t in threading_list:
        t.start()
    for t in threading_list:
        t.join()
    return


def iter_product(words, number):
    """
    根据words组合成number位 字符串
    :param words: 字符串
    :param number: 位数
    :return:
    """
    word_iter = itertools.product(words, repeat=number)
    for word in word_iter:
        word = "".join(word)
        info_logger.info("%s" % word)


def parser_test():
    parser = optparse.OptionParser("useage%Prog" + "-f <zipfile> -d <dictionary>")
    # 要解压的文件路径
    parser.add_option('-f', dest='zname', type="string", help="specify zip file")
    # 暴力破解密码文件
    parser.add_option('-d', dest='dname', type="string", help="specify dictionary file")
    (options, args) = parser.parse_args()
    if not options.zname or not options.dname:
        print parser.usage
        sys.exit(0)
    else:
        zname = options.zname
        dname = options.dname
    zfile = zipfile.ZipFile(zname)
    passfile = open(dname)
    for line in passfile.readlines():
        password = line.strip("\n")
        t = threading.Thread(target=extract_file, args=(zfile, password))
        t.start()


if __name__ == '__main__':
    print "start ..."
    start_time = time.time()
    iter_str()
    end_time = time.time()
    all_time = end_time - start_time
    with open("time.txt", "a") as f:
        f.write(str(all_time))
    f.close()
