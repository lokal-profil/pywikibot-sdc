#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for helpers.py."""
from __future__ import unicode_literals

import unittest

from pywikibotsdc.sdc_exception import SdcException


class TestSdcException(unittest.TestCase):
    """Test the SdcException __init__ method."""

    def test_init_invalid_level_fail(self):
        with self.assertRaises(ValueError):
            SdcException('foo', {}, '')

    def test_init_level_prefixes_log(self):
        E = SdcException('warning', 'data', 'log_msg')
        self.assertEqual(E.log, 'WARNING: log_msg')

    def test_init_log_is_msg(self):
        E = SdcException('warning', 'data', 'log_msg')
        self.assertEqual(E.log, str(E))
