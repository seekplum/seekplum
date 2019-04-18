#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import tempfile


def old():
    print "正常方法 开始创建临时文件..."
    filename = '%s.txt' % os.getpid()

    temp = open(filename, 'wb+')
    try:
        print "temp name: ", temp.name
        temp.write("123456789abc")
    finally:
        temp.close()
        os.remove(filename)


def temp_file():
    print "temp file 创建临时文件..."
    # TemporaryFile创建的临时文件没有文件名
    temp = tempfile.TemporaryFile()
    try:
        print "temp name:", temp.name
        temp.write('123456789abc')
        # 不用seek(N)无法读取数据: 从N开始往后读取
        temp.seek(0)
        print temp.read()
    finally:
        temp.close()


def temp_file_mode():
    print "temp file 以text模式运行"
    temp = tempfile.TemporaryFile(mode='w+t')
    try:
        temp.writelines(['first\n', 'second\n'])
        temp.seek(0)

        for line in temp:
            print "line:", line.rstrip()
    finally:
        temp.close()


def temp_file_name():
    print "创建有名字的临时文件..."
    # 创建后还是会自动删除
    temp = tempfile.NamedTemporaryFile()
    # 自己定义文件名格式 dir + prefix + random + suffix
    temp_name = tempfile.NamedTemporaryFile(suffix='_suffix', prefix='prefix_', dir='/tmp')
    try:
        print "temp name:", temp.name
        print "temp_name:", temp_name.name
    finally:
        temp.close()


def temp_file_dir():
    print "创建临时目录..."
    # 目录需要自己手动删除
    directory_name = tempfile.mkdtemp(suffix='_suffix', prefix='prefix_', dir='/tmp')
    print directory_name
    # os.removedirs(directory_name)


def temp_file_mktemp():
    print "返回临时文件的路径..."
    # 返回一个临时文件的路径，但并不创建该临时文件
    file_name = tempfile.mktemp(suffix='_suffix', prefix='prefix_')
    print file_name


def temp_file_mkstemp():
    print "创建需要手动删除的临时文件..."
    # 创建临时文件, 需要手动删除。 返回两个参数： 临时文件安全级别， 临时文件路径
    security_level, file_name = tempfile.mkstemp(suffix='_suffix', prefix='prefix_', dir='/tmp', text=False)
    print "安全级别：", security_level
    print "文件名：", file_name


if __name__ == '__main__':
    temp_file_mkstemp()
