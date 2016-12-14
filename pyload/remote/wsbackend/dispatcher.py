# -*- coding: utf-8 -*-
# @author: RaNaN

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
