#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
from bottle import request, HTTPError, redirect, ServerAdapter

from webinterface import env, TEMPLATE, PYLOAD

def render_to_response(name, args={}, proc=[]):
    for p in proc:
        args.update(p())
    t = env.get_or_select_template((TEMPLATE + "/" + name, "default/" + name))
    return t.render(**args)


def set_session(request, user):
    s = request.environ.get('beaker.session')
    s["uid"] = user.uid
    s.save()
    return s

def get_user_api(s):
    uid = s.get("uid", None)
    if uid is not None:
        api = PYLOAD.withUserContext(uid)
        return api

    return None

def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):
            s = request.environ.get('beaker.session')
            api = get_user_api(s)
            if api is not None:
                if perm:
                    if api.user.hasPermission(perm):
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return HTTPError(403, "Forbidden")
                        else:
                            return redirect("/nopermission")

                kwargs["api"] = api
                return func(*args, **kwargs)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HTTPError(403, "Forbidden")
                else:
                    return redirect("/login")

        return _view

    return _dec


class CherryPyWSGI(ServerAdapter):
    def run(self, handler):
        from wsgiserver import CherryPyWSGIServer

        server = CherryPyWSGIServer((self.host, self.port), handler)
        server.start()
