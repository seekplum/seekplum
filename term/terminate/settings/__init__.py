#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import yaml
import os
import glob

current_path = os.path.dirname(os.path.abspath(__file__))
ThisModule = sys.modules[__name__]


def parser_yaml(file):
    with open(file) as f:
        text = f.read()
        return yaml.load(text)


def add_yaml(file_name):
    settings_file = os.path.join(current_path, file_name)
    settings = parser_yaml(settings_file)
    if not settings:
        return
    for k, v in settings.iteritems():
        try:
            if k.lower() != "verstion":
                getattr(ThisModule, k)
        except AttributeError:
            setattr(ThisModule, k, v)
        else:
            print "error: the key '%s' already in use!" % k


files = glob.glob(os.path.join(current_path, "*.yml"))
for file in files:
    add_yaml(file)
