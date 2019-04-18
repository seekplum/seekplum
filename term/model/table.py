# -*- coding: utf-8 -*-
try:
    import simplejson as json
except:
    import json
import time
from datetime import datetime
from model import db
from model import db_local
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import Column, Integer, String, PickleType


class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)
            return Mutable.coerce(key, value)
        else:
            return value

    def __delitem(self, key):
        dict.__delitem__(self, key)
        self.changed()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()

    def __getstate__(self):
        return dict(self)

    def __setstate__(self, state):
        self.update(self)


class Server(db.Entity):
    __tablename__ = "server"

    name = Column(String, primary_key=True)
    id = Column(Integer, nullable=False)
    ip = Column(String, nullable=False)
    type = Column(String, nullable=False)
    ibcard_ip = Column(String, nullable=False)
    cluster_uuid = Column(String(50), nullable=False)

    def __repr__(self):
        return "<Server(name={}, id={}, ip={}, type={}, ibcard_ip={})>".format(
            self.name, self.id, self.ip, self.type, self.ibcard_ip)

    @classmethod
    def get_name_set(cls):
        with db.open_session() as session:
            server = session.query(Server).all()

        return set([item.name for item in server])

    @classmethod
    def get_server_ip(cls):
        with db.open_session() as session:
            server = session.query(Server).all()

        return {item.name: item.ip for item in server}


class ConfTime(db.Entity):
    __tablename__ = "time"

    id = Column(Integer, primary_key=True)
    time = Column(Integer, nullable=False)
    change_node = Column(String)

    def __init__(self):
        self.time = int(time.time())

    def __repr__(self):
        return "<ConfTime(id={}, time={}, change_node={})>".format(
            self.id, datetime.fromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S"), self.change_node)


class API_Local(db_local.Entity):
    session = db_local.session
    __tablename__ = "api_local"
    cmd = Column(String(200), primary_key=True)
    value = Column(MutableDict.as_mutable(PickleType(pickler=json)), default={})

    def __repr__(self):
        return "<cache: {}, hdd_disk: {}, com_disk: {}, status: {}, settings: {}>".format(
            self.cache, self.hdd_disk, self.com_disk, self.status, self.settings)


# create all table
db.metadata.create_all(db.engine)
db_local.metadata.create_all(db_local.engine)
