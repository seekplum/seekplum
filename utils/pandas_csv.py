# -*- coding: utf-8 -*-
"""
# 安装依赖

pip install pandas openpyxl
"""
import os
import re
import glob
import random
import string

import pandas as pd


def random_string(length=5):
    """生成随机指定长度的字符串

    :return 随机字符串
    :rtype str
    """
    strings = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join([strings[random.randint(0, len(strings) - 1)] for _ in
                    range(length)])


def random_number(length=5):
    """随机生成指定长度的数字

    :return 随机数字
    :rtype int
    """
    strings = string.digits
    s = "".join([str(random.randint(1, 9))] +
                [strings[random.randint(0,
                                        len(strings) - 1)] for _ in range(length - 1)])
    return int(s)


def read_csv():
    os.remove("/tmp/coupon-logs.csv")
    csv_list = glob.glob('/tmp/coupon-log/*/*.csv')
    print(csv_list[0])

    df = None
    for index, csv_path in enumerate(csv_list):
        print(index + 1, csv_path)
        temp_df = pd.read_csv(csv_path)
        df = pd.concat([df, temp_df], axis=0, ignore_index=True)

    # 替换敏感信息
    for content in df["content"]:
        df["content"] = re.sub(r'"session":\s*"\w+"', '"session": "xxx"', content)

    # 删除重复行
    df = df.drop_duplicates()

    # 删除不需要的列
    df = df.drop(['__tag__:__client_ip__', '__tag__:__hostname__',
                  '__tag__:__receive_time__', '__tag__:_node_ip_', '__tag__:_node_name_',
                  '__topic__', '_container_ip_', '_container_name_', '_image_name_',
                  '_namespace_', '_pod_name_', '_pod_uid_', '_source_'], axis=1)

    # 按列排序
    df = df.sort_values(by=["_time_"])
    df = df.reset_index(drop=True)
    df.to_csv("/tmp/coupon-logs.csv")


def write_excel():
    file_path = "/tmp/test.xlsx"

    # 删除文件
    if os.path.exists(file_path):
        os.remove(file_path)

    # 设置列名
    columns = ["clientId", "map1", "map2", "map3", "map4"]

    # 创建数据结构
    df = pd.DataFrame(data=[], columns=columns)

    # 循环生成数据
    for i in range(10):
        # 生成每列数据
        client_id = random_string()
        map1 = random.choices(["vip1", "vip2"])
        map2 = random.choices(["家装", "车贷", "ETC"])
        map3 = random.choices(["渠道1", "渠道2", "渠道3"])
        map4 = random.choices(["支行1", "支行2", "支行3"])
        tmp_data = [client_id, map1, map2, map3, map4]

        # 生成新的数据结构
        tmp_df = pd.DataFrame(data=[tmp_data], columns=columns)

        # 追加
        df = df.append(tmp_df, ignore_index=True)

    # 保存到文件中
    df.to_excel(file_path, sheet_name="表格名字", index=False)


if __name__ == '__main__':
    read_csv()
    write_excel()
