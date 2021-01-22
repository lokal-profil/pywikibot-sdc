#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Common functions not specifically related to batchuploads or wiki."""
from __future__ import unicode_literals

# avoid having to use from past.builtins import basestring
try:
    basestring  # attempt to evaluate basestring
except NameError:
    def is_str(s):
        """Python 3 test for string type."""
        return isinstance(s, str)
else:
    def is_str(s):
        """Python 2 test for basestring type."""
        return isinstance(s, basestring)


def is_int(value):
    """Check if the given value is an integer.

    @param value: The value to check
    @type value: str, or int
    @return bool
    """
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def is_pos_int(value):
    """Check if the given value is a positive integer.

    @param value: The value to check
    @type value: str, or int
    @return bool
    """
    if is_int(value) and int(value) > 0:
        return True
    return False
