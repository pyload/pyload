# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   https://pyload.net
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from __future__ import unicode_literals
from mod_pywebsocket import util
from mod_pywebsocket.dispatch import Dispatcher as BaseDispatcher


class Dispatcher(BaseDispatcher):

    def __init__(self):
        self._logger = util.get_class_logger(self)

        self._handler_suite_map = {}
        self._source_warnings = []

    def addHandler(self, path, handler):
        self._handler_suite_map[path] = handler
