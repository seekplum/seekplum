#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#=============================================================================
#  ProjectName: seekplum
#     FileName: ftp_utils
#         Desc: 接收alertmanger发送过来的告警信息，做出相应处理
#       Author: seekplum
#        Email: 1131909224m@sina.cn
#     HomePage: seekplum.github.io
#       Create: 2018-05-31 16:06
#=============================================================================
"""
import os
import json
import sys
import getopt
import datetime
import logging
import logging.handlers

from contextlib import contextmanager
from ftplib import FTP

LOG_PATH = "/tmp/receiving_alarm_data.log"  # 日志路径

# ftp服务器相关配置
FTP_HOST = "192.168.1.27"
FTP_USERNAME = "ftpuser"
FTP_PASSWORD = "ftpuser"
FTP_ROOT = "/home/ftpuser"
FTP_PORT = 21


def get_logger(level):
    """设置日志格式,路径
    """
    logger_ = logging.getLogger("receiving_alarm_data")
    file_formatter = logging.Formatter('[%(name)s %(levelname)s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                                       datefmt='%Y-%m-%d %H:%M:%S')
    # 只保留 10 份日志, 最大10M
    log_file_handle = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=10 * 1024 * 1024, backupCount=10)
    log_file_handle.setFormatter(file_formatter)
    logger_.addHandler(log_file_handle)

    logger_.setLevel(level)
    return logger_


logger = get_logger(logging.INFO)


@contextmanager
def ftp_connect(host, username, password, port):
    ftp_conn = FTP()
    ftp_conn.set_debuglevel(2)
    ftp_conn.connect(host, port)
    ftp_conn.login(username, password)
    yield ftp_conn
    ftp_conn.quit()


def upload_file(local_path, remote_path):
    """上传文件到ftp服务器

    :param local_path: 本地文件路径
    :type local_path str

    :param remote_path: 目标服务器路径
    :type remote_path str
    """
    logger.info("upload file: %s to %s" % (local_path, remote_path))
    buf_size = 1024 * 1
    with ftp_connect(FTP_HOST, FTP_USERNAME, FTP_PASSWORD, FTP_PORT) as ftp_conn:
        with open(local_path, 'rb') as fp:
            ftp_conn.storbinary('STOR ' + remote_path, fp, buf_size)


def get_curr_time_str(fmt="%Y-%m-%d_%H-%M-%S"):
    """获取当前时间的字符串

    :param fmt 时间格式
    :type fmt str

    :rtype str
    :return 当前时间的字符串格式
    """
    return datetime.datetime.now().strftime(fmt)


def parse_data(data):
    """解析alertmanager发送过来的数据

    :param data 告警数据
    :type data dict

    :rtype list
    :return 重新组合后的告警数据
    """
    info = []
    for item in data["alerts"]:
        annotations = item["annotations"]
        labels = item["labels"]
        status = item["status"]
        res = {
            "severity": labels["severity"],  # 告警级别 `critical`为严重的告警, `warn`为警告级别的告警
            "ip": labels["ip"],  # 告警对象的ip
            "status": status,  # 状态 firing为未解决 resolved为已经解决的告警
            "start_time": item["startsAt"],  # 告警开始时间
            "end_time": item["endsAt"] if status == "resolved" else None,  # 告警结束时间 只有告警状态是已解决时，该值才不为空
            "alert_name": annotations["alertname"],  # 告警指标名
            "description": annotations["description"],  # 告警描述信息
            "error_code": annotations["errorcode"],  # 告警错误码
            "message": annotations["message"],  # 告警详情
            "suggest": annotations["suggest"],  # 告警建议
        }
        info.append(res)
    return info


def print_help():
    """打印帮助信息
    """
    print "%s { json格式的告警信息 } { 收件人手机号码 }" % sys.argv[0]
    # 数据格式
    help_info = """往文件中写入的是json字符串，json load后示例数据如下:
    [
      {
        'status': 'firing',
        'alert_name': '目录空间剩余容量',
        'severity': 'critical',
        'suggest': '请尝试删除一些不必要的文件释放空间，或者增加其空间',
        'ip': '10.10.100.5',
        'start_time': '2018-05-30T14:09:52.803+08:00',
        'end_time': null,
        'description': '监控文件系统挂载点目录的剩余空间，在空间耗尽之前及时告警',
        'error_code': 'QD-S007',
        'message': 'QD-S007：文件系统挂载点目录 \u003cspan\u003e/home\u003c/span\u003e 的剩余空间百分比仅剩 \u003cspan\u003e84.8%\u003c/span\u003e！某些重要的目录空间不足可能导致严重的问题'
      }
    ]

每个字段含义:
    status: 状态 `firing` 为未解决, `resolved` 为已经解决的告警
    alert_name: 告警指标名
    severity: 告警级别 `critical`为严重的告警, `warn`为警告级别的告警
    suggest: 告警建议
    ip: 告警对象的ip
    start_time: 告警开始时间
    end_time: 告警结束时间 只有告警状态是已解决时，该值才不为空
    description: 告警描述信息
    error_code: 告警错误码
    message: 告警详情"""
    print help_info


def parse_args():
    """解析输入参数

    python2.6.6没有 argparse模块
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        print_help()
        sys.exit(1)
    else:
        logger.info("args: %s" % (" | ".join(args)))
        logger.info("opts: %s" % (" | ".join([" - ".join(opt) for opt in opts])))
        if opts or "-h" in args or "--help" in args:
            print_help()
            sys.exit(0)
    return args


def write_data(data, phone_number):
    """记录数据到指定文件中

    :param data 要记录的数据
    :type data list

    :param phone_number 电话号码
    :type phone_number str
    """
    logger.info("phone number: %s" % phone_number)
    logger.info(data)

    curr_path = os.path.dirname(os.path.abspath(__file__))

    # 以IP和时间的格式记录json数据
    ip = data[0]["ip"]
    curr_time = get_curr_time_str()
    data_file_name = "%s_%s_%s_json.txt" % (ip, phone_number, curr_time)
    data_file_path = os.path.join(curr_path, data_file_name)
    logger.info("data_file_path: %s" % data_file_path)

    with open(data_file_path, "w") as f:
        content = json.dumps(data)
        f.write(content)

    return data_file_path


def parse_and_upload(args):
    """解析并上传文件

    :param args 输入的参数
    :type args list
    """
    data = parse_data(json.loads("".join(args[:-1])))
    phone_number = args[-1]

    # 把数据写入指定文件中
    data_file_path = write_data(data, phone_number)

    # 上传文件到服务器
    upload_file(data_file_path, os.path.join(FTP_ROOT, os.path.basename(data_file_path)))

    # 删除文件
    os.remove(data_file_path)


def get_test_data():
    """获取测试数据
    """
    return """{
  "receiver": "group-sms-1",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "node_filesystem_use__1host",
        "device": "/dev/mapper/VolGroup-root",
        "exporter": "host",
        "fstype": "xfs",
        "instance": "10.10.100.5:10001",
        "ip": "10.10.100.5",
        "job": "Host",
        "monitor": "QFlame",
        "mountpoint": "/",
        "product_type": "seekplum",
        "routing_key": "seekplum__10.10.100.5",
        "severity": "critical",
        "tid": "1"
      },
      "annotations": {
        "alertname": "目录空间剩余容量",
        "description": "监控文件系统挂载点目录的剩余空间，在空间耗尽之前及时告警",
        "errorcode": "QD-S007",
        "message": "QD-S007：文件系统挂载点目录 \u003cspan\u003e/\u003c/span\u003e 的剩余空间百分比仅剩 \u003cspan\u003e68.6%\u003c/span\u003e！某些重要的目录空间不足可能导致严重的问题",
        "suggest": "请尝试删除一些不必要的文件释放空间，或者增加其空间"
      },
      "startsAt": "2018-05-30T14:09:52.803+08:00",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://127.0.0.1:10011/graph?g0.expr=100+%2A+node_filesystem_free+%2F+node_filesystem_size%7Bexporter%3D%22host%22%2Cmountpoint%21~%22%28%3Fi%29%2Fmnt%2Frhel%22%2Ctid%3D%221%22%7D+%3C+100\u0026g0.tab=0"
    }
  ],
  "groupLabels": {
    "routing_key": "seekplum__10.10.100.5"
  },
  "commonLabels": {
    "exporter": "host",
    "instance": "10.10.100.5:10001",
    "ip": "10.10.100.5",
    "job": "Host",
    "monitor": "QFlame",
    "product_type": "seekplum",
    "routing_key": "seekplum__10.10.100.5",
    "severity": "critical",
    "tid": "1"
  },
  "commonAnnotations": {

  },
  "externalURL": "http://host-192-168-1-157:10012"
}"""


def test():
    """测试函数
    """
    data = parse_data(json.loads(get_test_data()))
    phone_number = "12341234123"

    # 把数据写入指定文件中
    file_path = write_data(data, phone_number)

    # 重新解析数据看是否正常
    with open(file_path, "r") as f:
        content = f.read()
        data = json.loads(content)

    # 打印数据
    for item in data:
        for k, v in item.items():
            print "%s: %s" % (k, v)
        print


def main():
    """主函数
    """
    # 解析传入的参数
    args = parse_args()
    if len(args) < 2:
        test()
    else:
        parse_and_upload(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
