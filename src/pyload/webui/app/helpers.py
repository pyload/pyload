# -*- coding: utf-8 -*-
# @author: RaNaN


import flask
import flask_themes2
import flask_login

from pyload.core.api import PERMS, ROLE, has_permission
from urllib.parse import urlparse, urljoin
from flask import request, url_for
from functools import wraps

# class User(UserMixin):

    # def __init__(self, id):
        # self.id = id
        
    # def is_active(self):
        # """True, as all users are active."""
        # return True

    # def get_id(self):
        # """Return the email address to satisfy Flask-Login's requirements."""
        # return self.email

    # def is_authenticated(self):
        # """Return True if the user is authenticated."""
        # return self.authenticated

    # def is_anonymous(self):
        # """False, as anonymous users aren't supported."""
        # return False
        
        
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
            
           
def pre_processor():
    s = flask.session
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    api = flask.current_app.config["PYLOAD_API"]

    if user["is_authenticated"]:
        status = api.statusServer()
        captcha = api.isCaptchaWaiting()

        # check if update check is available
        info = api.getInfoByPlugin("UpdateManager")
        if info:
            update = info["pyload"] == "True"
            plugins = info["plugins"] == "True"

    return {
        "user": user,
        "status": status,
        "captcha": captcha,
        "perms": perms,
        "url": flask.request.url,
        "update": update,
        "plugins": plugins,
    }


def base(messages):
    return render_template("base.html", {"messages": messages}, [pre_processor])
    
    
def clear_session():
    flask.session.clear()
    flask.session.modified = True


def render_template(template, context={}, proc=[]):
    for p in proc:
        context.update(p())
    api = flask.current_app.config["PYLOAD_API"]
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
    s["id"] = info["id"]
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
    @wraps(func)
    def wrapper(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        core_apiver = api.__version__
        if int(kwargs.get("apiver", core_apiver).strip("v")) < core_apiver:
            return "Obsolete API", 404
        return func(*args, **kwargs)

    return wrapper


def login_required(perm=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if flask.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return "Forbidden", 403
                            
            s = flask.session
            if s.get("name", None) and s.get("authenticated", False):
                if perm:
                    perms = parse_permissions(s)
                    if perm not in perms or not perms[perm]:
                        return flask.redirect(flask.url_for("nopermission"))
                return func(*args, **kwargs)
                
            api = flask.current_app.config["PYLOAD_API"]
            autologin = api.getConfigValue("webui", "autologin")
            if autologin:  # TODO: check if localhost
                users = api.getAllUserData()
                if len(users) == 1:
                    info = next(iter(users.values()))
                    set_session(info)
                    return func(*args, **kwargs)
            
            return flask_login.login_url("app.login", flask.request.url)

        return wrapper

    return decorator


def toDict(obj):
    ret = {}
    for att in obj.__slots__:
        ret[att] = getattr(obj, att)
    return ret
    