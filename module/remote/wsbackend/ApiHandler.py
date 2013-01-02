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

from mod_pywebsocket.msgutil import receive_message

from module.Api import ExceptionObject

from AbstractHandler import AbstractHandler

class ApiHandler(AbstractHandler):
    """Provides access to the API.

    Send your request as json encoded string in the following manner:
    ["function", [*args]] or ["function", {**kwargs}]

    the result will be:

    [code, result]

    Don't forget to login first.
    Non json request will be ignored.
    """

    PATH = "/api"

    def transfer_data(self, req):
        while True:
            try:
                line = receive_message(req)
            except TypeError, e: # connection closed
                self.log.debug("WS Error: %s" % e)
                return self.passive_closing_handshake(req)

            self.handle_message(line, req)

    def handle_message(self, msg, req):

        func, args, kwargs = self.handle_call(msg, req)
        if not func:
            return # handle_call already sent the result

        if func == 'login':
            user =  self.api.checkAuth(*args, **kwargs)
            if user:
                req.api = self.api.withUserContext(user.uid)
                return self.send_result(req, self.OK, True)

            else:
                return self.send_result(req, self.OK, False)

        elif func == 'logout':
            req.api = None
            return self.send_result(req, self.OK, True)

        else:
            if not req.api:
                return self.send_result(req, self.FORBIDDEN, "Forbidden")

            if not self.api.isAuthorized(func, req.api.user):
                return self.send_result(req, self.UNAUTHORIZED, "Unauthorized")

            try:
                result = getattr(req.api, func)(*args, **kwargs)
            except ExceptionObject, e:
                return self.send_result(req, self.BAD_REQUEST, e)
            except AttributeError:
                return self.send_result(req, self.NOT_FOUND, "Not Found")
            except Exception, e:
                self.core.print_exc()
                return self.send_result(req, self.ERROR, str(e))

            # None is invalid json type
            if result is None: result = True

            return self.send_result(req, self.OK, result)