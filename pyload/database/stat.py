# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future import standard_library

from pyload.database import DatabaseMethods

standard_library.install_aliases()


class StatisticMethods(DatabaseMethods):

    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
