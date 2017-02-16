# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from pyload.database import DatabaseMethods


class StatisticMethods(DatabaseMethods):

    def add_entry(self, user, plugin, premium, amount):
        raise NotImplementedError


StatisticMethods.register()
