#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nosetests: pip install nose
subunit: pip install python-subunit
testrepository: pip install testrepository
testscenarios: pip install testscenarios
coverage: pip install coverage
"""
import unittest

import mock
import requests
import testscenarios


class WhereIsPythonError(Exception):
    pass


def is_python_still_a_programming_language():
    try:
        response = requests.get("http://python.org")
    except IOError:
        pass
    else:
        if response.status_code == 200:
            return "Python is a programming language" in response.content
    raise WhereIsPythonError("Something bad happened")


def get_fake_get(status_code, content):
    m = mock.Mock()
    m.status_code = status_code
    m.content = content

    def fake_get(url):
        return m

    return fake_get


def raise_get(url):
    raise IOError("Unable to fetch url %s" % url)


class TestPython(unittest.TestCase):
    @mock.patch("requests.get", get_fake_get(200, "Python is a programming language for sure"))
    def test_python_is(self):
        self.assertTrue(is_python_still_a_programming_language())

    @mock.patch("requests.get", get_fake_get(200, "Python is not more programming language"))
    def test_python_is_not(self):
        self.assertFalse(is_python_still_a_programming_language())

    @mock.patch("requests.get", get_fake_get(404, "Whatever"))
    def test_bad_status_code(self):
        self.assertRaises(WhereIsPythonError, is_python_still_a_programming_language)

    @mock.patch("requests.get", raise_get)
    def test_io_error(self):
        self.assertRaises(WhereIsPythonError, is_python_still_a_programming_language)


class TestPythonErrorCode(testscenarios.TestWithScenarios):
    scenarios = [
        ("Not found", dict(status=404)),
        ("Client error", dict(status=400)),
        ("Server error", dict(status=500)),
    ]

    def test_python_status_code_handling(self):
        with mock.patch("requests.get", get_fake_get(self.status, "Python is programming language for sure")):
            self.assertRaises(WhereIsPythonError, is_python_still_a_programming_language)


if __name__ == '__main__':
    unittest.main()
