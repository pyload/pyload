# -*- coding: utf-8 -*-
# AUTHOR: RaNaN, vuolter

import datetime
import logging  # test
import operator
import os
import sys
import time
from urllib.parse import unquote

import flask

from pyload import PKGDIR
from pyload.core.utils import formatSize

from ..filters import unquotepath
from ..helpers import (
    static_file_url,
    clear_session,
    get_permission,
    login_required,
    permlist,
    render_base,
    render_template,
    set_permission,
    set_session,
    is_authenticated,
    get_redirect_url,
)


bp = flask.Blueprint("app", __name__)


@bp.route("/favicon.ico", endpoint="favicon")
def favicon():
    location = static_file_url("img/favicon.ico")
    return flask.redirect(location)


@bp.route("/robots.txt", endpoint="robots")
def robots():
    return "User-agent: *\nDisallow: /"


# TODO: Rewrite login route using flask-login
@bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    api = flask.current_app.config["PYLOAD_API"]

    next = get_redirect_url(fallback=flask.url_for("app.dashboard"))

    if flask.request.method == "POST":
        user = flask.request.form["username"]
        password = flask.request.form["password"]
        user_info = api.checkAuth(user, password)

        if not user_info:
            return render_template("login.html", next=next, errors=True)

        set_session(user_info)
        flask.flash("Logged in successfully")

    if is_authenticated():
        return flask.redirect(next)

    if api.getConfigValue("webui", "autologin"):
        allusers = api.getAllUserData()
        if len(allusers) == 1:  # TODO: check if localhost
            user_info = next(iter(allusers.values()))
            # user_info = allusers[next(allusers)]
            set_session(user_info)
            # NOTE: Double-check autentication here because if session[name] is empty,
            #       next login_required redirects here again and all loop out.
            if is_authenticated():
                return flask.redirect(next)

    return render_template("login.html", next=next)


@bp.route("/logout", endpoint="logout")
def logout():
    # logout_user()
    clear_session()
    return render_template("logout.html")


@bp.route("/", endpoint="index")
@bp.route("/dashboard", endpoint="dashboard")
@login_required("ALL")
def dashboard():
    api = flask.current_app.config["PYLOAD_API"]
    links = api.statusDownloads()

    for link in links:
        if link["status"] == 12:
            current_size = link["size"] - link["bleft"]
            speed = link["speed"]
            link["information"] = f"{current_size} KiB @ {speed} KiB/s"

    return render_template("dashboard.html", res=links)


@bp.route("/queue", endpoint="queue")
@login_required("LIST")
def queue():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.getQueue()
    queue.sort(key=operator.attrgetter("order"))

    return render_template("queue.html", content=queue, target=1)


@bp.route("/collector", endpoint="collector")
@login_required("LIST")
def collector():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.getCollector()

    queue.sort(key=operator.attrgetter("order"))

    return render_template("queue.html", content=queue, target=0)


@bp.route("/files", endpoint="files")
@login_required("DOWNLOAD")
def files():
    api = flask.current_app.config["PYLOAD_API"]
    root = api.getConfigValue("general", "storage_folder")

    if not os.path.isdir(root):
        messages = ["Download directory not found."]
        return render_base(messages)
    data = {"folder": [], "files": []}

    items = os.listdir(root)

    for item in sorted(items):
        if os.path.isdir(os.path.join(root, item)):
            folder = {"name": item, "path": item, "files": []}
            files = os.listdir(os.path.join(root, item))
            for file in sorted(files):
                try:
                    if os.path.isfile(os.path.join(root, item, file)):
                        folder["files"].append(file)
                except Exception:
                    pass

            data["folder"].append(folder)
        elif os.path.isfile(os.path.join(root, item)):
            data["files"].append(item)

    return render_template("files.html", files=data)


@bp.route("/files/get/<filename>", endpoint="get_file")
@login_required("DOWNLOAD")
def get_file(filename):
    api = flask.current_app.config["PYLOAD_API"]
    filename = unquote(filename).replace("..", "")
    directory = api.getConfigValue("general", "storage_folder")
    return flask.send_from_directory(directory, filename, as_attachment=True)


@bp.route("/settings", endpoint="settings")
@login_required("SETTINGS")
def settings():
    api = flask.current_app.config["PYLOAD_API"]
    conf = api.getConfig()
    plugin = api.getPluginConfig()

    conf_menu = []
    plugin_menu = []

    for entry in sorted(conf.keys()):
        conf_menu.append((entry, conf[entry].description))

    for entry in sorted(plugin.keys()):
        plugin_menu.append((entry, plugin[entry].description))

    accs = []

    for data in api.getAccounts(False):
        if data.trafficleft == -1:
            trafficleft = "unlimited"
        elif not data.trafficleft:
            trafficleft = "not available"
        else:
            trafficleft = formatSize(data.trafficleft << 10)

        if data.validuntil == -1:
            validuntil = "unlimited"
        elif not data.validuntil:
            validuntil = "not available"
        else:
            t = time.localtime(data.validuntil)
            validuntil = time.strftime("%Y-%m-%d %H:%M:%S", t)

        if "time" in data.options:
            try:
                _time = data.options["time"][0]
            except Exception:
                _time = ""
        else:
            _time = ""

        if "limitDL" in data.options:
            try:
                limitdl = data.options["limitDL"][0]
            except Exception:
                limitdl = "0"
        else:
            limitdl = "0"

        accs.append(
            {
                "type": data.type,
                "login": data.login,
                "valid": data.valid,
                "premium": data.premium,
                "trafficleft": trafficleft,
                "validuntil": validuntil,
                "limitdl": limitdl,
                "time": _time,
            }
        )

    context = {
        "conf": {"plugin": plugin_menu, "general": conf_menu, "accs": accs},
        "types": api.getAccountTypes(),
    }
    return render_template("settings.html", **context)


@bp.route("/pathchooser", endpoint="pathchooser")
@bp.route("/pathchooser/<path:path>", endpoint="pathchooser")
@login_required("STATUS")
def pathchooser(path):
    browse_for = "folder" if os.path.isdir(path) else "file"
    path = os.path.normpath(unquotepath(path))

    if os.path.isfile(path):
        oldfile = path
        path = os.path.dirname(path)
    else:
        oldfile = ""

    abs = False

    if os.path.isdir(path):
        if os.path.isabs(path):
            cwd = os.path.abspath(path)
            abs = True
        else:
            cwd = os.path.relpath(path)
    else:
        cwd = os.getcwd()

    cwd = os.path.normpath(os.path.abspath(cwd))
    parentdir = os.path.dirname(cwd)
    if not abs:
        if os.path.abspath(cwd) == os.path.abspath("/"):
            cwd = os.path.relpath(cwd)
        else:
            cwd = os.path.relpath(cwd) + os.path.os.sep
        parentdir = os.path.relpath(parentdir) + os.path.os.sep

    if os.path.abspath(cwd) == os.path.abspath("/"):
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

        if os.path.isdir(os.path.join(cwd, f)):
            data["type"] = "dir"
        else:
            data["type"] = "file"

        if os.path.isfile(os.path.join(cwd, f)):
            data["size"] = os.path.getsize(os.path.join(cwd, f))

            power = 0
            while (data["size"] >> 10) > 0.3:
                power += 1
                data["size"] >>= 10
            units = ("", "K", "M", "G", "T")
            data["unit"] = units[power] + "Byte"
        else:
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
@bp.route("/logs/<int:page>", methods=["GET", "POST"], endpoint="logs")
@login_required("LOGS")
def logs(page=-1):
    s = flask.session
    api = flask.current_app.config["PYLOAD_API"]

    perpage = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = api.getConfigValue("log", "filelog")
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

        perpage = int(flask.request.form["perpage"])
        s["perpage"] = perpage

        reversed = bool(flask.request.form["reversed"])
        s["reversed"] = reversed

        # s.modified = True

    log = api.getLog()
    if not perpage:
        page = 0

    if page < 1 or not isinstance(page, int):
        page = (
            1 if len(log) - perpage + 1 < 1 or perpage == 0 else len(log) - perpage + 1
        )

    if isinstance(fro, datetime.datetime):  #: we will search for datetime.datetime
        page = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= page:
            try:
                date, time, level, message = l.split(" ", 3)
                dtime = datetime.datetime.strptime(
                    date + " " + time, "%Y-%m-%d %H:%M:%S"
                )
            except Exception:
                dtime = None
                date = "?"
                time = " "
                level = "?"
                message = l
            if page == -1 and dtime is not None and fro <= dtime:
                page = counter  #: found our datetime.datetime
            if page >= 0:
                data.append(
                    {
                        "line": counter,
                        "date": date + " " + time,
                        "level": level,
                        "message": message,
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
        "iprev": 1 if page - perpage < 1 else page - perpage,
        "inext": (page + perpage) if page + perpage < len(log) else page,
    }
    return render_template("logs.html", **context)


@bp.route("/admin", methods=["GET", "POST"], endpoint="admin")
@login_required("ADMIN")
def admin():
    api = flask.current_app.config["PYLOAD_API"]

    allusers = api.getAllUserData()

    perms = permlist()
    users = {}

    # NOTE: messy code... users just need "perms" data in admin template
    for name, data in allusers.items():
        users[name] = {"perms": get_permission(data["permission"])}
        users[name]["perms"]["admin"] = data["role"] is 0

    s = flask.session
    if flask.request.method == "POST":
        for name, data in users.items():
            if flask.request.form.get(f"{name}|admin"):
                data["role"] = 0
                data["perms"]["admin"] = True
            elif name != s["name"]:
                data["role"] = 1
                data["perms"]["admin"] = False

            # set all perms to false
            for perm in perms:
                data["perms"][perm] = False

            for perm in flask.request.form.getlist(f"{name}|perms"):
                data["perms"][perm] = True

            data["permission"] = set_permission(data["perms"])

            api.setUserPermission(name, data["permission"], data["role"])

    return render_template("admin.html", users=users, permlist=perms)


@bp.route("/filemanager", endpoint="filemanager")
@login_required("MODIFY")
def filemanager(path):
    return render_template("filemanager.html")


@bp.route("/info", endpoint="info")
@login_required("STATUS")
def info():
    api = flask.current_app.config["PYLOAD_API"]
    conf = api.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    context = {
        "python": sys.version,
        "os": " ".join((os.name, sys.platform) + extra),
        "version": api.getServerVersion(),
        "folder": os.path.abspath(PKGDIR),
        "config": os.path.abspath(api.get_userdir()),
        "download": os.path.abspath(conf["general"]["storage_folder"]["value"]),
        "freespace": formatSize(api.freeSpace()),
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
    }
    return render_template("info.html", **context)
