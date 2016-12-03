# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals
from pyload.Api import Api, RequirePerm, Permission

from .ApiComponent import ApiComponent

CACHE = {}
QUOTA_UNLIMITED = -1


class StatisticsApi(ApiComponent):
    """ Retrieve download statistics and quota """

    def recordDownload(self, pyfile):
        """ Add download record to the statistics """
        del CACHE[:]

    def calcQuota(self, uid):
        return QUOTA_UNLIMITED

    def getQuota(self):
        """ Number of bytes the user has left for download  """
        return self.calcQuota(self.user.true_primary)


if Api.extend(StatisticsApi):
    del StatisticsApi
