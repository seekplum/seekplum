#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: gen_ts
#         Desc: 自动生成前端sdk
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-02-25 22:11
#=============================================================================
"""

import os
import json
import sys
import shutil
import logging

from marshmallow import validate, ValidationError
from marshmallow.utils import _Missing
from marshmallow_enum import EnumField

from schemas import Nested

from schemas import BaseResponse
from schemas import BaseApiSchema

from user_schema import *


# logger = logging.getLogger(__name__)


class SchemaMissingError(Exception):
    pass


class SchemaExampleError(Exception):
    pass


def generate_ts_name(name):
    return "{name}.d.ts".format(name=name)


def generate_array_type(type_):
    return "Array<{type}>".format(type=type_)


def is_handler_schema(sma):
    cls_name = sma.__class__.__name__
    if cls_name.startswith("ApiRequest") or cls_name.startswith("ApiResponse"):
        return True
    return False


def write_common_import_in_header(file_path):
    if os.path.basename(file_path) not in [generate_ts_name("common"), generate_ts_name("enum")] and not os.path.exists(
            file_path):
        with open(file_path, "w+") as f:
            f.write("import * as common from './common'\n\n")


def generate_request_ts(class_name, example):
    return "/* {class_name} Request Example: \n{example}\n */\n\n".format(class_name=class_name, example=example)


def generate_response_ts(class_name, example):
    return "/* {class_name} Response example: \n{example}\n */\n\n".format(class_name=class_name, example=example)


def check_variable(module_name, class_name, field):
    variables = ["example", "description"]
    for variable in variables:
        if variable not in field.metadata:
            raise SchemaMissingError("{module_name}.{class_name} 中 {column} 缺少 {variable} 属性".format(
                module_name=module_name, class_name=class_name, column=field.name, variable=variable))


def parser_ts_name(module_name):
    # return ".".join(module_name.split(".", 1)[1:])
    return module_name


class Generate(object):
    # 防止ts中的类重复定义
    _generated_names = set()

    def __init__(self, sma, ts_root):
        self._pre_count = 1
        self._ts_root = ts_root
        self._sma = sma

        self._sma_set = set()
        self._field_enum_set = set()

        # TODO: 待支持更多类型
        self._map_ts_type = {
            "String": "string",
            "Boolean": "boolean",
            "Integer": "number"
        }

    def _generate(self, _sma):
        class_name = _sma.__class__.__name__

        if class_name in self._generated_names:
            logging.warning("class name: {class_name} is exists".format(class_name=class_name))
            return None
        attributes = [
            "{retract}{name}{optional}: {type}; {description}".format(
                retract="\t" * self._pre_count,
                name=name,
                type=self._get_type(_sma, field),
                optional="" if field.required else "?",  # 标识可选类型
                description=self._generate_description(_sma, class_name, field)
            ) for name, field in _sma.fields.iteritems()
        ]
        context = "{{ {description}\n{attribute}\n}}\n".format(
            description="/* {description} */".format(description=_sma.__description__()),
            attribute="\n".join(attributes))
        self._generated_names.add(class_name)
        return context

    def _get_optional(self, field):
        if field.required:
            optional = ""
        else:
            optional = "参数可选, 默认值为: {default}".format(
                default=json.dumps(field.default, indent=4) if field.default else '""')
        return optional

    def _get_description(self, field):
        return "/* {description}, 示例: {example} {optional} */".format(
            description=field.metadata["description"],
            example=field.metadata["example"],
            optional=self._get_optional(field)
        )

    def _generate_description(self, sma, class_name, field):
        """生成描述信息，注释"""
        module_name = sma.__class__.__module__
        if not field.required and \
                (isinstance(field.default, _Missing) or field.default is None) and \
                not isinstance(sma, BaseResponse):
            raise SchemaMissingError("{module_name}.{class_name} 中 参数 {column} 是可选的，但缺少默认值".format(
                module_name=module_name, class_name=class_name, column=field.name))
        optional = self._get_optional(field)
        if isinstance(field, Nested):
            return "/* 见定义处, {optional} */".format(optional=optional)

        check_variable(module_name, class_name, field)
        return self._get_description(field)

    def _conversion_type(self, field):
        """python类型转换为ts类型
        """
        py_type = field.__class__.__name__

        # 指定type优先级最高
        if "type" in field.metadata:
            return field.metadata["type"]

        if py_type == "List":
            list_type = field.container.__class__.__name__
            return generate_array_type(self._map_ts_type[list_type])

        return self._map_ts_type[py_type]

    def _get_type(self, sma, field):
        if isinstance(field, Nested):
            self._sma_set.add(field.schema)
            class_name = field.schema.__class__.__name__

            if is_handler_schema(sma):
                type_name = "common.{class_name}".format(class_name=class_name)
            else:
                type_name = class_name

            # 数组类型
            if field.many:
                return generate_array_type(type_name)
            return type_name
        elif isinstance(field, EnumField):
            self._field_enum_set.add(field)
            enum_name = field.enum.__name__
            type_name = "en.{enum_name}".format(enum_name=enum_name)
            return type_name
        elif isinstance(field.validate, validate.OneOf):
            return " | ".join(map(lambda x: '"%s"' % x, field.validate.choices))

        return self._conversion_type(field)

    def _generate_api_info(self):
        """生成api信息"""
        message = "* description: {description}\n* method: {method}\n* url: {url}".format(
            description=self._sma.__description__(),
            method=self._sma.__method__(),
            url=self._sma.__url__())
        module_name = self._sma.__class__.__module__
        return generate_ts_name(parser_ts_name(module_name)), "/*\n{msg}\n*/\n".format(msg=message)

    def _generate_ts(self, sma, func):
        """生成请求参数ts文件"""
        # 校验schema类型
        if not isinstance(sma, BaseLocalSchema):
            return
        self._sma_set.add(sma)
        while self._sma_set:
            _sma = self._sma_set.pop()
            context = self._generate(_sma)
            if not context:
                continue

            class_name = _sma.__class__.__name__
            module_name = _sma.__class__.__module__
            if not is_handler_schema(_sma):
                file_name = generate_ts_name("common")
            else:
                file_name = generate_ts_name(parser_ts_name(module_name))

            try:
                _, err = _sma.load(_sma.__example__())
                if err:
                    raise SchemaExampleError(
                        "{module_name}.{class_name} 中__example__方法返回值时错误的，错误详情: {error_msg}".format(
                            module_name=module_name, class_name=class_name,
                            error_msg=", ".join(["{}: {}".format(k, v) for k, v in err.iteritems])))
            except ValidationError as e:
                logging.exception(e)
                raise SchemaExampleError("{module_name}.{class_name} 中__example__方法返回值时错误的，错误详情: {error_msg}".format(
                    module_name=module_name, class_name=class_name,
                    error_msg=e.messages))
            example = json.dumps(_sma.__example__(), indent=4)
            yield file_name, "export type {class_name} = {context}".format(class_name=class_name, context=context)
            yield file_name, func(class_name, example)

    def _write(self, file_name, context, mode="a+"):
        file_path = os.path.join(self._ts_root, file_name)
        write_common_import_in_header(file_path)

        with open(file_path, mode) as f:
            f.write(context)

    def _generate_enum(self):
        while self._field_enum_set:
            field = self._field_enum_set.pop()
            field_enum = field.enum
            class_name = field_enum.__name__
            module_name = field.enum.__module__
            values = ["{retract}{type} = {value},".format(type=e.name, value=e.value, retract="\t" * self._pre_count)
                      for e in field_enum]
            check_variable(module_name, class_name, field)
            context = "export enum {name} {{ /* {description} 示例: {example}*/\n{value}\n}}".format(
                name=field_enum.__name__, description=field.metadata["description"], example=field.metadata["example"],
                value="\n".join(values))
            yield generate_ts_name("enum"), context

    def generate_ts(self):
        self._write(generate_ts_name("common"), "")

        file_name, description = self._generate_api_info()
        self._write(file_name, description)

        for file_name, request in self._generate_ts(self._sma.request(), generate_request_ts):
            self._write(file_name, request)
        for file_name, response in self._generate_ts(self._sma.response(), generate_response_ts):
            self._write(file_name, response)
        for file_name, context in self._generate_enum():
            self._write(file_name, context)


def clear(root):
    for file_name in os.listdir(root):
        if file_name.endswith(".d.ts"):
            file_path = os.path.join(root, file_name)
            logging.info("删除ts文件: %s" % file_path)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)


def generate_ts(root):
    for cls in BaseApiSchema.__subclasses__():
        s = cls()
        g = Generate(s, root)
        g.generate_ts()


def main():
    # if len(sys.argv) != 2:
    #     logging.error("必须制定ts文件路径!")
    #     sys.exit(2)
    # root = sys.argv[1]
    root = "/tmp/ts"
    clear(root)
    generate_ts(root)


if __name__ == '__main__':
    try:
        main()
    except SchemaMissingError as e:
        logging.exception(e)
        sys.exit(1)
    except Exception as e:
        logging.exception(e)
        sys.exit(-1)
