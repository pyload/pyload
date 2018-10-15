# -*- coding: utf-8 -*-
# @author: RaNaN

import bottle

from pyload.api import PERMS, ROLE
from pyload.api import has_permission
from pyload.webui import PREFIX, env
from pyload.webui.server_thread import PYLOAD_API


def get_themedir():
    theme = PYLOAD_API.getConfigValue("webui", "theme").lower()
    return os.path.join('themes', theme)
    
    
def render_to_response(path, args={}, proc=[]):
    for p in proc:
        args.update(p())
    t = env.get_template(path, get_themedir())
    return t.render(**args)


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


def set_session(request, info):
    s = bottle.request.environ.get("beaker.session")
    s["authenticated"] = True
    s["user_id"] = info["id"]
    s["name"] = info["name"]
    s["role"] = info["role"]
    s["perms"] = info["permission"]
    s["template"] = info["template"]
    s.save()

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
        core_apiver = PYLOAD_API.__version__
        if int(kwargs.get("apiver", core_apiver).strip("v")) < core_apiver:
            return bottle.HTTPError(404, json.dumps("Obsolete API"))
        return func(*args, **kwargs)

    return _view


def login_required(perm=None):
    def _dec(func):
        def _view(*args, **kwargs):
            s = bottle.request.environ.get("beaker.session")
            if s.get("name", None) and s.get("authenticated", False):
                if perm:
                    perms = parse_permissions(s)
                    if perm not in perms or not perms[perm]:
                        if bottle.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                            return bottle.HTTPError(403, json.dumps("Forbidden"))
                        else:
                            return bottle.redirect("{}/nopermission".format(PREFIX))

                return func(*args, **kwargs)
            else:
                if bottle.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return bottle.HTTPError(403, json.dumps("Forbidden"))
                else:
                    return bottle.redirect("{}/login".format(PREFIX))

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
