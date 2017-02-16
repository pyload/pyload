# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

from pyload.database.account import AccountMethods
from pyload.database.backend import (DatabaseBackend, DatabaseMethods, async,
                                     inner, queue)
from pyload.database.config import ConfigMethods
from pyload.database.file import FileMethods
from pyload.database.stat import StatisticMethods
from pyload.database.storage import StorageMethods
from pyload.database.user import UserMethods

standard_library.install_aliases()
