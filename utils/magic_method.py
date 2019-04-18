#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: magic_method
#         Desc: python魔法方法
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-05-30 14:45
#=============================================================================
"""


class Person(object):
    def __new__(cls, *args, **kwargs):
        """创建类实例的方法

        通常用于控制生成一个新实例的过程，属于类级别的方法

        主要场景在：
            重载__new__ 方法，实现特殊功能
            创建单例
        """
        print "__new__ called"
        # 必须要返回当前类的一个实例
        # 通过这个实例来调用 __init__ 方法，实例就是 __init__ 中的 self
        return super(Person, cls).__new__(cls, *args, **kwargs)

    def __init__(self, name, age):
        """在类实例创建之后调用进行初始化

        通常用于初始化一个新实例，控制初始化过程

        发生在类实例被创建以后，属于实例级别的方法
        """
        print "__init__ called"
        self.name = name
        self.age = age

    def __call__(self, *args, **kwargs):
        """把实例当成函数使用
        """
        print "call: args: {}, kwargs: {}".format(args, kwargs)

    def __str__(self):
        return "Person: {}({})".format(self.name, self.age)


def test():
    p = Person("hello", 10)
    print p
    p(1, 2, d=4)


if __name__ == '__main__':
    test()
