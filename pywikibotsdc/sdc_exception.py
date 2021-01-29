#!/usr/bin/python
# -*- coding: utf-8  -*-
"""SDC flavoured pywikibot.Error exception."""
from __future__ import unicode_literals

from pywikibot.exceptions import Error


class SdcException(Error):
    """
    SDC flavoured exception with severity level, data and formatted log entry.

    Designed to be compatible with the BatchuploadTools results report.
    BatchuploadTools: https://github.com/lokal-profil/BatchUploadTools
    """

    allowed_levels = ('error', 'warning')

    def __init__(self, level, data, log):
        """
        Initializer.

        @param page: Page that caused the exception
        @type page: Page object
        @raise: ValueError
        """
        if level not in self.allowed_levels:
            raise ValueError(
                'Level must be one of "{0}": got "{1}"'.format(
                    '", "'.join(self.allowed_levels), level))
        self.level = level
        self.data = data
        self.log = "{0}: {1}".format(level.upper(), log)
        super(SdcException, self).__init__(self.log)
