#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import yaml
import os
import glob

from term import *

current_path = os.path.dirname(os.path.abspath(__file__))
ThisModule = sys.modules[__name__]


def parser_yaml(file):
    with open(file) as f:
        text = f.read()
        return yaml.load(text)


def add_yaml(file_name):
    settings_file = os.path.join(current_path, file_name)
    settings = parser_yaml(settings_file)
    # import pprint
    # pprint.pprint(settings)
    if not settings:
        return
    for k, v in settings.iteritems():
        # print "conf[%s]:%s" % (k, v)
        try:
            if k.lower() != "verstion":
                getattr(ThisModule, k)
        except AttributeError:
            setattr(ThisModule, k, v)
        else:
            print "the key '{}' already in use!".format(k)


files = glob.glob(os.path.join(current_path, "*.yml"))
for file in files:
    add_yaml(file)
