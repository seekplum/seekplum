#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import yaml
import logging
from logging import config


def setup_logging(yaml_file=None, filename=None, title=None, default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration
    :param yaml_file: yaml配置文件
    :param filename: info文件名，路径默认在yaml中可以修改
    :param title: 开头标识
    :param default_level:
    :param env_key:
    :return:

    setup_logging(filename='info.log', title='seekplum')

    error_logger = logging.getLogger("seekplum.cloud")
    info_logger = logging.getLogger("seekplum") # title存在则和title相等，不存在则填写 seekplum.info

    error_logger.error("错误日志")
    info_logger.info("普通日志")
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    if not yaml_file:
        path = os.path.join(os.path.dirname(current_path), "settings", "logging.yaml")
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            conf = yaml.load(f.read())
        if filename:
            filename = os.path.join(conf['LOG_PATH'], filename)
            conf['handlers']['info_handler']['filename'] = filename
        if title:
            conf['loggers'][title] = conf['loggers_info']
        else:
            conf['loggers']['seekplum.info'] = conf['loggers_info']
        config.dictConfig(conf)
    else:
        logging.basicConfig(level=default_level)
