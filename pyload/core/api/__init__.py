# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from .init import Api
from .init import requireperm
from .init import statestring
from .base import AbstractApi
from .base import BaseApi
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
