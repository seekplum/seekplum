# -*- coding: utf-8 -*-

import json
import time
import logging
import gc
import random
import commands
import traceback

import objgraph

from schema import SchemaError

from tornado.options import options
from tornado.web import Finish, HTTPError
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)


class BaseRequestHandler(RequestHandler):
    """Base RequestHandler"""

    def on_finish(self):
        self.do_finish()

    def do_finish(self, *args, **kwargs):
        pass

    def get_url_data(self):
        """
        返回get请求的数据
        获取query_arguments，同一key有重复值时只取值列表最后一个
        """
        return {key: value[-1] for key, value in self.request.query_arguments.iteritems()}

    def get_body_data(self, name=None):
        """
        当post时，获取json数据
        """
        try:
            if name:
                data = json.loads(self.get_body_argument(name))
            else:
                # `strict = False` 允许控制字符出现在value里
                # reference: https://docs.python.org/2/library/json.html
                data = json.loads(self.request.body, strict=False)
            return data
        except ValueError as e:
            logger.exception(e)
            self.error_response(error_code=1,
                                message="get json in body error: {}".format(e.message))

    def get_data(self, schema=None):
        """
        post, get, put, delete 类型handler 验证数据,
        schema 是 from schema import Schema中的Schema的一个实例
        func_type: get, post, put, delete
        """
        stack = traceback.extract_stack()
        func_type = stack[-2][2]
        if func_type in ["post", "put", "delete"]:
            data = self.get_body_data()
        elif func_type == "get":
            data = self.get_url_data()
        else:
            raise Exception("unsurported function type: {}".format(func_type))
        try:
            if schema:
                data = schema.validate(data)
            return data
        except SchemaError as e:
            logger.exception(e)
            self.error_response(error_code=2, message=e.message)

    def write_json(self, data):
        real_ip = self.request.headers.get('X-Real-Ip', "unknown")
        logger.info(
            "method: {}, uri: {}, real ip: {}, remote ip: {}, start time: {}, finish_time: {}, error_code: {}".format(
                self.request.method, self.request.uri, real_ip, self.request.remote_ip, self.request._start_time,
                time.time(), data["error_code"]))
        self.set_header("Content-Type", "application/json")
        if options.debug:
            self.write(json.dumps(data, indent=2))
        else:
            self.write(json.dumps(data))

    def success_response(self, data=None, message="", finish=True):
        response = {
            "error_code": 0,
            "message": message,
            "data": data
        }
        self.write_json(response)
        if finish:
            raise Finish

    def error_response(self, error_code, message="", data=None, status_code=202, finish=True):
        self.set_status(status_code)
        response = {
            "error_code": error_code,
            "data": data,
            "message": message,
        }
        self.write_json(response)
        if finish:
            raise Finish

    def options(self, *args, **kwargs):
        """
        避免前端跨域options请求报错
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods",
                        "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Max-Age", 1000)
        self.set_header("Access-Control-Allow-Headers",
                        "CONTENT-TYPE, Access-Control-Allow-Origin, cache-control, Cache-Control, x-access-token")
        self.set_header("Access-Control-Expose-Headers", "X-Resource-Count")

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods",
                        "POST, GET, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Max-Age", 1000)
        self.set_header("Access-Control-Allow-Headers",
                        "CONTENT-TYPE, Access-Control-Allow-Origin, cache-control, Cache-Control, x-access-token")
        self.set_header("Access-Control-Expose-Headers", "X-Resource-Count")

    def write_error(self, status_code, **kwargs):
        """Custrom error response
        """
        http_status_code = status_code
        http_reason = self._reason

        if "exc_info" in kwargs:
            exception = kwargs["exc_info"][1]
            if isinstance(exception, Exception) and not isinstance(exception, HTTPError):
                code = hasattr(exception, "code")
                if code:
                    http_status_code = exception.code
                else:
                    http_status_code = 1
                http_reason = exception.message

            if isinstance(exception, HTTPError):
                finish = False
            else:
                finish = True
        else:
            finish = True
        self.set_status(200)
        self.error_response(http_status_code, http_reason, finish=finish)


class AnalysisHandler(BaseRequestHandler):
    def show_leak_increase(self):
        print objgraph.show_most_common_types()
        print "===" * 20
        objgraph.show_growth()

    def show_chain(self, obj_type):
        # obj_type: Myobj_Type, type:string
        ref_chain = objgraph.find_backref_chain(
            random.choice(objgraph.by_type(obj_type)),
            objgraph.is_proper_module,
            max_depth=5)
        objgraph.show_chain(ref_chain, filename='chain.dot')
        cmd = "dot -Tpng chain.dot -o chain.png"
        commands.getstatusoutput(cmd)

    def show_leak_obj(self):
        root = objgraph.get_leaking_objects()
        logging.error("leak object: {}".format(len(root)))
        import pdb;
        pdb.set_trace()
        # objgraph.show_refs(root[:3], refcounts=True, filename='/tmp/leak.dot')
        # # yum install graphviz
        # cmd = "dot -Tpng /tmp/leak.dot -o /tmp/leak.png"
        # logging.error("result picture is: /tmp/leak.png")
        # commands.getstatusoutput(cmd)

    def gc(self):
        ### 强制进行垃圾回收
        gc.set_debug(gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_SAVEALL)
        # collect_garbage = gc.collect()
        # logging.error("unreachabel:   {}".format(collect_garbage))
        # gc.garbage是一个list对象，列表项是垃圾收集器发现的不可达（即垃圾对象）
        # 、但又不能释放(不可回收)的对象，通常gc.garbage中的对象是引用对象还中的对象。
        # 因Python不知用什么顺序来调用对象的__del__函数，导致对象始终存活在gc.garbage中，造成内存泄露
        garbage = gc.garbage
        logging.error("uncollectabel: {}".format(len(garbage)))

        mash = 0
        sql = 0
        with open("/tmp/garbage.txt", "w") as f:
            for g in garbage:
                line = "{}".format(garbage)
                # print linem
                if "marshmallow" in line:
                    mash += 1
                if "Column" in line:
                    sql += 1
                f.write("{}\n\n".format(line[0:150]))
        logging.error("total: {}".format(len(garbage)))
        logging.error("mash: {}".format(mash))
        logging.error("sql: {}".format(sql))
        import pdb
        pdb.set_trace()
        with open("/tmp/garbage.txt", "a") as f:
            f.write("total: {}, mash: {}, sql: {}".format(len(garbage), mash, sql))
        del garbage

        # gc.set_threshold(700, 10, 5)
        logging.error("threshold:     {}".format(gc.get_threshold()))

    def leak(self):
        self.gc()
        self.show_leak_increase()
        # self.show_leak_obj()

    def get(self):
        key = self.get_argument("key")
        if key == "leak":
            self.leak()
        self.success_response("OK")
