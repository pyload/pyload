# -*- coding: utf-8 -*-
# @author: vuolter

from .init import Api, requireperm, statestring
from .base import AbstractApi, BaseApi
from .account import AccountApi
from .addon import AddonApi
from .config import ConfigApi
from .core import CoreApi
from .download import DownloadApi
from .file import FileApi
from .interaction import UserInteractionApi
from .predownload import PreDownloadApi
from .stat import StatisticsApi
from .user import UserApi

# Populate Api
Api.EXTEND = True

__api_classes = (
    AccountApi,
    AddonApi,
    ConfigApi,
    CoreApi,
    DownloadApi,
    FileApi,
    UserInteractionApi,
    PreDownloadApi,
    StatisticsApi,
    UserApi)
for api in __api_classes:
    Api.extend(api)

Api.EXTEND = False

# Cleanup
del __api_classes
