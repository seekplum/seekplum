#!/usr/bin/env python
# -*- coding: utf-8 -*-

import conf
from terminate.term_main_api import Terminate

if __name__ == '__main__':
    conf.API = True
    ter = Terminate()
    ter.main()
