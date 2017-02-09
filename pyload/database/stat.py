# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.database import DatabaseMethods
from pyload.database import async
from pyload.database import inner
from pyload.database import queue


class StatisticMethods(DatabaseMethods):

    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
