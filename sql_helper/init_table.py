#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 不导入无法创建表
from base import *
from seekplum import *
import logging

if __name__ == '__main__':
    try:
        # 删除所有表
        drop_all_table()
        # 创建所有表
        create_all_table()
        logging.info("init table success")
    except Exception as e:
        logging.error(e)
