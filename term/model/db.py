#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import MetaData
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from conf import Seekplum_DB_FILE
from utils.util import get_project_path

dbfile = os.path.join(get_project_path(), Seekplum_DB_FILE)

engine = create_engine("sqlite:///{}".format(dbfile))
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
metadata = MetaData(bind=engine)

session = Session()


@contextmanager
def open_session():
    try:
        session = Session()
        yield session
        session.commit()
    except OperationalError as e:
        # create all table
        metadata.create_all(checkfirst=True)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def clean_all_table():
    global engine
    metadata.drop_all(engine)
    metadata.create_all(engine)


def drop_all_table():
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

    @classmethod
    def count(cls):
        with open_session() as session:
            return session.query(cls).count()


Entity = declarative_base(name="Entity", metadata=metadata, cls=ModelMixin)
