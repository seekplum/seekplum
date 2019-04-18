#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from log import setup_logging

setup_logging(filename='info.log', title='seekplum')


error_logger = logging.getLogger("seekplum.cloud")
info_logger = logging.getLogger("seekplum")

error_logger.error("error error")
info_logger.info('info info')
