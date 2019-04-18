#!/usr/bin/env python
# -*- coding: utf-8 -*-

import settings

from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy import Column, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.schema import MetaData

engine_str = 'mysql+mysqldb://{username}:{password}@{host}:{port}/{db_name}'.format(**settings.db["mysql"])
engine = create_engine(engine_str, pool_size=5, pool_recycle=3600,
                       connect_args={"use_unicode": True, "charset": "utf8"})
Session = sessionmaker(bind=engine, autocommit=True, autoflush=False, expire_on_commit=False)
metadata = MetaData(bind=engine)


class ModelMixin(object):
    """
    自带两个时间戳字段的base model
    """
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8"
    }

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    attr = Column(JSON, default={})
    create_time = Column(DateTime, default=datetime.utcnow, doc="创建时间utc")
    update_time = Column(DateTime, default=None, onupdate=datetime.utcnow)

    @classmethod
    def get_first(cls, session, key, value):
        obj = session.query(cls).filter(getattr(cls, key) == value).first()
        return obj

    @classmethod
    def get_one(cls, session, key, value):
        obj = session.query(cls).filter(getattr(cls, key) == value).one()
        return obj

    @classmethod
    def get_all(cls, session, key=None, value=None):
        if key:
            objs = session.query(cls).filter(getattr(cls, key) == value).all()
        else:
            objs = session.query(cls).all()
        return objs

    @property
    def keys(self):
        return self.__table__.columns.keys()

    def to_dict(self):
        """返回一个dict格式"""
        result = {}
        columns = self.__table__.columns.keys()
        for column in columns:
            if column != "attr":
                result[column] = getattr(self, column)
        return result

    @classmethod
    def merge(cls, session, obj, key, value=None):
        """
        根据key, value来查询数据库中的数据，，如果有数据就merge，如果没有则add
        **注意**: 对于一对多(多对一)这种外键表，例如一个father, 多个children这种情况，
        当father使用merge时，如果father有children，则merge后，老的children会被删除，
        当father没有children时，则merge后，children不更新，如果需要更新，则要重新实现merge方法
        所以，在merge father的方法应该为：
        先merge father， 再merge children, 最后将children加入到father中将, 同时注意children为空时，
        使用father.children = set()将children置空, 例如：

        # 先merge father
        father = Father(name="King")
        father = Fater.merge(session, father, "name")

        # child
        child1 = Child(name = "child1")
        child2 = Child(name = "child2")
        # merge
        child1 = Child.merge(session, child1, "name")
        child2 = Child.merge(session, child2, "name")

        # 最后将child加给father.children
        father.chidren.add(child1)
        father.chidren.add(child2)

        # 如果没有child，则要将father.children清空
        father.children = set()
        """
        update_obj = None
        if not value:
            value = getattr(obj, key)
        old_obj = cls.get_first(session, key, value)
        if old_obj:
            obj.id = old_obj.id
            flag_modified(old_obj, key)
            update_obj = session.merge(obj)
        else:
            session.add(obj)
            update_obj = obj
        return update_obj

    def update(self, info_dict):
        """
        用info_dict中键值对来更新数据库中字段对应的值
        """
        if not isinstance(info_dict, dict):
            raise SQLException("updata: argument {} is not dict type".format(info_dict))
        for key, value in info_dict.iteritems():
            if isinstance(value, (int, float, basestring)) and key in self.keys:
                setattr(self, key, value)
                flag_modified(self, key)
            elif isinstance(value, dict) and key in self.keys:
                old_value = getattr(self, key)
                if not isinstance(old_value, dict):
                    raise SQLException("old value type error, type must dict.")
                old_value.update(value)
                setattr(self, key, old_value)
                flag_modified(self, key)
            else:
                raise SQLException("update: no such key {} or unsurpported value type {}".format(key, type(value)))
                
    def modify(self, key):
        flag_modified(self, key)

    @classmethod
    def table_columns(cls):
        """ 得到表的字段 """
        return inspect(cls).columns.keys()

    @classmethod
    def initialize(cls):
        """删除表并创建表"""
        table_name = cls.__table__.name
        try:
            table = metadata.tables[table_name]
        except KeyError:
            return False
        try:
            metadata.drop_all(tables=[table])
            metadata.create_all(tables=[table])
        except Exception:
            return False
        return True

    @classmethod
    def drop_table(cls):
        """删除表"""
        if cls.__table__ in metadata.sorted_tables:
            cls.__table__.drop(engine)


@contextmanager
def open_session():
    """ 可以使用with 上下文，在with结束之后自动commit """
    session = Session()
    session.begin()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def clean_all_table():
    """ 清除所有的表 """
    metadata.drop_all(engine)
    metadata.create_all(engine)


def drop_all_table():
    """ 删除所有的表 """
    metadata.drop_all(engine)


# create table
def create_all_table():
    metadata.create_all(checkfirst=True)


Entity = declarative_base(name="Entity", metadata=metadata, cls=ModelMixin)
