#!/usr/bin/env python
# -*- coding:utf-8 -*-

import shutil

# 复制文件，等于 cp
shutil.copyfile('/home/hjd/test/test.txt', '/home/hjd/test/test123.txt')
# 复制文件，等于 cp -p 把属性也一致复制过去
shutil.copy("/home/hjd/test/test.txt", '/home/hjd/test/test456.txt')
# 复制目录, 等于 cp -r
shutil.copytree("/home/hjd/test/a/", "/home/hjd/test/c")
# 删除目录， 等于 rm -rf
shutil.rmtree('/home/hjd/test/b')
# 文件重命名
shutil.move('/home/hjd/test/c', '/home/hjd/test/d')
