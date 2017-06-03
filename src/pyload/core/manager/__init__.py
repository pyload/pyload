# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import unicode_literals
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from .plugin import PluginManager
from .account import AccountManager
from .addon import AddonManager
from .base import BaseManager
from .config import ConfigManager
from .event import EventManager
from .exchange import ExchangeManager
from .file import FileManager
from .info import InfoManager
from .transfer import TransferManager
