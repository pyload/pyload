# -*- coding: utf-8 -*-
# @author: RaNaN, vuolter

import datetime
import logging  # test
import operator
import os
import sys
import time
from builtins import PKGDIR
from urllib.parse import unquote

import flask_login
import flask

from pyload.core.utils.utils import formatSize, fs_decode, fs_encode
from ..filters import unquotepath
from ..helpers import (clear_session, get_permission, login_required,
                                    parse_permissions, parse_userdata, permlist,
                                    render_template, set_permission, set_session,
                                    toDict)
from .helpers import pre_processor, base, get_redirect_target


# from flask_login import login_required, login_user, logout_user


bp = flask.Blueprint("app", __name__)


@bp.route(r"/favicon.ico")
def favicon():
    filename = os.path.join('img', 'favicon.ico')
    return flask.send_from_directory(bp.static_folder, filename)


@bp.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /"


@bp.route(r"/login", methods=["GET", "POST"])
def login():
    if flask.request.method == 'GET':
        return render_template("login.html", proc=[pre_processor])

    user = flask.request.form.get("username")
    password = flask.request.form.get("password")

    api = flask.current_app.config["PYLOAD_API"]
    info = api.checkAuth(user, password)

    if not info:
        return render_template("login.html", {"errors": True}, [pre_processor])

    # user = User(info['id'])
    # login_user(user)

    set_session(info)
    flask.flash('Logged in successfully.')

    next = get_redirect_target()
    return flask.redirect(next or flask.url_for('index'))


@bp.route(r"/logout")
def logout():
    # logout_user()
    clear_session()
    return render_template("logout.html", proc=[pre_processor])


@bp.route(r"/", endpoint="index")
@bp.route(r"/home", endpoint="home")
@login_required("LIST")
def home():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        res = [toDict(x) for x in api.statusDownloads()]
    except Exception:
        clear_session()
        return flask_login.login_url("app.login", flask.request.url)

    for link in res:
        if link["status"] == 12:
            link["information"] = "{} KiB @ {} KiB/s".format(
                link["size"] - link["bleft"], link["speed"]
            )

    return render_template("home.html", {"res": res}, [pre_processor])


@bp.route(r"/queue", endpoint="queue")
@login_required("LIST")
def queue():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.getQueue()

    queue.sort(key=operator.attrgetter("order"))

    return render_template(
        "queue.html", {"content": queue, "target": 1}, [pre_processor]
    )


@bp.route(r"/collector", endpoint="collector")
@login_required("LIST")
def collector():
    api = flask.current_app.config["PYLOAD_API"]
    queue = api.getCollector()

    queue.sort(key=operator.attrgetter("order"))

    return render_template(
        "queue.html", {"content": queue, "target": 0}, [pre_processor]
    )


@bp.route(r"/downloads", endpoint="downloads")
@login_required("DOWNLOAD")
def downloads():
    api = flask.current_app.config["PYLOAD_API"]
    root = api.getConfigValue("general", "download_folder")

    if not os.path.isdir(root):
        messages = ["Download directory not found."]
        return base(messages)
    data = {"folder": [], "files": []}

    items = os.listdir(fs_encode(root))

    for item in sorted(fs_decode(x) for x in items):
        if os.path.isdir(os.path.join(root, item)):
            folder = {"name": item, "path": item, "files": []}
            files = os.listdir(os.path.join(root, item))
            for file in sorted(fs_decode(x) for x in files):
                try:
                    if os.path.isfile(os.path.join(root, item, file)):
                        folder["files"].append(file)
                except Exception:
                    pass

            data["folder"].append(folder)
        elif os.path.isfile(os.path.join(root, item)):
            data["files"].append(item)

    return render_template("downloads.html", {"files": data}, [pre_processor])


@bp.route(r"/downloads/get/<filename>", endpoint="get_download")
@login_required("DOWNLOAD")
def get_download(filename):
    api = flask.current_app.config["PYLOAD_API"]
    filename = unquote(filename).decode("utf-8").replace("..", "")
    directory = api.getConfigValue("general", "download_folder")
    return flask.send_from_directory(directory, filename, as_attachment=True)


@bp.route(r"/settings", endpoint="settings")
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

    return render_template(
        "settings.html",
        {
            "conf": {"plugin": plugin_menu, "general": conf_menu, "accs": accs},
            "types": api.getAccountTypes(),
        },
        [pre_processor],
    )


@bp.route(r"/pathchooser", endpoint="filemanager")
@bp.route(r"/pathchooser/<path:path>", endpoint="filemanager")
@login_required("STATUS")
def filemanager(path):
    browse_for = "folder" if os.path.isdir(path) else "file"
    path = os.path.normpath(unquotepath(path))

    try:
        path = os.path.decode("utf-8")
    except Exception:
        pass

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

    # try:
    #     cwd = cwd.encode("utf-8")
    # except Exception:
    #     pass
    #
    try:
        folders = os.listdir(cwd)
    except Exception:
        folders = []

    files = []

    for f in folders:
        try:
            # f = f.decode(getfilesystemencoding())
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

    return render_template(
        "pathchooser.html",
        {
            "cwd": cwd,
            "files": files,
            "parentdir": parentdir,
            "type": browse_for,
            "oldfile": oldfile,
            "absolute": abs,
        },
        [],
    )


@bp.route(r"/logs", methods=["GET", "POST"], endpoint="logs")
@bp.route(r"/logs/<item>", methods=["GET", "POST"], endpoint="logs")
@login_required("LOGS")
def logs(item=-1):
    s = flask.session
    api = flask.current_app.config["PYLOAD_API"]

    perpage = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = api.getConfigValue("log", "file_log")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (34, 34), (40, 40), (100, 100), (0, "all"))
    fro = None

    if flask.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        try:
            fro = datetime.datetime.strptime(
                flask.request.form["from"], "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            pass
        try:
            perpage = int(flask.request.form["perpage"])
            s["perpage"] = perpage

            reversed = bool(flask.request.form.get("reversed", False))
            s["reversed"] = reversed
        except Exception:
            pass

        s.modified = True

    try:
        item = int(item)
    except Exception:
        pass

    log = api.getLog()
    if not perpage:
        item = 0

    if item < 1 or not isinstance(item, int):
        item = (
            1 if len(log) - perpage + 1 < 1 or perpage == 0 else len(log) - perpage + 1
        )

    if isinstance(fro, datetime.datetime):  #: we will search for datetime.datetime
        item = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= item:
            try:
                date, time, level, message = l.decode("utf-8", "ignore").split(" ", 3)
                dtime = datetime.datetime.strptime(
                    date + " " + time, "%Y-%m-%d %H:%M:%S"
                )
            except Exception:
                dtime = None
                date = "?"
                time = " "
                level = "?"
                message = l
            if item == -1 and dtime is not None and fro <= dtime:
                item = counter  #: found our datetime.datetime
            if item >= 0:
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
    return render_template(
        "logs.html",
        {
            "warning": warning,
            "log": data,
            "from": fro.strftime("%Y-%m-%d %H:%M:%S"),
            "reversed": reversed,
            "perpage": perpage,
            "perpage_p": sorted(perpage_p),
            "iprev": 1 if item - perpage < 1 else item - perpage,
            "inext": (item + perpage) if item + perpage < len(log) else item,
        },
        [pre_processor],
    )


@bp.route(r"/admin", methods=["GET", "POST"], endpoint="admin")
@login_required("ADMIN")
def admin():
    api = flask.current_app.config["PYLOAD_API"]
    # convert to dict
    user = {name: toDict(y) for name, y in api.getAllUserData().items()}
    perms = permlist()

    for data in user.values():
        data["perms"] = {}
        get_permission(data["perms"], data["permission"])
        data["perms"]["admin"] = data["role"] is 0

    s = flask.session
    if flask.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        for name in user:
            if flask.request.form.get("{}|admin".format(name), False):
                user[name]["role"] = 0
                user[name]["perms"]["admin"] = True
            elif name != s["name"]:
                user[name]["role"] = 1
                user[name]["perms"]["admin"] = False

            # set all perms to false
            for perm in perms:
                user[name]["perms"][perm] = False

            for perm in flask.request.form.getlist("{}|perms".format(name)):
                user[name]["perms"][perm] = True

            user[name]["permission"] = set_permission(user[name]["perms"])

            api.setUserPermission(name, user[name]["permission"], user[name]["role"])

    return render_template(
        "admin.html", {"users": user, "permlist": perms}, [pre_processor]
    )


@bp.route(r"/setup")
def setup():
    messages = ["Run pyLoad -s to access the setup."]
    return base(messages)


@bp.route(r"/info", endpoint="info")
@login_required("STATUS")
def info():
    api = flask.current_app.config["PYLOAD_API"]
    conf = api.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    data = {
        "python": sys.version,
        "os": " ".join((os.name, sys.platform) + extra),
        "version": api.getServerVersion(),
        "folder": os.path.abspath(PKGDIR),
        "config": os.path.abspath(api.get_userdir()),
        "download": os.path.abspath(conf["general"]["download_folder"]["value"]),
        "freespace": formatSize(api.freeSpace()),
        "remote": conf["remote"]["port"]["value"],
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
    }

    return render_template("info.html", data, [pre_processor])
