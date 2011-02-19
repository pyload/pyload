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
    along with this plrogram; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
from bottle import request, HTTPError, redirect, ServerAdapter

from webinterface import env, TEMPLATE

from module.database.UserDatabase import has_permission, PERMS, ROLE

def render_to_response(name, args={}, proc=[]):
    for p in proc:
        args.update(p())

    t = env.get_template(TEMPLATE + "/" + name)
    return t.render(**args)

def parse_permissions(session):
    perms = {"add": False,
             "delete": False,
            "status": False,
            "see_downloads": False,
            "download" : False,
            "settings": False}

    if not session.get("authenticated", False):
        return perms

    if session.get("role") == ROLE.ADMIN:
        for k in perms.iterkeys():
            perms[k] = True
    else:
        p = session.get("permission")
        perms["add"] = has_permission(p, PERMS.ADD)
        perms["delete"] = has_permission(p, PERMS.DELETE)
        perms["status"] = has_permission(p, PERMS.STATUS)
        perms["see_downloads"] = has_permission(p, PERMS.SEE_DOWNLOADS)
        perms["download"] = has_permission(p, PERMS.DOWNLOAD)
        perms["settings"] = has_permission(p, PERMS.SETTINGS)

    return perms

def parse_userdata(session):
    return {"name": session.get("name", "Anonymous"),
            "is_staff": True,
            "is_authenticated": session.get("authenticated", False)}

def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):
            s = request.environ.get('beaker.session')
            if s.get("name", None) and s.get("authenticated", False):
                if perm:
                    pass
                    #print perm
                return func(*args, **kwargs)
            else:
                if request.header.get('X-Requested-With') == 'XMLHttpRequest':
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
