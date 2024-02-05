# -*- coding: utf-8 -*-

import json
from functools import wraps
from urllib.parse import urljoin, urlparse

import flask
import flask_themes2
import werkzeug.routing
from pyload.core.api import Perms, Role, has_permission


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return dict(obj)
        except TypeError:
            pass
        return super().default(obj)


try:
    JSONProviderBase = flask.json.provider.JSONProvider
except AttributeError:
    pass
else:
    class JSONProvider(JSONProviderBase):
        def dumps(self, obj, **kwargs):
            return json.dumps(obj, **kwargs, cls=JSONEncoder)

        def loads(self, s, **kwargs):
            return json.loads(s, **kwargs)


#: Checks if location belongs to same host address
def is_safe_url(location):
    location_urlp = urlparse(location)
    #: if relative URL then must start with "/"
    if not location_urlp.netloc and location[0] != "/":
        return False
    host_urlp = urlparse(flask.request.host_url)
    test_urlp = urlparse(urljoin(flask.request.host_url, location))
    return test_urlp.scheme in ('http', 'https') and host_urlp.netloc == test_urlp.netloc


def get_redirect_url(fallback=None):
    next_arg = flask.request.values.get("next")
    redirect_url = flask.url_for(fallback)
    if next_arg and next_arg != "login":  # don't redirect to same location
        try:
            redirect_url = flask.url_for(f"app.{next_arg}")
        except werkzeug.routing.BuildError:
            pass

    return urljoin(flask.request.url_root, redirect_url)


def render_base(messages):
    return render_template("base.html", messages=messages)


def clear_session(session=flask.session, permanent=True):
    session.permanent = bool(permanent)
    session.clear()
    # session.modified = True


def current_theme_id():
    api = flask.current_app.config["PYLOAD_API"]
    return api.get_config_value("webui", "theme").lower()


#: tries to serve the file from the static directory of the current theme otherwise fallback to builtin one
def static_file_url(filename):
    themeid = current_theme_id()
    try:
        url = flask_themes2.static_file_url(themeid, filename)
    except KeyError:
        url = flask.url_for("static", filename=filename)
    return url


def theme_template(filename):
    return flask.url_for("app.render", filename=filename)


#: tries to render the template of the current theme otherwise fallback to builtin template
def render_template(template, **context):
    themeid = current_theme_id()
    return flask_themes2.render_theme_template(themeid, template, **context)


def parse_permissions(session=flask.session):
    perms = {x.name: False for x in Perms}
    perms["ADMIN"] = False
    perms["is_admin"] = False

    if not session.get("authenticated", False):
        return perms

    perms["ANY"] = True
    if session.get("role") == Role.ADMIN:
        for key in perms.keys():
            perms[key] = True

    elif session.get("perms"):
        p = session.get("perms")
        perms.update(get_permission(p))

    return perms


def permlist():
    return [x.name for x in Perms if x.name != "ANY"]


def get_permission(userperms):
    """
    Returns a dict with permission key.

    :param userperms: permission bits
    """
    return {
        name: has_permission(userperms, getattr(Perms, name).value)
        for name in permlist()
    }


def set_permission(perms):
    """
    generates permission bits from dictionary.

    :param perms: dict
    """
    permission = 0
    for name in permlist():
        if name.startswith("_"):
            continue

        if name in perms and perms[name]:
            permission |= getattr(Perms, name)

    return permission


def set_session(user_info, session=flask.session, permanent=True):
    session.permanent = bool(permanent)
    session.update(
        {
            "authenticated": True,
            "id": user_info["id"],
            "name": user_info["name"],
            "role": user_info["role"],
            "perms": user_info["permission"],
            "template": user_info["template"],
        }
    )
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
    api = flask.current_app.config["PYLOAD_API"]
    user = session.get("name")
    authenticated = session.get("authenticated")

    return authenticated and api.user_exists(user)


def login_required(perm):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            s = flask.session
            #: already authenticated?
            if is_authenticated(s):
                perms = parse_permissions(s)
                if perm not in perms or not perms[perm]:
                    response = "Forbidden", 403
                else:
                    response = func(*args, **kwargs)

            else:
                clear_session(s)
                if flask.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    response = "Forbidden", 403

                else:
                    location = flask.url_for(
                        "app.login",
                        next=flask.request.endpoint.split(".")[-1]
                    )
                    response = flask.redirect(location)

            return response

        return wrapper

    return decorator
