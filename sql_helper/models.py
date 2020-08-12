# -*- coding: utf-8 -*-

import logging

from sqlalchemy import Column, String, Integer, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from .base import Entity, open_session


def default_host_uuid(context):
    return context.current_parameters["ip"]


class Cluster(Entity):
    """集群信息表"""
    __tablename__ = "cluster"

    # enum
    THREE_TIER = "Three-tier"
    SAN_FREE = "Sanfree"
    UNKNOWN = "Unknown"
    LONGHAUL = "Longhaul"
    enum_qdtype = Enum(THREE_TIER, SAN_FREE, UNKNOWN, LONGHAUL)
    TYPE_NAME = {
        THREE_TIER: u"三层架构",
        SAN_FREE: u"双节点架构",
        LONGHAUL: u"长距双活",
        UNKNOWN: u"未知",
    }

    # columns
    id = Column(Integer, primary_key=True)
    name = Column(String(length=128), nullable=True, unique=True, doc="集群名字")
    uuid = Column(String(length=128), nullable=False, doc="集群uuid")
    type = Column(enum_qdtype, nullable=False, doc="集群类型")
    distance = Column(Integer, nullable=True, doc="距离：1/10/40/80公里")
    description = Column(JSON, default=[], nullable=True, doc="集群描述")
    ssh = Column(JSON, default={}, doc="登录集群的user/password/port/key")

    @classmethod
    def get_by_uuid(cls, cluster_uuid):
        with open_session() as session:
            return session.query(cls).filter_by(uuid=cluster_uuid).first()

    @classmethod
    def get_by_id(cls, session, cluster_id):
        return session.query(cls).filter_by(id=cluster_id).first()

    @classmethod
    def update_cluster(cls, cluster, name=None, description=None):
        """
        更新集群名字、描述
        :param cluster: 集群对象
        :param name: 待更新的集群名字
        :param description: 待更新集群描述
        :return: 成功返回 True，失败返回 False
        """
        logger = logging.getLogger(__name__)
        if not name and not description:
            return False
        if not isinstance(cluster, cls):
            return False
        try:
            with open_session() as session:
                if name:
                    cluster.name = name
                if description:
                    cluster.description = description
                session.merge(cluster)
        except Exception as e:
            logger.exception(e)
            return False
        return True

    @classmethod
    def merge(cls, session, obj, key):
        old_obj = cls.get_first(session, key, getattr(obj, key))
        if old_obj:
            # 根据 key 判断原来数据中的 nodes( 即节点信息)是否存在，old_obj和obj同时有nodes则不允许merge
            if old_obj.nodes and obj.nodes:
                raise Exception("merge failed: both source and destination has no empty nodes")
            else:
                return super(Cluster, cls).merge(session, obj, key)
        else:
            return super(Cluster, cls).merge(session, obj, key)


class Node(Entity):
    """主机信息表"""
    __tablename__ = "node"
    # enum

    COMPUTE = "compute"
    STORAGE = "storage"
    SANFREE = "sanfree"
    NORMAL = "normal"
    enum_hosttype = Enum(COMPUTE, STORAGE, SANFREE, NORMAL)
    TYPE_NAME = {
        COMPUTE: u"计算节点",
        STORAGE: u"存储节点",
        SANFREE: u"Sanfree",
        NORMAL: u"主机",
    }

    # columns
    uuid = Column(String(100), nullable=False, default=default_host_uuid, doc="主机uuid")
    name = Column(String(length=100), nullable=True, doc="host别名")
    hostname = Column(String(length=100), nullable=False, doc="主机名")
    room = Column(String(length=100), nullable=True, doc="机房名称, room_A, room_B")
    ip = Column(String(length=39), nullable=False, doc="ip地址，长度兼容ipv6")
    vip = Column(String(length=39), nullable=True, doc="vip地址，长度兼容ipv6")
    type = Column(enum_hosttype, doc="主机类型")
    status = Column(JSON, default={}, doc="主机状态 up/down")
    # cluster(many2one)
    cluster_id = Column(Integer, ForeignKey("cluster.id", ondelete="CASCADE"))
    cluster = relationship(Cluster, backref=backref("nodes", cascade="all, delete-orphan", collection_class=set),
                           doc="集群id")
    config = Column(JSON, default={}, doc="主机配置信息")  # 存ipmi信息
