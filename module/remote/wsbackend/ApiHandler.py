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

from mod_pywebsocket.util import get_class_logger
from mod_pywebsocket.msgutil import receive_message, send_message
from module.remote.json_converter import loads, dumps

class ApiHandler:
    """Provides access to the API.

    Send your request as json encoded string in the following manner:
    ["function", [*args]] or ["function", {**kwargs}]

    the result will be:

    [code, result]

    Don't forget to login first.
    Non json request will be ignored.
    """

    def __init__(self, api):
        self.log = get_class_logger()
        self.api = api

    def do_extra_handshake(self, req):
        self.log.debug("WS Connected: %s" % req)

    def transfer_data(self, req):

        while True:
            try:
                line = receive_message(req)
                self.handle_message(line, req)
            except TypeError, e: # connection closed
                print e
                return

    def passive_closing_handshake(self, req):
        self.log.debug("WS Closed: %s" % req)

    def handle_message(self, msg, req):
        try:
            o = loads(msg)
        except ValueError, e: #invalid json object
            self.log.debug("Invalid Request: %s" % e)
            return

        if type(o) != list and len(o) > 2:
            self.log.debug("Invalid Api call: %s" % o)
            return self.send_result(req, 500, "Invalid Api call")
        if len(o) == 1: # arguments omitted
            o.append([])

        func, args = o
        if type(args) == list:
            kwargs = {}
        else:
            args, kwargs = [], args

        if func == 'login':
            user =  self.api.checkAuth(*args, **kwargs)
            if user:
                req.api = self.api.withUserContext(user.uid)
                return self.send_result(req, 200, True)

            else:
                return self.send_result(req, 403, "Forbidden")

        elif func == 'logout':
            req.api = None
            return self.send_result(req, 200, True)

        else:
            if not req.api:
                return self.send_result(req, 403, "Forbidden")

            if not self.api.isAuthorized(func, req.api.user):
                return self.send_result(req, 401, "Unauthorized")

            try:
                result = getattr(req.api, func)(*args, **kwargs)
            except AttributeError:
                return self.send_result(req, 404, "Not Found")
            except Exception, e:
                return self.send_result(req, 500, str(e))

            # None is invalid json type
            if result is None: result = True

            return self.send_result(req, 200, result)


    def send_result(self, req, code, result):
        return send_message(req, dumps([code, result]))