# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from .backend import DatabaseMethods

standard_library.install_aliases()


class StatisticMethods(DatabaseMethods):

    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
