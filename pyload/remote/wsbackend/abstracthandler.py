# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import range
from past.builtins import basestring
from builtins import object
from mod_pywebsocket.msgutil import send_message
from mod_pywebsocket.util import get_class_logger

from pyload.Api import UserData
from pyload.remote.json_converter import loads, dumps


class AbstractHandler(object):
    """
        Abstract Handler providing common methods shared across WebSocket handlers
    """
    PATH = "/"

    OK = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    ERROR = 500

    def __init__(self, api):
        self.log = get_class_logger()
        self.api = api
        self.pyload = api.pyload

    def do_extra_handshake(self, req):
        self.log.debug("WS Connected: %s" % req)
        req.api = None #when api is set client is logged in

        # allow login via session when webinterface is active
        cookie = req.headers_in.getheader('Cookie')
        s = self.load_session(cookie)
        if s:
            uid = s.get('uid', None)
            req.api = self.api.withUserContext(uid)
            self.log.debug("WS authenticated user with cookie: %d" % uid)

        self.on_open(req)

    def on_open(self, req):
        pass

    def load_session(self, cookies):
        from http.cookies import SimpleCookie
        from beaker.session import Session
        from pyload.web.webinterface import session

        cookies = SimpleCookie(cookies)
        sid = cookies.get(session.options['key'])
        if not sid:
            return None

        s = Session({}, use_cookies=False, id=sid.value, **session.options)
        if s.is_new:
            return None

        return s

    def passive_closing_handshake(self, req):
        self.log.debug("WS Closed: %s" % req)
        self.on_close(req)

    def on_close(self, req):
        pass

    def transfer_data(self, req):
        raise NotImplemented

    def handle_call(self, msg, req):
        """ Parses the msg for an argument call. If func is null an response was already sent.

        :return: func, args, kwargs
        """
        try:
            o = loads(msg)
        except ValueError as e: #invalid json object
            self.log.debug("Invalid Request: %s" % e)
            self.send_result(req, self.ERROR, "No JSON request")
            return None, None, None

        if not isinstance(o, basestring) and not isinstance(o, list) and len(o) not in range(1, 4):
            self.log.debug("Invalid Api call: %s" % o)
            self.send_result(req, self.ERROR, "Invalid Api call")
            return None, None, None

        # called only with name, no args
        if isinstance(o, basestring):
            return o, [], {}
        elif len(o) == 1: # arguments omitted
            return o[0], [], {}
        elif len(o) == 2:
            func, args = o
            if isinstance(args, list):
                return func, args, {}
            else:
                return func, [], args
        else:
            return tuple(o)

    def do_login(self, req, args, kwargs):
        user = None
        # Cookies login when one argument is given
        if len(args) == 1:
            s = self.load_session(args)
            if s:
                user = UserData(uid=s.get('uid', None))
        else:
            s = self.api.checkAuth(*args, **kwargs)
            if s:
                user = UserData(uid=s.uid)

        if user:
            req.api = self.api.withUserContext(user.uid)
            return self.send_result(req, self.OK, True)
        else:
            return self.send_result(req, self.FORBIDDEN, "Forbidden")

    def do_logout(self, req):
        req.api = None
        return self.send_result(req, self.OK, True)

    def send_result(self, req, code, result):
        return send_message(req, dumps([code, result]))

    def send(self, req, obj):
        return send_message(req, dumps(obj))
