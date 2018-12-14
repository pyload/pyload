# -*- coding: utf-8 -*-
# AUTHOR: RaNaN


from functools import partial, wraps
from urllib.parse import urljoin, urlparse

import flask
import flask_themes2

from pyload.core.api import PERMS, ROLE, has_permission
    

#: Check if location belongs to same host address
def is_safe_url(location):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, location))
    return ref_url.netloc == test_url.netloc


def get_redirect_url(fallback=None):
    for location in flask.request.values.get('next'), flask.request.referrer:
        if not location:
            continue
        if location == flask.request.url:  # don't redirect to same location
            continue
        if is_safe_url(location):
            return location
    return fallback
           
           
def render_base(messages):
    return render_template("base.html", messages=messages)


def render_error(messages):
    return render_template("error.html", messages=messages)


def clear_session(session=flask.session, permanent=True):
    session.permanent = bool(permanent)
    session.clear()
    # session.modified = True


def render_template(template, **context):
    api = flask.current_app.config["PYLOAD_API"]
    theme = api.getConfigValue("webui", "theme").lower()
    return flask_themes2.render_theme_template(theme, template, **context)


def parse_permissions(session=flask.session):
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


def set_session(user_info, session=flask.session, permanent=True):
    session.permanent = bool(permanent)
    session.update({
        "authenticated": True,
        "id": user_info["id"],
        "name": user_info["name"],
        "role": user_info["role"],
        "perms": user_info["permission"],
        "template": user_info["template"]
    })
    # session.modified = True
    return session


# TODO: Recheck...
def parse_userdata(session=flask.session):
    return {
        "name": session.get("name", "Anonymous"),
        "is_admin": session.get("role", 1) == 0,
        "is_authenticated": session.get("authenticated", False),
    }


def apiver_check(func):
    # if no apiver is provided assumes latest
    @wraps(func)
    def wrapper(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        core_apiver = api.__version__
        if int(kwargs.get("apiver", core_apiver).strip("v")) < core_apiver:
            return "Obsolete API", 404
        return func(*args, **kwargs)

    return wrapper


def is_authenticated(session=flask.session):
    return session.get("name") and session.get("authenticated")  # NOTE: why checks name?


def login_required(perm):

    def decorator(func):
    
        @wraps(func)
        def wrapper(*args, **kwargs):
            s = flask.session
            #: already authenticated
            if is_authenticated(s):
                perms = parse_permissions(s)
                if perm not in perms or not perms[perm]:
                    response = "Forbidden", 403
                else:
                    response = func(*args, **kwargs)
                
            elif flask.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                response = "Forbidden", 403     
                
            else:
                location = flask.url_for("app.login", next=flask.request.url)
                response = flask.redirect(location)
                
            return response

        return wrapper

    return decorator
    

def toDict(obj):
    ret = {}
    for att in obj.__slots__:
        ret[att] = getattr(obj, att)
    return ret
