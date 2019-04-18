#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest


class DB(object):
    def __init__(self):
        self.intransaction = []

    def begin(self, name):
        self.intransaction.append(name)

    def rollback(self):
        self.intransaction.pop()


@pytest.fixture(scope="module")
def db():
    return DB()


class TestClass(object):
    @pytest.fixture(scope="function", autouse=True)
    # @pytest.fixture(scope="class", autouse=True)
    def transact(self, request, db):
        # db.begin(request.cls.__name__)
        db.begin(request.function.__name__)
        yield
        db.rollback()

    def test_method1(self, db):
        assert db.intransaction == ["test_method1"]
