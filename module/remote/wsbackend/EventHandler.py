#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
#   http://www.pyload.org
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

from threading import Lock


from module.utils import lock
from AbstractHandler import AbstractHandler

class EventHandler(AbstractHandler):

    def __init__(self, api):
        AbstractHandler.__init__(self, api)
        self.clients = []
        self.lock = Lock()

    @lock
    def on_open(self, req):
        self.clients.append(req)

    @lock
    def on_close(self, req):
        self.clients.remove(req)

    def handle_message(self, line, req):
        pass