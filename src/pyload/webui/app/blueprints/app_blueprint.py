# -*- coding: utf-8 -*-

import datetime
import operator
import re
import os
import sys
import time
from urllib.parse import unquote
import mimetypes

import flask
from functools import wraps

from pyload import PKGDIR
from pyload.core.utils import format

from ..helpers import (
    clear_session,
    get_permission,
    get_redirect_url,
    is_authenticated,
    login_required,
    permlist,
    render_base,
    render_template,
    set_session,
    static_file_url,
)

from oauth2client.client import FlowExchangeError

_RE_LOGLINE = re.compile(r"\[([\d\-]+) ([\d:]+)\] +([A-Z]+) +(.+?) (.*)")

bp = flask.Blueprint("app", __name__)


@bp.route("/favicon.ico", endpoint="favicon")
def favicon():
    location = static_file_url("img/favicon.ico")
    return flask.redirect(location)


@bp.route("/render/<path:filename>", endpoint="render")
def render(filename):
    mimetype = mimetypes.guess_type(filename)[0] or "text/html"
    data = render_template(filename)
    return flask.Response(data, mimetype=mimetype)


@bp.route("/robots.txt", endpoint="robots")
def robots():
    return "User-agent: *\nDisallow: /"


# TODO: Rewrite login route using flask-login
@bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    api = flask.current_app.config["PYLOAD_API"]

    next = get_redirect_url(fallback=flask.url_for("app.dashboard"))

    if flask.request.method == "POST":
        if flask.request.form['submit'] == 'login_oidc':
            api = flask.current_app.config["PYLOAD_API"]
            user_info = None
            if api.oidc_user_loggedin():
                user_info = api.openid_login()
            else:
                return api.oidc_redirect_to_auth_server(customstate={"next": flask.url_for("app.login", values={"check_oidc"})})

        else:
            user = flask.request.form["username"]
            password = flask.request.form["password"]
            user_info = api.check_auth(user, password)

        if not user_info:
            return render_template("login.html", next=next, errors=True)

        set_session(user_info)
        flask.flash("Logged in successfully")
    elif flask.request.method == "GET" and 'oidc' in flask.request.values and not api.oidc_user_loggedin():
        return render_template("login.html", next=next, errors=True)

    if is_authenticated():
        return flask.redirect(next)

    if api.get_config_value("webui", "autologin"):
        allusers = api.get_all_userdata()
        if len(allusers) == 1:  # TODO: check if localhost
            user_info = list(allusers.values())[0]
            set_session(user_info)
            # NOTE: Double-check authentication here because if session[name] is empty,
            #       next login_required redirects here again and all loop out.
            if is_authenticated():
                return flask.redirect(next)

    return render_template("login.html", next=next)


@bp.route("/logout", endpoint="logout")
def logout():
    # logout_user()
    clear_session()
    return render_template("logout.html")

def require_oidc_login(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        wrapped = api.pyload.oidc.require_login(view_func, *args, **kwargs)
        res = wrapped()
        return res

    return decorated

def require_oidc_token(view_func):
    def decorated(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        wrapped = api.pyload.oidc.accept_token()
        res = wrapped(view_func)
        return res

    return decorated

def register_oidc_custom_callback(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        wrapped = api.pyload.oidc.custom_callback(view_func, *args, **kwargs)

    return decorated

def oidc_custom_callback(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        api = flask.current_app.config["PYLOAD_API"]
        wrapped = api.pyload.oidc.custom_callback(view_func, *args, **kwargs)
        try:
            res = wrapped()
        except FlowExchangeError:
            api.oidc_logout()
            return view_func()
        return res

    return decorated

@bp.route("/openid/login", endpoint="oidc_login")
def openid_login():
    api = flask.current_app.config["PYLOAD_API"]
    logged_in = False
    if api.oidc_user_loggedin():
        logged_in = api.openid_login()
    else:
        return api.oidc_redirect_to_auth_server(customstate={"next": flask.url_for("app.login")})

    if logged_in:
        return flask.redirect(get_redirect_url(fallback=flask.url_for("app.dashboard")))
    else:
        flask.flash("Log-in failed", category="error")
        return flask.redirect(get_redirect_url(fallback=flask.url_for("app.login")))

@bp.route("/openid/connect", endpoint="oidc_connect")
def openid_connect():
    register_oidc_custom_callback(openid_custom_callback)()
    api = flask.current_app.config["PYLOAD_API"]
    if not api.oidc_user_loggedin():
        return api.oidc_redirect_to_auth_server(customstate={"next": flask.url_for("app.oidc_connect")})
    api = flask.current_app.config["PYLOAD_API"]
    if not is_authenticated():
        flask.redirect(get_redirect_url(fallback=flask.url_for("app.dashboard")))
    user_id = flask.session.get('id')
    api.openid_connect(user_id)
    flask.flash("OpenId account linked", category="info")
    return flask.redirect(get_redirect_url(fallback=flask.url_for("app.dashboard")))

@bp.route("/oidc_callback", endpoint="oidc_callback")
@oidc_custom_callback
def openid_custom_callback(*args):
    api = flask.current_app.config["PYLOAD_API"]
    if is_authenticated() and api.oidc_user_loggedin():
        try:
            api.openid_connect()
        except Exception:
            flask.flash(message="Error linking OpenId", category="error")
        return flask.redirect(get_redirect_url(fallback=flask.url_for("app.dashboard")))
    elif api.openid_login():
        return flask.redirect(get_redirect_url(fallback=flask.url_for("app.dashboard")))
    else:
        return flask.redirect(flask.url_for("app.login", oidc=1))

@bp.route("/", endpoint="index")
@bp.route("/home", endpoint="home")
@bp.route("/dashboard", endpoint="dashboard")
@login_required("LIST")
def dashboard():
    api = flask.current_app.config["PYLOAD_API"]
    links = api.status_downloads()

    for link in links:
        if link["status"] == 12:
            current_size = link["size"] - link["bleft"]
            formatted_speed = format.speed(link["speed"])
            link["info"] = f"{current_size} KiB @ {formatted_speed}"

    return render_template("dashboard.html", res=links)


@bp.route("/queue", endpoint="queue")
@login_required("LIST")
def queue():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.get_queue()
    queue.sort(key=operator.attrgetter("order"))

    return render_template("packages.html", content=queue, target=1)


@bp.route("/collector", endpoint="collector")
@login_required("LIST")
def collector():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.get_collector()

    queue.sort(key=operator.attrgetter("order"))

    return render_template("packages.html", content=queue, target=0)


@bp.route("/files", endpoint="files")
@login_required("DOWNLOAD")
def files():
    api = flask.current_app.config["PYLOAD_API"]
    root = api.get_config_value("general", "storage_folder")

    if not os.path.isdir(root):
        messages = ["Download directory not found."]
        return render_base(messages)
    data = {"folder": [], "files": []}

    for entry in sorted(os.listdir(root)):
        if os.path.isdir(os.path.join(root, entry)):
            folder = {"name": entry, "path": entry, "files": []}
            files = os.listdir(os.path.join(root, entry))
            for file in sorted(files):
                try:
                    if os.path.isfile(os.path.join(root, entry, file)):
                        folder["files"].append(file)
                except Exception:
                    pass

            data["folder"].append(folder)

        elif os.path.isfile(os.path.join(root, entry)):
            data["files"].append(entry)

    return render_template("files.html", files=data)


@bp.route("/files/get/<path:path>", endpoint="get_file")
@login_required("DOWNLOAD")
def get_file(path):
    api = flask.current_app.config["PYLOAD_API"]
    path = unquote(path).replace("..", "")
    directory = api.get_config_value("general", "storage_folder")
    return flask.send_from_directory(directory, path, as_attachment=True)


@bp.route("/settings", endpoint="settings")
@login_required("SETTINGS")
def settings():
    api = flask.current_app.config["PYLOAD_API"]
    conf = api.get_config()
    plugin = api.get_plugin_config()

    conf_menu = []
    plugin_menu = []

    for entry in sorted(conf.keys()):
        conf_menu.append((entry, conf[entry].description))

    for entry in sorted(plugin.keys()):
        plugin_menu.append((entry, plugin[entry].description))

    accs = []

    for userdata in api.get_accounts(False):
        if userdata.trafficleft == -1:
            trafficleft = "unlimited"
        elif not userdata.trafficleft:
            trafficleft = "not available"
        else:
            trafficleft = format.size(userdata.trafficleft)

        if userdata.validuntil == -1:
            validuntil = "unlimited"
        elif not userdata.validuntil:
            validuntil = "not available"
        else:
            t = time.localtime(userdata.validuntil)
            validuntil = time.strftime("%d.%m.%Y", t)

        if "time" in userdata.options:
            try:
                _time = userdata.options["time"][0]
            except Exception:
                _time = ""
        else:
            _time = ""

        if "limit_dl" in userdata.options:
            try:
                limitdl = userdata.options["limit_dl"][0]
            except Exception:
                limitdl = "0"
        else:
            limitdl = "0"

        accs.append(
            {
                "type": userdata.type,
                "login": userdata.login,
                "valid": userdata.valid,
                "premium": userdata.premium,
                "trafficleft": trafficleft,
                "validuntil": validuntil,
                "limitdl": limitdl,
                "time": _time,
            }
        )

    all_users = api.get_all_userdata()
    users = {}
    for userdata in all_users.values():
        name = userdata["name"]
        users[name] = {"perms": get_permission(userdata["permission"])}
        users[name]["perms"]["admin"] = userdata["role"] == 0

    admin_menu = {
        "permlist": permlist(),
        "users": users
    }

    context = {
        "conf": {"plugin": plugin_menu, "general": conf_menu, "accs": accs, "admin": admin_menu},
        "types": api.get_account_types(),
    }
    return render_template("settings.html", **context)


@bp.route("/pathchooser/", endpoint="pathchooser")
@bp.route("/filechooser/", endpoint="filechooser")
@login_required("STATUS")
def pathchooser():
    browse_for = "folder" if flask.request.endpoint == "app.pathchooser" else "file"
    path = os.path.normpath(flask.request.args.get('path', ""))

    if os.path.isfile(path):
        oldfile = path
        path = os.path.dirname(path)
    else:
        oldfile = ""

    abs = False

    if os.path.isdir(path):
        if os.path.isabs(path):
            cwd = os.path.realpath(path)
            abs = True
        else:
            cwd = os.path.relpath(path)
    else:
        cwd = os.getcwd()

    cwd = os.path.normpath(os.path.realpath(cwd))
    parentdir = os.path.dirname(cwd)
    if not abs:
        if os.path.realpath(cwd) == os.path.realpath("/"):
            cwd = os.path.relpath(cwd)
        else:
            cwd = os.path.relpath(cwd) + os.path.sep
        parentdir = os.path.relpath(parentdir) + os.path.sep

    if os.path.realpath(cwd) == os.path.realpath("/"):
        parentdir = ""

    try:
        folders = os.listdir(cwd)
    except Exception:
        folders = []

    files = []

    for f in folders:
        try:
            data = {"name": f, "fullpath": os.path.join(cwd, f)}
            data["sort"] = data["fullpath"].lower()
            data["modified"] = datetime.datetime.fromtimestamp(
                int(os.path.getmtime(os.path.join(cwd, f)))
            )
            data["ext"] = os.path.splitext(f)[1]
        except Exception:
            continue

        if os.path.isfile(os.path.join(cwd, f)):
            data["type"] = "file"
            data["size"] = os.path.getsize(os.path.join(cwd, f))

            power = 0
            while (data["size"] >> 10) > 0.3:
                power += 1
                data["size"] >>= 10
            units = ("", "K", "M", "G", "T")
            data["unit"] = units[power] + "Byte"
        else:
            data["type"] = "dir"
            data["size"] = ""

        files.append(data)

    files = sorted(files, key=operator.itemgetter("type", "sort"))

    context = {
        "cwd": cwd,
        "files": files,
        "parentdir": parentdir,
        "type": browse_for,
        "oldfile": oldfile,
        "absolute": abs,
    }
    return render_template("pathchooser.html", **context)


@bp.route("/logs", methods=["GET", "POST"], endpoint="logs")
@bp.route("/logs/<int:start_line>", methods=["GET", "POST"], endpoint="logs")
@login_required("LOGS")
def logs(start_line=-1):
    s = flask.session
    api = flask.current_app.config["PYLOAD_API"]

    perpage = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = api.get_config_value("log", "filelog")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (34, 34), (40, 40), (100, 100), (0, "all"))
    fro = None

    if flask.request.method == "POST":
        try:
            from_form = flask.request.form["from"]
            fro = datetime.datetime.strptime(from_form, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        perpage = int(flask.request.form.get("perpage", 34))
        s["perpage"] = perpage

        reversed = bool(flask.request.form.get("reversed", False))
        s["reversed"] = reversed

        # s.modified = True

    log = api.get_log()
    if not perpage:
        start_line = 0

    if start_line < 1:
        start_line = (
            1 if len(log) - perpage + 1 < 1 or perpage == 0 else len(log) - perpage + 1
        )

    if isinstance(fro, datetime.datetime):  #: we will search for datetime.datetime
        start_line = -1

    data = []
    counter = 0
    perpagecheck = 0
    for logline in log:
        counter += 1

        if counter >= start_line:
            try:
                date, time, level, source, message = _RE_LOGLINE.match(logline).groups()
                dtime = datetime.datetime.strptime(
                    date + " " + time, "%Y-%m-%d %H:%M:%S"
                )
                message = message.strip()
            except (AttributeError, IndexError):
                dtime = None
                date = "?"
                time = " "
                level = "?"
                source = "?"
                message = logline
            if start_line == -1 and dtime is not None and fro <= dtime:
                start_line = counter  #: found our datetime.datetime

            if start_line >= 0:
                data.append(
                    {
                        "line": counter,
                        "date": date + " " + time,
                        "level": level,
                        "source": source,
                        "message": message.rstrip('\n'),
                    }
                )
                perpagecheck += 1
                if (
                    fro is None and dtime is not None
                ):  #: if fro not set set it to first showed line
                    fro = dtime
            if perpagecheck >= perpage > 0:
                break

    if fro is None:  #: still not set, empty log?
        fro = datetime.datetime.now()

    if reversed:
        data.reverse()

    context = {
        "warning": warning,
        "log": data,
        "from": fro.strftime("%Y-%m-%d %H:%M:%S"),
        "reversed": reversed,
        "perpage": perpage,
        "perpage_p": sorted(perpage_p),
        "iprev": max(start_line - perpage, 1),
        "inext": (start_line + perpage) if start_line + perpage <= len(log) else start_line,
    }
    return render_template("logs.html", **context)


@bp.route("/filemanager", endpoint="filemanager")
@login_required("MODIFY")
def filemanager(path):
    return render_template("filemanager.html")


@bp.route("/info", endpoint="info")
@login_required("STATUS")
def info():
    api = flask.current_app.config["PYLOAD_API"]
    conf = api.get_config_dict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    context = {
        "python": sys.version,
        "os": " ".join((os.name, sys.platform) + extra),
        "version": api.get_server_version(),
        "folder": PKGDIR,
        "config": api.get_userdir(),
        "download": conf["general"]["storage_folder"]["value"],
        "freespace": format.size(api.free_space()),
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
        "oidc_enabled": conf["webui"]["use_oidc"]["value"]
    }
    return render_template("info.html", **context)
