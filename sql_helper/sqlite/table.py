# -*- coding: utf-8 -*-
try:
    import simplejson as json
except:
    import json
import db_local
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import Column, String, Text, PickleType


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


class API_Local(db_local.Entity):
    session = db_local.session
    __tablename__ = "api_local"
    cmd = Column(String(200), primary_key=True)
    value = Column(Text)

    def __repr__(self):
        return "<cache: {}, hdd_disk: {}, com_disk: {}, status: {}, settings: {}>".format(
            self.cache, self.hdd_disk, self.com_disk, self.status, self.settings)

    @classmethod
    def delete_cache(cls, cmd):
        num = cls.session.query(cls).filter_by(cmd=cmd).delete()
        cls.session.commit()
        return num


class FlashCache(db_local.Entity):
    session = db_local.session
    __tablename__ = "flashcache"
    cache = Column(String(100), primary_key=True)
    hdd_disk = Column(String(100))
    com_disk = Column(String(200))  # combination disk
    status = Column(String(20))
    settings = Column(MutableDict.as_mutable(PickleType(pickler=json)), default={})

    def __repr__(self):
        return "<cache: {}, hdd_disk: {}, com_disk: {}, status: {}, settings: {}>".format(
            self.cache, self.hdd_disk, self.com_disk, self.status, self.settings)

    @classmethod
    def delete_by_cache(cls, cache):
        num = cls.session.query(cls).filter_by(cache=cache).delete()
        cls.session.commit()
        return num

    @classmethod
    def get_active_flashcache(cls):
        return cls.session.query(cls).filter_by(status="ACTIVE").all()

    @classmethod
    def get_all(cls):
        return cls.session.query(cls).all()


# create all table
db_local.metadata.create_all(db_local.engine)
