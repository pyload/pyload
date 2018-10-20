# -*- coding: utf-8 -*-
# @author: RaNaN



import datetime
import json
import operator
import os
import sys
import time
from builtins import HOMEDIR, PKGDIR, _
from urllib.parse import unquote

import flask

from pyload.utils.utils import formatSize, fs_decode, fs_encode
from pyload.webui.app import PREFIX, env
from pyload.webui.app.filters import relpath, unquotepath
from pyload.webui.app.utils import (get_permission, get_theme, login_required,
                                    parse_permissions, parse_userdata, permlist,
                                    flask_render, set_permission, set_session,
                                    toDict)
from pyload.webui.server_thread import PYLOAD_API


bp = flask.Blueprint('app', __name__)


# Helper
def pre_processor():
    s = flask.session
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    
    if user["is_authenticated"]:
        status = PYLOAD_API.statusServer()
        captcha = PYLOAD_API.isCaptchaWaiting()
        
        # check if update check is available
        info = PYLOAD_API.getInfoByPlugin("UpdateManager")
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
    return flask_render("base.html", {"messages": messages}, [pre_processor])

    
# Views
# @bp.errorhandler(403)
# def error403(error):
    # return "The parameter you passed has the wrong format"


# @bp.errorhandler(404)
# def error404(error):
    # return "Sorry, this page does not exist"


# @bp.errorhandler(500)
# def error500(error):
    # if error.traceback:
        # print(error.traceback)

    # return base(
        # [
            # "An Error occured, please enable debug mode to get more details.",
            # error,
            # error.traceback.replace("\n", "<br>")
            # if error.traceback
            # else "No Traceback",
        # ]
    # )


# render js
# @bp.route('/<path:re:.+\.js>')
# def server_js(path):
    # flask.response.headers['Content-Type'] = "text/javascript; charset=UTF-8"

    # if "/render/" in path or ".render." in path:
        # flask.response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                    # time.gmtime(time.time() + 24 * 7 * 60 * 60))
        # flask.response.headers['Cache-control'] = "public"

        # return flask_render(path)
    # else:
        # return serve_static(path)
        

# @bp.route(r"/<path:path>")
# def serve_static(path):
    # flask.response.headers["Expires"] = time.strftime(
        # "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time() + 60 * 60 * 24 * 7)
    # )
    # flask.response.headers["Cache-control"] = "public"
    # root = os.path.join('.', 'themes', get_theme())
    # return bottle.static_file(path, root=root)


# @bp.route(r"/favicon.ico")
# def favicon():
    # return bottle.static_file("favicon.ico", root=".")


# @bp.route(r"/robots.txt")
# def robots():
    # return bottle.static_file("robots.txt", root=".")


@bp.route(r"/login", methods=["GET"])
def login():
    return flask_render("login.html", proc=[pre_processor])


@bp.route(r"/nopermission")
def nopermission():
    return base([_("You dont have permission to access this page.")])


@bp.route(r"/login", methods=['POST'])
def login_post():
    user = flask.request.form.get("username")
    password = flask.request.form.get("password")

    info = PYLOAD_API.checkAuth(user, password)

    if not info:
        return flask_render("login.html", {"errors": True}, [pre_processor])

    set_session(flask.request, info)
    return flask.redirect("{}/".format(PREFIX))


@bp.route(r"/logout")
def logout():
    flask.session.clear()
    flask.session.modified = True
    return flask_render("logout.html", proc=[pre_processor])

import logging  # test
@bp.route(r"/")
@bp.route(r"/home")
@login_required("LIST")
def home():
    log = logging.getLogger('werkzeug')
    log.info(flask.url_for('index'))
    log.info(flask.url_for('home'))
    log.info(flask.url_for('/'))
    
    try:
        res = [toDict(x) for x in PYLOAD_API.statusDownloads()]
    except Exception:
        flask.session.clear()
        flask.session.modified = True
        return flask.redirect("{}/login".format(PREFIX))

    for link in res:
        if link["status"] == 12:
            link["information"] = "{} KiB @ {} KiB/s".format(
                link["size"] - link["bleft"], link["speed"]
            )

    return flask_render("home.html", {"res": res}, [pre_processor])


@bp.route(r"/queue")
@login_required("LIST")
def queue():
    queue = PYLOAD_API.getQueue()

    queue.sort(key=operator.attrgetter("order"))

    return flask_render(
        "queue.html", {"content": queue, "target": 1}, [pre_processor]
    )


@bp.route(r"/collector")
@login_required("LIST")
def collector():
    queue = PYLOAD_API.getCollector()

    queue.sort(key=operator.attrgetter("order"))

    return flask_render(
        "queue.html", {"content": queue, "target": 0}, [pre_processor]
    )


@bp.route(r"/downloads")
@login_required("DOWNLOAD")
def downloads():
    root = PYLOAD_API.getConfigValue("general", "download_folder")

    if not os.path.isdir(root):
        return base([_("Download directory not found.")])
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

    return flask_render("downloads.html", {"files": data}, [pre_processor])


@bp.route(r"/downloads/get/<filename>")
@login_required("DOWNLOAD")
def get_download(filename):
    filename = unquote(filename).decode("utf-8").replace("..", "")
    directory = PYLOAD_API.getConfigValue("general", "download_folder")
    return flask.send_from_directory(directory, filename, as_attachment=True)


@bp.route(r"/settings")
@login_required("SETTINGS")
def config():
    conf = PYLOAD_API.getConfig()
    plugin = PYLOAD_API.getPluginConfig()

    conf_menu = []
    plugin_menu = []

    for entry in sorted(conf.keys()):
        conf_menu.append((entry, conf[entry].description))

    for entry in sorted(plugin.keys()):
        plugin_menu.append((entry, plugin[entry].description))

    accs = []

    for data in PYLOAD_API.getAccounts(False):
        if data.trafficleft == -1:
            trafficleft = _("unlimited")
        elif not data.trafficleft:
            trafficleft = _("not available")
        else:
            trafficleft = formatSize(data.trafficleft << 10)

        if data.validuntil == -1:
            validuntil = _("unlimited")
        elif not data.validuntil:
            validuntil = _("not available")
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

    return flask_render(
        "settings.html",
        {
            "conf": {"plugin": plugin_menu, "general": conf_menu, "accs": accs},
            "types": PYLOAD_API.getAccountTypes(),
        },
        [pre_processor],
    )


@bp.route(r"/filechooser")
@bp.route(r"/filechooser/<path:filename>")
@login_required("STATUS")
def file(filename=""):
    return choose_path("file", filename)


@bp.route(r"/pathchooser")
@bp.route(r"/pathchooser/<path:dirname>")
@login_required("STATUS")
def folder(dirname=""):
    return choose_path("folder", dirname)


def choose_path(browse_for, path):
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

    return flask_render(
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


@bp.route(r"/logs", methods=['GET', 'POST'])
@bp.route(r"/logs/<item>", methods=['GET', 'POST'])
@login_required("LOGS")
def logs(item=-1):
    s = flask.session

    perpage = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = PYLOAD_API.getConfigValue("log", "file_log")
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

    log = PYLOAD_API.getLog()
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
    return flask_render(
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


@bp.route(r"/admin", methods=['GET', 'POST'])
@login_required("ADMIN")
def admin():
    # convert to dict
    user = {name: toDict(y) for name, y in PYLOAD_API.getAllUserData().items()}
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

            PYLOAD_API.setUserPermission(
                name, user[name]["permission"], user[name]["role"]
            )

    return flask_render(
        "admin.html", {"users": user, "permlist": perms}, [pre_processor]
    )


@bp.route(r"/setup")
def setup():
    return base([_("Run pyLoad -s to access the setup.")])
    
    
# @bp.route("/refresh")
# def refresh():
    # bp.app.theme_manager.refresh()
    # return flask.redirect(flask.url_for('themes'))
    
    
@bp.route(r"/info")
@login_required("STATUS")
def info():
    conf = PYLOAD_API.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    data = {
        "python": sys.version,
        "os": " ".join((os.name, sys.platform) + extra),
        "version": PYLOAD_API.getServerVersion(),
        "folder": os.path.abspath(PKGDIR),
        "config": os.path.abspath(os.path.join(HOMEDIR, "pyLoad")),
        "download": os.path.abspath(conf["general"]["download_folder"]["value"]),
        "freespace": formatSize(PYLOAD_API.freeSpace()),
        "remote": conf["remote"]["port"]["value"],
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
    }

    return flask_render("info.html", data, [pre_processor])
