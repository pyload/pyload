# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library
standard_library.install_aliases()

from .backend import DatabaseMethods


class StatisticMethods(DatabaseMethods):

    # __slots__ = []

    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
