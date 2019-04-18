#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: user
#         Desc: 用户相关schema
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2019-02-26 18:17
#=============================================================================
"""

from marshmallow import fields, validate

from schemas import BaseApiSchema
from schemas import BaseResponse
from schemas import BaseLocalSchema
from schemas import Nested


class ApiRequestUserSchema(BaseLocalSchema):
    name = fields.Str(required=True, description="用户名", example="teste")
    email = fields.String(required=True, description="邮箱名", example="1@qq.com")
    type = fields.String(required=False, validate=validate.OneOf(("admin", "normal")), description="用户类型",
                         example="admin", default="normal")

    def __description__(self):
        return "查询用户信息参数"

    def __example__(self):
        return {
            "name": "test",
            "email": "1@qq.com",
            "type": "admin"
        }


class UserSchema(BaseLocalSchema):
    id = fields.Integer(required=True, description="用户id", example="1")
    name = fields.Str(required=True, description="用户名", example="test")
    email = fields.String(required=True, description="邮箱名", example="1@qq.com")
    created_at = fields.String(required=True, description="创建时间", example="2019-02-25 22:24:00")
    type = fields.String(validate=validate.OneOf(("admin", "normal")), required=True, description="用户类型",
                         example="admin")

    def __description__(self):
        return "返回用户信息"

    def __example__(self):
        return {
            "id": 1,
            "name": "test",
            "email": "1@qq.com",
            "created_at": "2019-02-25 22:24:00",
            "type": "admin"
        }


class ApiResponseUserSchema(BaseResponse):
    data = Nested(UserSchema, required=True)

    def __description__(self):
        return "返回用户信息查询结果"

    def __example__(self):
        return {
            "error_code": 0,
            "message": "",
            "data": UserSchema().__example__()
        }


class UserHandlerSchema(BaseApiSchema):
    def __description__(self):
        """api描述信息
        """
        return "查询用户信息"

    def __url__(self):
        """API的url路径"""
        return "/seekplum/user"

    def __method__(self):
        """API请求类型"""
        return "GET"

    def request(self):
        """请求参数schema"""
        return ApiRequestUserSchema()

    def response(self):
        """返回参数schema"""
        return ApiResponseUserSchema()
