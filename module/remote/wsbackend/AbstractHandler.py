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

from mod_pywebsocket.msgutil import send_message
from mod_pywebsocket.util import get_class_logger
from module.remote.json_converter import loads, dumps


class AbstractHandler:
    """
        Abstract Handler providing common methods shared across WebSocket handlers
    """

    def __init__(self, api):
        self.log = get_class_logger()
        self.api = api

    def do_extra_handshake(self, req):
        self.log.debug("WS Connected: %s" % req)
        self.on_open(req)

    def on_open(self, req):
        pass

    def passive_closing_handshake(self, req):
        self.log.debug("WS Closed: %s" % req)
        self.on_close(req)

    def on_close(self, req):
        pass

    def transfer_data(self, req):
        raise NotImplemented

    def handle_call(self, msg, req):
        """ Parses the msg for an argument call. If func is null an response was already sent.

        :param msg:
        :param req:
        :return: func, args, kwargs
        """
        try:
            o = loads(msg)
        except ValueError, e: #invalid json object
            self.log.debug("Invalid Request: %s" % e)
            return None, None, None

        if type(o) != list and len(o) > 2:
            self.log.debug("Invalid Api call: %s" % o)
            self.send_result(req, 500, "Invalid Api call")
            return None, None, None
        if len(o) == 1: # arguments omitted
            o.append([])

        func, args = o
        if type(args) == list:
            kwargs = {}
        else:
            args, kwargs = [], args

        return func, args, kwargs

    def send_result(self, req, code, result):
        return send_message(req, dumps([code, result]))