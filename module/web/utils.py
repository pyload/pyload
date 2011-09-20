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
	    "filemanager" : False,
            "settings": False,
            "is_admin": False}

    if not session.get("authenticated", False):
        return perms

    if session.get("role") == ROLE.ADMIN:
        for k in perms.iterkeys():
            perms[k] = True

    elif session.get("perms"):
        p = session.get("perms")
        get_permission(perms, p)

    return perms


def get_permission(perms, p):
    perms["add"] = has_permission(p, PERMS.ADD)
    perms["delete"] = has_permission(p, PERMS.DELETE)
    perms["status"] = has_permission(p, PERMS.STATUS)
    perms["see_downloads"] = has_permission(p, PERMS.SEE_DOWNLOADS)
    perms["download"] = has_permission(p, PERMS.DOWNLOAD)
    perms["settings"] = has_permission(p, PERMS.SETTINGS)
    perms["accounts"] = has_permission(p, PERMS.ACCOUNTS)

def set_permission(perms):
    permission = 0
    if perms["add"]:
        permission |= PERMS.ADD
    if perms["delete"]:
        permission |= PERMS.DELETE
    if perms["status"]:
        permission |= PERMS.STATUS
    if perms["see_downloads"]:
        permission |= PERMS.SEE_DOWNLOADS
    if perms["download"]:
        permission |= PERMS.DOWNLOAD
    if perms["settings"]:
        permission |= PERMS.SETTINGS
    if perms["accounts"]:
        permission |= PERMS.ACCOUNTS

    return permission


def set_session(request, info):
    s = request.environ.get('beaker.session')
    s["authenticated"] = True
    s["user_id"] = info["id"]
    s["name"] = info["name"]
    s["role"] = info["role"]
    s["perms"] = info["permission"]
    s["template"] = info["template"]
    s.save()

    return s

def parse_userdata(session):
    return {"name": session.get("name", "Anonymous"),
            "is_admin": True if session.get("role", 1) == 0 else False,
            "is_authenticated": session.get("authenticated", False)}

def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):
            s = request.environ.get('beaker.session')
            if s.get("name", None) and s.get("authenticated", False):
                if perm:
                    perms = parse_permissions(s)
                    if perm not in perms or not perms[perm]:
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return HTTPError(403, "Forbidden")
                        else:
                            return redirect("/nopermission")

                return func(*args, **kwargs)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return HTTPError(403, "Forbidden")
                else:
                    return redirect("/login")

        return _view

    return _dec

def toDict(obj):
    ret = {}
    for att in obj.__slots__:
        ret[att] = getattr(obj, att)
    return ret

class CherryPyWSGI(ServerAdapter):

    def run(self, handler):
        from wsgiserver import CherryPyWSGIServer

        server = CherryPyWSGIServer((self.host, self.port), handler)
        server.start()
