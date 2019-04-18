#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: test_something
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-09-06 10:44
#=============================================================================
"""


def teardown_function():
    print "{0} start {0}".format("=" * 50)
    yield
    print "{0} end {0}".format("-" * 50)


def test_username(username):
    assert username == 'username'
