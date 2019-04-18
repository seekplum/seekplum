#!/usr/bin/env python
# -*- coding: utf-8 -*-

import schema
from schema import Use
from schema import Optional, And, Or

try:
    # 判断是否为 int 类型数据
    result = schema.Schema(int).validate(12)
    print "result", result
except schema.SchemaError as e:
    # 验证失败则是抛出 SchemaError 异常
    print "异常：", str(e)

# 先进行转换在验证
use_result = schema.Schema(Use(int)).validate('123')
print "use_result", use_result

# 参数是容器类型
list_result = schema.Schema([1, 0]).validate([1, 1, 0, 0])
print "list_result", list_result

# 验证字段的key, value
dict_result = schema.Schema({'name': str, 'age': lambda n: 10 < n < 99}).validate({'name': 'abc', 'age': 14})
print "dict_result", dict_result

# 部分键值验证, 不用验证的部分写object即可
ret = schema.Schema({'name': str, str: object}).validate({'name': '0', 'aa': 'da'})

# Optional 可选： dd可以不存在，但存在必须是int类型
optional = schema.Schema({'name': str, Optional('dd'): int}).validate({'name': 'Sam', 'dd': 1})
print "optional", optional

and_result = schema.Schema({'age': And(int, lambda n: 0 < n < 100)}).validate({'age': 7})
print "and_result", and_result

or_result = schema.Schema(And(Or(int, float), lambda x: x > 0)).validate(3.6)
print "or_result", or_result
