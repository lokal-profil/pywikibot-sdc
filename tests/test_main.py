#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for __main__.py."""
from __future__ import unicode_literals

import unittest

import mock

from pywikibotsdc.__main__ import handle_args


class TestHandleArgs(unittest.TestCase):
    """Test the handle_args method."""

    def setUp(self):

        patcher = mock.patch(
            'pywikibotsdc.__main__.argparse.ArgumentParser.error',
            autospec=True)
        self.mock_argparse_error = patcher.start()
        self.addCleanup(patcher.stop)

        # mock out anything communicating with live platforms
        patcher = mock.patch(
            'pywikibotsdc.__main__.pywikibot.handle_args')
        self.mock_pwb_handle_args = patcher.start()
        self.mock_pwb_handle_args.return_value = None
        self.addCleanup(patcher.stop)

    def test_handle_args_argparse_catch_local_args(self):
        call = '-b data.json'
        handle_args(call.split(' '))
        self.mock_pwb_handle_args.assert_not_called()

    def test_handle_args_argparse_pass_pywikibot_args(self):
        call = '-simulate data.json'
        handle_args(call.split(' '))
        self.mock_pwb_handle_args.assert_called_once_with(['-simulate'])
        self.mock_argparse_error.assert_not_called()

    def test_handle_args_argparse_raise_on_unknown_args(self):
        call = '--foobar data.json'
        self.mock_pwb_handle_args.return_value = ['--foobar']
        handle_args(call.split(' '))
        self.mock_pwb_handle_args.assert_called_once()
        self.mock_argparse_error.assert_called_once()
