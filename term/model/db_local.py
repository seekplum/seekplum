#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from conf import Seekplum_DB_FILE_LOCAL
from utils.util import get_project_path

dbfile = os.path.join(get_project_path(), Seekplum_DB_FILE_LOCAL)

engine = create_engine("sqlite:///{}".format(dbfile))
Session = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False))  # make sure the session id is unique
metadata = MetaData(bind=engine)
session = Session()


@contextmanager
def open_session():
    global session
    try:
        session.close()
        session = Session()
        yield session
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()


def new_session():
    session = Session()
    return session


def clean_all_table():
    global metadata
    metadata.drop_all(engine)
    metadata.create_all(engine)


def drop_all_table():
    global metadata
    metadata.drop_all(engine)


class ModelMixin(object):
    def __getitem__(self, key):
        value = getattr(self, key)
        if isinstance(value, unicode):
            return str(value)
        return value

    def __getattribute__(self, key):
        value = super(ModelMixin, self).__getattribute__(key)
        if isinstance(value, unicode):
            return str(value)
        return value

    @classmethod
    def get(cls, id_):
        return cls.query.get(id_)

    @classmethod
    def get_all(cls, columns=None, offset=None, limit=None, order_by=None, lock_mode=None):
        if columns:
            if isinstance(columns, (tuple, list)):
                query = cls.session.query(*columns)
            else:
                query = cls.session.query(columns)
                if isinstance(columns, str):
                    query = query.select_from(cls)
        else:
            query = cls.session.query(cls)
        if order_by is not None:
            if isinstance(order_by, (tuple, list)):
                query = query.order_by(*order_by)
            else:
                query = query.order_by(order_by)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        if lock_mode:
            query = query.with_lockmode(lock_mode)
        return query.all()

    # Entity.get_all = get_all

    @classmethod
    def exist(cls, id_, lock_mode=None):
        s = cls.query.get(id_)
        return True if s else False

    @classmethod
    def update_or_insert(cls, id_, obj):
        if cls.exist(id_):
            cls.session.merge(obj)
        else:
            cls.session.add(obj)
        cls.session.commit()

    def to_dict(self):
        result = {}
        columns = self.__table__.columns.keys()
        for column in columns:
            result[column] = getattr(self, column)
        return result

    @classmethod
    def initialize(cls):
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
    def table_columns(cls):
        """
        Get table columns
        """
        return inspect(cls).columns.keys()

    @classmethod
    def drop_table(cls):
        global engine
        global metadata
        if cls.__table__ in metadata.sorted_tables:
            cls.__table__.drop(engine)


Entity = declarative_base(name="Entity", metadata=metadata, cls=ModelMixin)
Entity.query = Session.query_property()
