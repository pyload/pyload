# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from .base import BaseApi
from .init import Api


CACHE = {}
QUOTA_UNLIMITED = -1


class StatisticsApi(BaseApi):
    """
    Retrieve download statistics and quota.
    """
    __slots__ = []

    def record_download(self, pyfile):
        """
        Add download record to the statistics.
        """
        del CACHE[:]

    def calc_quota(self, uid):
        return QUOTA_UNLIMITED

    def get_quota(self):
        """
        Number of bytes the user has left for download.
        """
        return self.calc_quota(self.user.true_primary)
