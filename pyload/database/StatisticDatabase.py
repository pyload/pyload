#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.database import DatabaseMethods, queue, async, inner


class StatisticMethods(DatabaseMethods):
    def addEntry(self, user, plugin, premium, amount):
        pass


StatisticMethods.register()
