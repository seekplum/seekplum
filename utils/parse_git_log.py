#-*- coding: utf-8 -*-

from __future__ import print_function
import re

"""
通过 log 分析 git commit 命令
"""
# git log --name-only > test.txt 
with open("test.txt", "r") as f:
    content = f.read()
# 无 Change-Id
# pattern = re.compile(r'commit \w+\nAuthor: .*\nDate: .*\n\s+(.*)\s+\n([\S\n]+)\n', re.M)
pattern = re.compile(r'commit \w+\nAuthor: .*\nDate: .*\n\s+(.*)\s+\n\s+Change-Id: \w+\s*\n\s*\n([\S\n]+)\n', re.M)
result = pattern.findall(content)
for res in result[::-1]:
    message = res[0]
    files = " ".join(res[1].split("\n"))
    print('git commit {}-m "{}"'.format(files, message))

