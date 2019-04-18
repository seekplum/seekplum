# -*- coding: utf-8 -*-
"""
加载当前文件夹中所有yaml文件
以文件名当作module访问，yaml文件内部数据当作字典访问
如：settings.cmd["conf"]["server"]
"""
import os
import sys
import glob
import yaml

settings_path = os.path.dirname(os.path.abspath(__file__))
project_path = os.path.dirname(settings_path)

_this_module = sys.modules[__name__]

for yaml_file in glob.glob(os.path.join(settings_path, "*.yaml")):
    try:
        yaml_config = yaml.load(file(yaml_file))
        _config_module = os.path.basename(yaml_file).rsplit(".", 1)[0]
        setattr(_this_module, _config_module, yaml_config)
    except IOError:
        print "yaml settings file open faild"
