#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for common.py."""
from __future__ import unicode_literals

import unittest

from pywikibotsdc.common import is_int, is_pos_int


class TestIsInt(unittest.TestCase):
    """Test the is_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_valid_negative_int_succeed(self):
        s = '-123'
        result = is_int(s)
        self.assertEqual(result, True)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_int(s)
        self.assertEqual(result, True)


class TestIsPosInt(unittest.TestCase):
    """Test the is_pos_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_negative_int_fail(self):
        s = '-123'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_pos_int(s)
        self.assertEqual(result, True)
