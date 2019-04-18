#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: conftest
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-09-06 10:31
#=============================================================================
"""
import pytest


@pytest.fixture
def username():
    return 'username'
