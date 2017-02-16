# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
from mod_pywebsocket import util
from mod_pywebsocket.dispatch import Dispatcher as BaseDispatcher


class Dispatcher(BaseDispatcher):

    def __init__(self):
        self._logger = util.get_class_logger(self)

        self._handler_suite_map = {}
        self._source_warnings = []

    def add_handler(self, path, handler):
        self._handler_suite_map[path] = handler
