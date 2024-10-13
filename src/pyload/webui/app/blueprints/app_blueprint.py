# -*- coding: utf-8 -*-

import datetime
import mimetypes
import operator
import os
import re
import sys
import time
from logging import getLogger
from urllib.parse import unquote

import flask
from pyload import APPID, PKGDIR
from pyload.core.utils import format

from ..helpers import (
    clear_session, get_permission, get_redirect_url, is_authenticated, login_required, permlist, render_base,
    render_template, set_session, static_file_url)

_RE_LOGLINE = re.compile(r"\[([\d\-]+) ([\d:]+)\] +([A-Z]+) +(.+?) (.*)")

bp = flask.Blueprint("app", __name__)
log = getLogger(APPID)


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

    next_url = get_redirect_url(fallback="app.dashboard")

    if flask.request.method == "POST":
        user = flask.request.form["username"]
        password = flask.request.form["password"]
        user_info = api.check_auth(user, password)

        if flask.request.headers.get("X-Forwarded-For"):
            client_ip = flask.request.headers.get("X-Forwarded-For").split(',')[0].strip()
        else:
            client_ip = flask.request.remote_addr

        sanitized_user = user.replace("\n", "\\n").replace("\r", "\\r")
        if not user_info:
            log.error(f"Login failed for user '{sanitized_user}' [CLIENT: {client_ip}]")
            return render_template("login.html", errors=True)

        set_session(user_info)
        log.info(f"User '{sanitized_user}' successfully logged in [CLIENT: {client_ip}]")
        flask.flash("Logged in successfully")

    if is_authenticated():
        return flask.redirect(next_url)

    if api.get_config_value("webui", "autologin"):
        allusers = api.get_all_userdata()
        if len(allusers) == 1:  # TODO: check if localhost
            user_info = list(allusers.values())[0]
            set_session(user_info)
            # NOTE: Double-check authentication here because if session[name] is empty,
            #       next login_required redirects here again and all loop out.
            if is_authenticated():
                return flask.redirect(next_url)

    return render_template("login.html")


@bp.route("/logout", endpoint="logout")
def logout():
    s = flask.session
    user = s.get("name")
    clear_session(s)
    if user:
        log.info(f"User '{user}' logged out")
    return render_template("logout.html")


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
        if userdata.trafficleft is None:
            trafficleft = "not available"
        elif userdata.trafficleft == -1:
            trafficleft = "unlimited"
        elif userdata.trafficleft == 0:
            trafficleft = "drained"
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
@login_required("SETTINGS")
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

    per_page = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = api.get_config_value("log", "filelog")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    per_page_selection = ((20, 20), (34, 34), (40, 40), (100, 100), (0, "all"))
    fro = None

    if flask.request.method == "POST":
        try:
            from_form = flask.request.form["from"]
            fro = datetime.datetime.strptime(from_form, "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        per_page = int(flask.request.form.get("perpage", 34))
        s["perpage"] = per_page

        reversed = bool(flask.request.form.get("reversed", False))
        s["reversed"] = reversed

        # s.modified = True

    log_entries = api.get_log()
    if not per_page:
        start_line = 0

    if start_line < 1:
        start_line = (
            1 if len(log_entries) - per_page + 1 < 1 or per_page == 0 else len(log_entries) - per_page + 1
        )

    if isinstance(fro, datetime.datetime):  #: we will search for datetime.datetime
        start_line = -1

    data = []
    inpage_counter = 0
    for counter, logline in enumerate(log_entries, start=1):
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
                inpage_counter += 1
                if (
                    fro is None and dtime is not None
                ):  #: if fro not set, set it to first showed line
                    fro = dtime
            if inpage_counter >= per_page > 0:
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
        "perpage": per_page,
        "perpage_p": sorted(per_page_selection),
        "iprev": max(start_line - per_page, 1),
        "inext": (start_line + per_page) if start_line + per_page <= len(log_entries) else start_line,
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
        "config_folder": api.get_userdir(),
        "download": conf["general"]["storage_folder"]["value"],
        "freespace": format.size(api.free_space()),
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
    }
    return render_template("info.html", **context)
