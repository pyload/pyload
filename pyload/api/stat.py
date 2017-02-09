# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.api import Api
from pyload.api import Permission
from pyload.api import require_perm

from pyload.api.base import BaseApi

CACHE = {}
QUOTA_UNLIMITED = -1


class StatisticsApi(BaseApi):
    """
    Retrieve download statistics and quota.
    """

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


if Api.extend(StatisticsApi):
    del StatisticsApi
