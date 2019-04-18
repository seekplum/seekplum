#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import os
import re


def walk(paths):
    partitions = []
    for curr_path, _, files in os.walk(paths):
        print curr_path
        all_dev_list = files
        for dev in all_dev_list:
            result = re.search(r'(\w+p\d+$)', dev)
            # result = re.search(r'(?P<name>\w+p\d+$)', dev)  # 取值时用result.group(name)或者result.group(1)均可

            if result:
                partitions.append(dev)
    partitions.sort(key=lambda x: int(x.split("p")[-1]))
    print "\n".join(partitions)


def visit_dir(_, dir_name, names):
    for file_path in names:
        print os.path.join(dir_name, file_path)


def glob_glob(paths):
    slot_path = os.path.join(paths, slot)
    all_dev_string = os.path.join(paths, "{}p*".format(slot))
    all_dev_list = glob.glob(all_dev_string)
    print "all_dev_list", all_dev_list
    partitions = []
    for dev in all_dev_list:
        result = re.search(r'%sp\d+$' % slot_path, dev)
        if result:
            partitions.append(dev)
    print "partitions:", partitions
    partitions.sort(key=lambda x: int(x.split("p")[-1]))
    print "\n".join(partitions)


if __name__ == "__main__":
    abs_path = '/home/hjd/test/'
    slot = 'abc'
    walk(abs_path)
    glob_glob(abs_path)
    os.path.walk(abs_path, visit_dir, ())
