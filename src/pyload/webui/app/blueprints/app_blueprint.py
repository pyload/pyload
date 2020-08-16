# -*- coding: utf-8 -*-

import datetime
import logging  # test
import operator
import os
import sys
import time
from urllib.parse import unquote

import flask

from pyload import PKGDIR
from pyload.core.utils import format

from ..filters import unquotepath
from ..helpers import (
    clear_session,
    get_permission,
    get_redirect_url,
    is_authenticated,
    login_required,
    permlist,
    render_base,
    render_template,
    set_permission,
    set_session,
    static_file_url,
)

bp = flask.Blueprint("app", __name__)


@bp.route("/favicon.ico", endpoint="favicon")
def favicon():
    location = static_file_url("img/favicon.ico")
    return flask.redirect(location)


@bp.route("/render/<path:filename>", endpoint="render")
def render(filename):
    return render_template(f"{filename}")


@bp.route("/robots.txt", endpoint="robots")
def robots():
    return "User-agent: *\n_disallow: /"


# TODO: Rewrite login route using flask-login
@bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    api = flask.current_app.config["PYLOAD_API"]

    next = get_redirect_url(fallback=flask.url_for("app.dashboard"))

    if flask.request.method == "POST":
        user = flask.request.form["username"]
        password = flask.request.form["password"]
        user_info = api.check_auth(user, password)

        if not user_info:
            return render_template("login.html", next=next, errors=True)

        set_session(user_info)
        flask.flash("Logged in successfully")

    if is_authenticated():
        return flask.redirect(next)

    if api.get_config_value("webui", "autologin"):
        allusers = api.get_all_userdata()
        if len(allusers) == 1:  # TODO: check if localhost
            user_info = list(allusers.values())[0]
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
@bp.route("/home", endpoint="home")
@bp.route("/dashboard", endpoint="dashboard")
@login_required("ALL")
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


@bp.route("/files/get/<filename>", endpoint="get_file")
@login_required("DOWNLOAD")
def get_file(filename):
    api = flask.current_app.config["PYLOAD_API"]
    filename = unquote(filename).replace("..", "")
    directory = api.get_config_value("general", "storage_folder")
    return flask.send_from_directory(directory, filename, as_attachment=True)


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

    for data in api.get_accounts(False):
        if data.trafficleft == -1:
            trafficleft = "unlimited"
        elif not data.trafficleft:
            trafficleft = "not available"
        else:
            trafficleft = format.size(data.trafficleft << 10)

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

        if "limit_dl" in data.options:
            try:
                limitdl = data.options["limit_dl"][0]
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
        "types": api.get_account_types(),
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
            cwd = os.path.relpath(cwd) + os.path.os.sep
        parentdir = os.path.relpath(parentdir) + os.path.os.sep

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

        perpage = int(flask.request.form["perpage"])
        s["perpage"] = perpage

        reversed = bool(flask.request.form["reversed"])
        s["reversed"] = reversed

        # s.modified = True

    log = api.get_log()
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

    allusers = api.get_all_userdata()

    perms = permlist()
    users = {}

    # NOTE: messy code... users just need "perms" data in admin template
    for data in allusers.values():
        name = data["name"]
        users[name] = {"perms": get_permission(data["permission"])}
        users[name]["perms"]["admin"] = data["role"] == 0

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

            api.set_user_permission(name, data["permission"], data["role"])

    return render_template("admin.html", users=users, permlist=perms)


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
    }
    return render_template("info.html", **context)
