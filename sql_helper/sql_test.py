#!/usr/bin/env python
# -*- coding:utf-8 -*-

from base import open_session
from seekplum import Seekplum_Node, Seekplum_Cluster


def test1():
    ssh = {}
    data = {
        'uuid': '1245',
    }
    cluster_type = 'Three-tier'
    cluster_name = 'b'
    description = 'c'
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
        'ibcard_ip': ['123'],
        'name': '3',
        'cluster_uuid': '3',
        'ip': '3',
        'type': 'storage',
    }]
    print "start .."

    cluster_obj = Seekplum_Cluster(ssh=ssh, uuid=data["uuid"], type=cluster_type, name=cluster_name,
                                description=description)
    with open_session() as session:
        cluster_obj = Seekplum_Cluster.merge(session, cluster_obj, 'uuid')  # 更新集群前的所有 ip
        # 添加 node 节点的信息
        for node in node_list:
            attr = {"ibcard_ip": node['ibcard_ip']}
            node_obj = Seekplum_Node(hostname=node['name'], uuid=node['cluster_uuid'], ip=node['ip'],
                                  type=node['type'], cluster_id=cluster_obj.id, attr=attr)
            _node_obj = Seekplum_Node.merge(session, node_obj, 'ip')
            cluster_obj.nodes.add(_node_obj)
        if not node_list:
            cluster_obj.nodes = set()
    print "end .."


def test2():
    ssh = {}
    data = {
        'uuid': '1245',
    }
    cluster_type = 'Three-tier'
    cluster_name = 'b'
    description = 'c'
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
    print "start2 .."
    _cluster_obj = Seekplum_Cluster(ssh=ssh, uuid=data["uuid"], type=cluster_type, name=cluster_name,
                                 description=description)
    with open_session() as session:
        cluster_obj = Seekplum_Cluster.merge(session, _cluster_obj, 'uuid')  # 更新集群前的所有 ip
        # 添加 node 节点的信息
        for node in node_list:
            attr = {"ibcard_ip": node['ibcard_ip']}
            _node_obj = Seekplum_Node(hostname=node['name'], uuid=node['cluster_uuid'], ip=node['ip'],
                                   type=node['type'], cluster_id=cluster_obj.id, attr=attr)
            node_obj = Seekplum_Node.merge(session, _node_obj, 'ip')
            cluster_obj.nodes.add(node_obj)
        if not node_list:
            cluster_obj.nodes = set()
    print "end2 .."


if __name__ == "__main__":
    test2()
