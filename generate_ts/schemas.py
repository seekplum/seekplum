#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: schema
#         Desc: 
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-02-26 10:36
#=============================================================================
"""

import abc
import six
import logging

from marshmallow.schema import BaseSchema
from marshmallow import fields, pre_load, post_load, Schema, ValidationError
from marshmallow.utils import is_collection, _Missing

logger = logging.getLogger(__name__)


class LocalSchema(Schema):
    def __init__(self, *args, **kwargs):
        super(LocalSchema, self).__init__(*args, **kwargs)

    @pre_load
    def process_input(self, data):
        if data is not None:
            try:
                return dict(data)
            except ValueError:
                if isinstance(data, list):
                    return dict(data[0])
                logger.exception("解析的数据格式不符合规范:{}".format(data))
                raise
        return data

    @post_load
    def make_obj(self, data):
        if len(self.fields) != len(data):
            if isinstance(self.fields, dict) and isinstance(data, dict):
                diff_keys = set(self.fields.keys()) - set(data.keys())
                if diff_keys:
                    for item in diff_keys:
                        # 不能用getattr判断，防止默认值为 False, 空字符串， 0 等情况时，无法赋默认值
                        if hasattr(self.fields[item], "default") and \
                                not isinstance(self.fields[item].default, _Missing):
                            data[item] = self.fields[item].default
        return data

    @BaseSchema.error_handler
    def handle_errors(self, errors, obj):
        logger.error("Marshal error {} occurred while marshalling {}".format(errors, obj))
        raise ValidationError("关键参数校验出错: {}".format(errors))


class Nested(fields.Nested):
    """
    重写 fields.Nested的反序列方法, 支持对列表的序列化映射
    """

    def __init__(self, nested, default=None, exclude=tuple(), only=None, **kwargs):
        super(Nested, self).__init__(nested, default, exclude, only, **kwargs)

    def _deserialize(self, value, attr, data):
        if self.many:
            if not is_collection(value):
                value = [value]

        data, errors = self.schema.load(value)
        if errors:
            raise ValidationError(errors, data=data)
        return data


class BaseLocalSchema(LocalSchema):

    def __description__(self):
        """描述信息
        """
        raise NotImplementedError(
            "{}: The __description__ method must be implemented".format(self.__class__.__name__)
        )

    def __example__(self):
        """示例"""
        raise NotImplementedError(
            "{}: The __example__ method must be implemented".format(self.__class__.__name__)
        )


class BaseResponse(BaseLocalSchema):
    error_code = fields.Integer(required=True, description="请求状态码", example=200, default=0)
    message = fields.String(required=True, description="错误信息", example="请求正常!", default="")

    def __description__(self):
        """描述信息
        """
        raise NotImplementedError(
            "{}: The __description__ method must be implemented".format(self.__class__.__name__)
        )

    def __example__(self):
        """示例"""
        raise NotImplementedError(
            "{}: The __example__ method must be implemented".format(self.__class__.__name__)
        )


class BaseApiSchema(six.with_metaclass(abc.ABCMeta)):
    def __init__(self):
        pass

    @abc.abstractmethod
    def __description__(self):
        """api描述信息
        """

    @abc.abstractmethod
    def __url__(self):
        """API的url路径"""

    @abc.abstractmethod
    def __method__(self):
        """API请求类型"""

    @abc.abstractmethod
    def request(self):
        """请求参数schema"""

    @abc.abstractmethod
    def response(self):
        """返回参数schema"""
