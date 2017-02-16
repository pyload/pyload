# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

from pyload.datatype.check import OnlineCheck
from pyload.datatype.file import PyFile
from pyload.datatype.package import PyPackage, RootPackage
from pyload.datatype.task import InteractionTask
from pyload.datatype.user import User

standard_library.install_aliases()
# from pyload.datatype.types import *
