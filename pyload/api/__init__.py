# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import

from pyload.api.base import AbstractApi, Api, BaseApi, requireperm, statestring
from pyload.api.account import AccountApi
from pyload.api.addon import AddonApi
from pyload.api.config import ConfigApi
from pyload.api.core import CoreApi
from pyload.api.download import DownloadApi
from pyload.api.exchange import UserExchangeApi
from pyload.api.file import FileApi
from pyload.api.predownload import PreDownloadApi
from pyload.api.stat import StatisticsApi
from pyload.api.user import UserApi

# Populate Api
Api.EXTEND = True

__api_classes = (
    AccountApi,
    AddonApi,
    ConfigApi,
    CoreApi,
    DownloadApi,
    UserExchangeApi,
    FileApi,
    PreDownloadApi,
    StatisticsApi,
    UserApi
)
for api in __api_classes:
    Api.extend(api)

Api.EXTEND = False
