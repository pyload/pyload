# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
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

from __future__ import absolute_import
from __future__ import unicode_literals
import logging

from .RemoteManager import BackendBase

from mod_pywebsocket import util


def get_class_logger(o=None):
    return logging.getLogger('log')

# Monkey patch for our logger
util.get_class_logger = get_class_logger


class WebSocketBackend(BackendBase):
    def setup(self, host, port):

        from .wsbackend.Server import WebSocketServer, DefaultOptions
        from .wsbackend.Dispatcher import Dispatcher
        from .wsbackend.ApiHandler import ApiHandler
        from .wsbackend.AsyncHandler import AsyncHandler

        options = DefaultOptions()
        options.server_host = host
        options.port = port
        options.dispatcher = Dispatcher()
        options.dispatcher.addHandler(ApiHandler.PATH, ApiHandler(self.core.api))
        options.dispatcher.addHandler(AsyncHandler.PATH, AsyncHandler(self.core.api))

        # tls is needed when requested or webui is also on tls
        if self.core.api.isWSSecure():
            from .wsbackend.Server import import_ssl
            tls_module = import_ssl()
            if tls_module:
                options.use_tls = True
                options.tls_module = tls_module
                options.certificate = self.core.config['ssl']['cert']
                options.private_key = self.core.config['ssl']['key']
                self.core.log.info(_('Using secure WebSocket'))
            else:
                self.core.log.warning(_('SSL could not be imported'))

        self.server = WebSocketServer(options)

    def serve(self):
        self.server.serve_forever()
