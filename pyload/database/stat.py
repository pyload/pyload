# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.database import DatabaseMethods, queue, async, inner


class StatisticMethods(DatabaseMethods):
    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
