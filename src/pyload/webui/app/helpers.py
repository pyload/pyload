# -*- coding: utf-8 -*-

from functools import wraps
from urllib.parse import unquote, urljoin, urlparse

import flask
import flask_themes2
from flask_oidc import OpenIDConnect as BaseOpenIDConnect
from pyload.core.api import Perms, Role, has_permission

class OpenIDConfig:
    map = {
        "auth_uri": ["webui", "oidc_auth_uri"],
        "userinfo_uri": ["webui", "oidc_userinfo_uri"],
        "token_uri": ["webui", "oidc_token_uri"],
        "client_id": ["webui", "oidc_client_id"],
        "client_secret": ["webui", "oidc_client_secret"],
        "issuer": ["webui", "oidc_issuer"]
    }

    def __init__(self, pyload):
        self.pyload = pyload

    def get_issuer(self):
        config = self.pyload.config
        scheme = "https" if config.get('webui', 'use_ssl') else "http"
        host = config.get('webui', 'host')
        port = config.get('webui', 'port')
        port_str = "" if ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)) else f":{port}"
        return f"{scheme}://{host}{port_str}"

    def get(self, key):
        if key in ("revoke_uri",):
            return None
        if key in self.__class__.map.keys():
            return self.pyload.config.get(*self.__class__.map.get(key))

        raise KeyError

    def __getitem__(self, item):
        if type(item) == int:
            keys = ["revoke_uri"]
            for k in self.__class__.map.keys():
                keys.append(k)
            return self.get(keys[item])
        return self.get(item)

    def __iter__(self):
        yield "revoke_uri"
        for k in self.__class__.map.keys():
            yield k

    def __missing__(self, key):
        pass
    def __getattr__(self, item):
        return self.get(item)


class OpenIDConnect(BaseOpenIDConnect):
    def __init__(self, pyload, app):
        self.pyload = pyload
        self.config = OpenIDConfig(pyload)
        app.config.setdefault("OIDC_CLIENT_SECRETS", None)
        app.config.setdefault("OIDC_CALLBACK_ROUTE", '/oidc_callback')
        app.config.setdefault("OIDC_SCOPES", ['openid', 'dynamic'])
        super().__init__(app)
    def load_secrets(self, app):
        return {"web": self.config}

class JSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        try:
            return dict(obj)
        except TypeError:
            pass
        return super().default(obj)


#: Checks if location belongs to same host address
def is_safe_url(location):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, location))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_url(fallback=None):
    login_url = urljoin(flask.request.url_root, flask.url_for('app.login'))
    request_url = unquote(flask.request.url)
    for location in flask.request.values.get("next"), flask.request.referrer:
        if not location:
            continue
        if location in (request_url, login_url):  # don't redirect to same location
            continue
        if is_safe_url(location):
            return location
    return fallback


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
                        next=flask.request.url
                    )
                    response = flask.redirect(location)

            return response

        return wrapper

    return decorator
