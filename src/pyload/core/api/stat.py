# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from .base import BaseApi

standard_library.install_aliases()


CACHE = {}
QUOTA_UNLIMITED = -1


class StatisticsApi(BaseApi):
    """
    Retrieve download statistics and quota.
    """
    def record_download(self, file):
        """
        Add download record to the statistics.
        """
        del CACHE[:]
        raise NotImplementedError

    def calc_quota(self, uid):
        return QUOTA_UNLIMITED

    def get_quota(self):
        """
        Number of bytes the user has left for download.
        """
        return self.calc_quota(self.user.true_primary)
