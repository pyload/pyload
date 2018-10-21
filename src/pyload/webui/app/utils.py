# -*- coding: utf-8 -*-
# @author: RaNaN

import json
import os

import jinja2
import flask
import flask_themes2

from pyload.api import PERMS, ROLE, has_permission


def clear_session():
    flask.session.clear()
    flask.session.modified = True

    
def render_template(template, context={}, proc=[]):
    for p in proc:
        context.update(p())
    api = flask.current_app.config['PYLOAD_API']
    theme = api.getConfigValue("webui", "theme").lower()
    return flask_themes2.render_theme_template(theme, template, **context)

    
def parse_permissions(session):
    perms = {x: False for x in dir(PERMS) if not x.startswith("_")}
    perms["ADMIN"] = False
    perms["is_admin"] = False

    if not session.get("authenticated", False):
        return perms

    if session.get("role") == ROLE.ADMIN:
        for k in perms.keys():
            perms[k] = True

    elif session.get("perms"):
        p = session.get("perms")
        get_permission(perms, p)

    return perms


def permlist():
    return [x for x in dir(PERMS) if not x.startswith("_") and x != "ALL"]


def get_permission(perms, p):
    """
    Returns a dict with permission key.

    :param perms: dictionary
    :param p:  bits
    """
    for name in permlist():
        perms[name] = has_permission(p, getattr(PERMS, name))


def set_permission(perms):
    """
    generates permission bits from dictionary.

    :param perms: dict
    """
    permission = 0
    for name in dir(PERMS):
        if name.startswith("_"):
            continue

        if name in perms and perms[name]:
            permission |= getattr(PERMS, name)

    return permission


def set_session(info):
    s = flask.session
    s["authenticated"] = True
    s["user_id"] = info["id"]
    s["name"] = info["name"]
    s["role"] = info["role"]
    s["perms"] = info["permission"]
    s["template"] = info["template"]
    s.modified = True
    return s


def parse_userdata(session):
    return {
        "name": session.get("name", "Anonymous"),
        "is_admin": session.get("role", 1) == 0,
        "is_authenticated": session.get("authenticated", False),
    }


def apiver_check(func):
    # if no apiver is provided assumes latest
    def _view(*args, **kwargs):
        api = flask.current_app.config['PYLOAD_API']
        core_apiver = api.__version__
        if int(kwargs.get("apiver", core_apiver).strip("v")) < core_apiver:
            return "Obsolete API", 404
        return func(*args, **kwargs)

    return _view


def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):
            s = flask.session
            if s.get("name", None) and s.get("authenticated", False):
                if perm:
                    perms = parse_permissions(s)
                    if perm not in perms or not perms[perm]:
                        if (
                            flask.request.headers.get("X-Requested-With")
                            == "XMLHttpRequest"
                        ):
                            return "Forbidden", 403
                        else:
                            return flask.redirect("/nopermission")

                return func(*args, **kwargs)
            else:
                if flask.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return "Forbidden", 403
                else:
                    return flask.redirect("/login")

        return _view

    return _dec


def toDict(obj):
    ret = {}
    for att in obj.__slots__:
        ret[att] = getattr(obj, att)
    return ret


# class CherryPyWSGI(bottle.ServerAdapter):
    # def run(self, handler):
        # from wsgiserver import CherryPyWSGIServer

        # server = CherryPyWSGIServer((self.host, self.port), handler)
        # server.start()
