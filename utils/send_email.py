#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import smtplib

from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from pprint import pprint

# ================================= 常量 =================================
SSL_DRIVER = "ssl"  # 协议类型
TLS_DRIVER = "tls"
NORMAL_DRIVER = ""

HTML_TYPE = "html"  # 邮件类型
TEXT_TYPE = "text"

USERNAME = ""  # 用户名
PASSWORD = ""  # 密码
SERVER = "smtp.163.com"  # SMTP主机


def send_email(sendto, subject, message, mime_type, config, file_path=None):
    """发送邮件

    :param str or list sendto: 接收邮件的邮箱
    :param str subject: 邮件主题
    :param str message: 邮件正文内容
    :param str mime_type: 邮件类型
    :param dict config: 邮件发件人配置信息
    :param str file_path: 邮件附件路径
    """
    if config["protocol"] == "ssl":
        mail_server = smtplib.SMTP_SSL(host=config["server"],
                                       port=int(config["port"]),
                                       timeout=float(config["timeout"]))
    elif config["protocol"] == "tls":
        mail_server = smtplib.SMTP(host=config["server"],
                                   port=config["port"],
                                   timeout=float(config["timeout"]))
        mail_server.starttls()
    else:
        mail_server = smtplib.SMTP(host=config["server"],
                                   port=config["port"],
                                   timeout=float(config["timeout"]))

    mail_server.login(config["username"], str(config["password"]))

    if mime_type != "html":
        mime_type = "text"
    content = MIMEMultipart()
    content["Subject"] = Header(subject, "utf-8")
    content["From"] = config["from"]  # 发件人
    content["To"] = sendto  # 收件人
    content.attach(MIMEText(message, mime_type, "utf-8"))
    # 如果有附件,添加附件
    if file_path:
        file_buffer = MIMEApplication(open(file_path, 'rb').read(), charset="utf-8")
        file_buffer.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
        content.attach(file_buffer)
    mail_server.sendmail(config["from"], sendto, content.as_string())
    mail_server.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username",
                        required=False,
                        action="store",
                        dest="username",
                        help="email username.")
    parser.add_argument("-p", "--password",
                        required=False,
                        action="store",
                        dest="password",
                        help="email password.")
    parser.add_argument("-port", "--port",
                        required=False,
                        action="store",
                        dest="port",
                        type=int,
                        default=25,
                        help="email port.")
    parser.add_argument("-t", "--type",
                        required=False,
                        action="store",
                        dest="type",
                        default=HTML_TYPE,
                        choices=(HTML_TYPE, TEXT_TYPE),
                        help="email type.")
    parser.add_argument("-d", "--driver",
                        required=False,
                        action="store",
                        dest="driver",
                        default=SSL_DRIVER,
                        choices=(SSL_DRIVER, TLS_DRIVER, NORMAL_DRIVER),
                        help="email driver.")
    parser.add_argument("-s", "--server",
                        required=False,
                        action="store",
                        dest="server",
                        help="email server.")
    parser.add_argument("-timeout", "--timeout",
                        required=False,
                        action="store",
                        dest="timeout",
                        type=int,
                        default=5,
                        help="email timeout.")

    args = parser.parse_args()

    driver = args.driver  # 协议
    type_ = args.type  # 邮件类型
    server = args.server or SERVER  # SMTP 主机
    port = args.port  # 端口号
    username = args.username or USERNAME  # 用户名
    password = args.password or PASSWORD  # 密码
    timeout = args.timeout  # 超时时间
    config = {
        "username": username,
        "from": username,
        "password": password,
        "protocol": driver,
        "type": type_,
        "server": server,
        "port": port,
        "timeout": timeout,
    }
    pprint(config)
    sendto = config["username"]
    subject = "hjd test"
    message = "hjd test %s" % datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    mime_type = config["type"]
    send_email(sendto, subject, message, mime_type, config)


if __name__ == '__main__':
    main()
