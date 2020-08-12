#!/usr/bin/env python
# -*- coding:utf-8 -*-

from sql_helper.base import open_session
from sql_helper.models import Cluster, Node

from sqlalchemy import JSON

from sqlalchemy import func as sa_func


def test1():
    ssh = {}
    data = {
        'uuid': '1245',
    }
    cluster_type = 'Three-tier'
    cluster_name = 'a'
    description = ['c']
    node_list = [{
        'ibcard_ip': ['123'],
        'name': '1',
        'cluster_uuid': '1',
        'ip': '1',
        'type': 'storage',
    }, {
        'ibcard_ip': ['123'],
        'name': '2',
        'cluster_uuid': '2',
        'ip': '2',
        'type': 'compute',
    }, {
        'ibcard_ip': ['1234'],
        'name': '4',
        'cluster_uuid': '4',
        'ip': '4',
        'type': 'sanfree',
    }]
    print("start1 ...")
    _cluster_obj = Cluster(ssh=ssh, uuid=data["uuid"], type=cluster_type, name=cluster_name,
                           description=description)
    with open_session() as session:
        cluster_obj = Cluster.merge(session, _cluster_obj, 'uuid')  # 更新集群前的所有 ip
        # 添加 node 节点的信息
        for node in node_list:
            attr = {"ibcard_ip": node['ibcard_ip']}
            _node_obj = Node(hostname=node['name'], uuid=node['cluster_uuid'], ip=node['ip'],
                             type=node['type'], cluster_id=cluster_obj.id, attr=attr)
            node_obj = Node.merge(session, _node_obj, 'ip')
            cluster_obj.nodes.add(node_obj)
        if not node_list:
            cluster_obj.nodes = set()
    print("end1 ...")


def test2():
    # 修改普通数据
    with open_session() as session:
        # json_contains 中的 val 需要用双引号括起来，所以目标值类型是字符串时，需要两层引号
        query = session.query(Cluster).filter(Cluster.name == "a",
                                              sa_func.json_contains(Cluster.description, '"c"', "$[0]"))
        obj = query.one()
        print("cluster:", obj)
        obj.name = "b"

        # 修改 JSON 数组和对象 数据, 需要显示的转换成JSON
        # 如果路径标识数组元素，则将相应的值插入该元素位置，然后将任何后续值向右移动。如果路径标识了超出数组末尾的数组位置，则将值插入到数组末尾。
    update_info = {
        "description": sa_func.json_array_insert(Cluster.description, '$[1]', sa_func.cast({
            "x": 194,
            "y": 68,
            "o": 100,
            "a": 0,
            "f": "/bao/uploaded/i4/696944147/O1CN01qjcXhk1gVN66z6pog_!!2-item_pic.png",
            "type": "I",
            "w": 388,
            "h": 136
        }, JSON)),
        "attr": sa_func.json_insert(Cluster.attr, "$.thumbnail",
                                    "/bao/uploaded/i1/696944147/O1CN0175JvxQ1gVN6HRrZ44_!!0-item_pic.jpg")
    }
    with open_session() as session:
        count = session.query(Cluster).filter(Cluster.name == "b").update(
            update_info, synchronize_session=False)
        print("update_data count:", count)

    with open_session() as session:
        for obj in session.query(Cluster).filter(Cluster.name == "b").all():
            print(obj)


if __name__ == "__main__":
    test1()
    test2()
