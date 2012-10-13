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

from Queue import Queue
from threading import Lock

from mod_pywebsocket.msgutil import receive_message

from module.utils import lock
from AbstractHandler import AbstractHandler

class Mode:
    STANDBY = 1
    RUNNING = 2

class AsyncHandler(AbstractHandler):
    """
        Handler that provides asynchronous information about server status, running downloads, occurred events.

        Progress information are continuous and will be pushed in a fixed interval when available.
        After connect you have to login and can set the interval by sending the json command ["setInterval", xy].
        To start receiving updates call "start", afterwards no more incoming messages will be accept!
    """

    PATH = "/async"
    COMMAND = "start"

    PROGRESS_INTERVAL = 1
    STATUS_INTERVAL  = 60

    def __init__(self, api):
        AbstractHandler.__init__(self, api)
        self.clients = []
        self.lock = Lock()

    @lock
    def on_open(self, req):
        req.queue = Queue()
        req.interval = self.PROGRESS_INTERVAL
        req.mode = Mode.STANDBY
        self.clients.append(req)

    @lock
    def on_close(self, req):
        self.clients.remove(req)

    @lock
    def add_event(self, event):
        for req in self.clients:
            req.queue.put(event)

    def transfer_data(self, req):
        while True:

            if req.mode == Mode.STANDBY:
                try:
                    line = receive_message(req)
                except TypeError, e: # connection closed
                    self.log.debug("WS Error: %s" % e)
                    return self.passive_closing_handshake(req)

                self.mode_standby(line, req)
            else:
                if self.mode_running(req):
                    return self.passive_closing_handshake(req)

    def mode_standby(self, msg, req):
        """ accepts calls  before pushing updates """
        func, args, kwargs = self.handle_call(msg, req)
        if not func:
            return # Result was already sent

        if func == 'login':
            user =  self.api.checkAuth(*args, **kwargs)
            if user:
                req.api = self.api.withUserContext(user.uid)
                return self.send_result(req, self.OK, True)

            else:
                return self.send_result(req, self.FORBIDDEN, "Forbidden")

        elif func == 'logout':
            req.api = None
            return self.send_result(req, self.OK, True)

        else:
            if not req.api:
                return self.send_result(req, self.FORBIDDEN, "Forbidden")
            if func == "setInterval":
                req.interval = args[0]
            elif func == self.COMMAND:
                req.mode = Mode.RUNNING


    def mode_running(self, req):
        """  Listen for events, closes socket when returning True """
        self.send_result(req, "update", "test")