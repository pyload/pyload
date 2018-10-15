# -*- coding: utf-8 -*-
import datetime
import operator
import os
import sys
import time
from builtins import _
from urllib.parse import unquote

from builtins import PKGDIR, HOMEDIR

import bottle

import json
from pyload.utils.utils import formatSize, fs_decode, fs_encode, save_join
from pyload.webui.app import PREFIX, env
from pyload.webui.server_thread import PYLOAD_API
from pyload.webui.app.filters import relpath, unquotepath
from pyload.webui.app.utils import (
    get_permission,
    login_required,
    parse_permissions,
    parse_userdata,
    permlist,
    render_to_response,
    set_permission,
    set_session,
    toDict,
    get_themedir,
)

# @author: RaNaN


# Helper


def pre_processor():
    s = bottle.request.environ.get("beaker.session")
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    if user["is_authenticated"]:
        status = PYLOAD_API.statusServer()
        info = PYLOAD_API.getInfoByPlugin("UpdateManager")
        captcha = PYLOAD_API.isCaptchaWaiting()

        # check if update check is available
        if info:
            if info["pyload"] == "True":
                update = info["version"]
            if info["plugins"] == "True":
                plugins = True

    return {
        "user": user,
        "status": status,
        "captcha": captcha,
        "perms": perms,
        "url": bottle.request.url,
        "update": update,
        "plugins": plugins,
    }


def base(messages):
    return render_to_response("base.html", {"messages": messages}, [pre_processor])


def choose_path(browse_for, path=""):
    path = os.path.normpath(unquotepath(path))

    try:
        path = os.path.decode("utf8")
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
    #     cwd = cwd.encode("utf8")
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
            while (data["size"] / 1024.0) > 0.3:
                power += 1
                data["size"] /= 1024.0
            units = ("", "K", "M", "G", "T")
            data["unit"] = units[power] + "Byte"
        else:
            data["size"] = ""

        files.append(data)

    files = sorted(files, key=operator.itemgetter("type", "sort"))

    return render_to_response(
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


# Views
@bottle.error(403)
def error403(code):
    return "The parameter you passed has the wrong format"


@bottle.error(404)
def error404(code):
    return "Sorry, this page does not exist"


@bottle.error(500)
def error500(error):
    if error.traceback:
        print(error.traceback)

    return base(
        [
            "An Error occured, please enable debug mode to get more details.",
            error,
            error.traceback.replace("\n", "<br>")
            if error.traceback
            else "No Traceback",
        ]
    )


# TODO: fix
# @bottle.route("/<file:re:(.+/)?[^/]+\.min\.[^/]+>")
# def server_min(theme, filename):
    # path = os.path.join(get_themedir(), filename)
    # if not os.path.isfile(path):
        # path = path.replace(".min.", ".")
    # if path.endswith(".js"):
        # return server_js(path)
    # else:
        # return server_static(path)


# render js


@bottle.route(r"/media/js/<path:re:.+\.js>")
def js_dynamic(path):
    bottle.response.headers["Expires"] = time.strftime(
        "%a, {} %b %Y %H:%M:%S GMT", time.gmtime(time.time() + 60 * 60 * 24 * 2)
    )
    bottle.response.headers["Cache-control"] = "public"
    bottle.response.headers["Content-Type"] = "text/javascript; charset=UTF-8"

    try:
        # static files are not rendered
        if "static" not in path and "mootools" not in path:
            t = env.get_template("js/{}".format(path))
            return t.render()
        else:
            return bottle.static_file(path, root=os.path.join(get_themedir(), "js"))
    except Exception:
        return bottle.HTTPError(404, json.dumps("Not Found"))


@bottle.route(r"/media/<path:path>")
def server_static(path):
    bottle.response.headers["Expires"] = time.strftime(
        "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time.time() + 60 * 60 * 24 * 7)
    )
    bottle.response.headers["Cache-control"] = "public"
    PROJECT_DIR = ""  # TODO: fix
    return bottle.static_file(path, root=os.path.join(PROJECT_DIR, "media"))


# rewrite to return theme favicon
@bottle.route(r"/favicon.ico")
def favicon():
    return bottle.static_file("favicon.ico", root=os.path.join(get_themedir(), "img"))


@bottle.route(r"/robots.txt")
def robots():
    return bottle.static_file("robots.txt", root=".")


@bottle.route(r"/login", method="GET")
def login():
    if not PYLOAD_API:
        bottle.redirect("{}/setup".format(PREFIX))
    else:
        return render_to_response("login.html", proc=[pre_processor])


@bottle.route(r"/nopermission")
def nopermission():
    return base([_("You dont have permission to access this page.")])


@bottle.route(r"/login", method="POST")
def login_post():
    user = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    info = PYLOAD_API.checkAuth(user, password)

    if not info:
        return render_to_response("login.html", {"errors": True}, [pre_processor])

    set_session(bottle.request, info)
    return bottle.redirect("{}/".format(PREFIX))


@bottle.route(r"/logout")
def logout():
    s = bottle.request.environ.get("beaker.session")
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])


@bottle.route(r"/")
@bottle.route(r"/home")
@login_required("LIST")
def home():
    try:
        res = [toDict(x) for x in PYLOAD_API.statusDownloads()]
    except Exception:
        s = bottle.request.environ.get("beaker.session")
        s.delete()
        return bottle.redirect("{}/login".format(PREFIX))

    for link in res:
        if link["status"] == 12:
            link["information"] = "{} kB @ {} kB/s".format(
                link["size"] - link["bleft"], link["speed"]
            )

    return render_to_response("home.html", {"res": res}, [pre_processor])


@bottle.route(r"/queue")
@login_required("LIST")
def queue():
    queue = PYLOAD_API.getQueue()

    queue.sort(key=operator.attrgetter("order"))

    return render_to_response(
        "queue.html", {"content": queue, "target": 1}, [pre_processor]
    )


@bottle.route(r"/collector")
@login_required("LIST")
def collector():
    queue = PYLOAD_API.getCollector()

    queue.sort(key=operator.attrgetter("order"))

    return render_to_response(
        "queue.html", {"content": queue, "target": 0}, [pre_processor]
    )


@bottle.route(r"/downloads")
@login_required("DOWNLOAD")
def downloads():
    root = PYLOAD_API.getConfigValue("general", "download_folder")

    if not os.path.isdir(root):
        return base([_("Download directory not found.")])
    data = {"folder": [], "files": []}

    items = os.listdir(fs_encode(root))

    for item in sorted(fs_decode(x) for x in items):
        if os.path.isdir(save_join(root, item)):
            folder = {"name": item, "path": item, "files": []}
            files = os.listdir(save_join(root, item))
            for file in sorted(fs_decode(x) for x in files):
                try:
                    if os.path.isfile(save_join(root, item, file)):
                        folder["files"].append(file)
                except Exception:
                    pass

            data["folder"].append(folder)
        elif os.path.isfile(os.path.join(root, item)):
            data["files"].append(item)

    return render_to_response("downloads.html", {"files": data}, [pre_processor])


@bottle.route(r"/downloads/get/<path:re:.+>")
@login_required("DOWNLOAD")
def get_download(path):
    path = unquote(path).decode("utf8")
    # TODO: some files can not be downloaded

    root = PYLOAD_API.getConfigValue("general", "download_folder")

    path = os.path.replace("..", "")
    try:
        return bottle.static_file(fs_encode(path), fs_encode(root), download=True)

    except Exception as e:
        print(e)
        return bottle.HTTPError(404, json.dumps("File not Found"))


@bottle.route(r"/settings")
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
            trafficleft = formatSize(data.trafficleft * 1024)

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

    return render_to_response(
        "settings.html",
        {
            "conf": {"plugin": plugin_menu, "general": conf_menu, "accs": accs},
            "types": PYLOAD_API.getAccountTypes(),
        },
        [pre_processor],
    )


@bottle.route(r"/filechooser")
@bottle.route(r"/filechooser/:file#.+#")
@login_required("STATUS")
def file(file=""):
    return choose_path("file", file)


@bottle.route(r"/pathchooser")
@bottle.route(r"/pathchooser/:path#.+#")
@login_required("STATUS")
def path(path=""):
    return choose_path("folder", path)


@bottle.route(r"/logs")
@bottle.route(r"/logs", method="POST")
@bottle.route(r"/logs/<item>")
@bottle.route(r"/logs/<item>", method="POST")
@login_required("LOGS")
def logs(item=-1):
    s = bottle.request.environ.get("beaker.session")

    perpage = s.get("perpage", 34)
    reversed = s.get("reversed", False)

    warning = ""
    conf = PYLOAD_API.getConfigValue("log", "file_log")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (34, 34), (40, 40), (100, 100), (0, "all"))
    fro = None

    if bottle.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        try:
            fro = datetime.datetime.strptime(bottle.request.forms["from"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        try:
            perpage = int(bottle.request.forms["perpage"])
            s["perpage"] = perpage

            reversed = bool(bottle.request.forms.get("reversed", False))
            s["reversed"] = reversed
        except Exception:
            pass

        s.save()

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

    if isinstance(fro, datetime.datetime):  # we will search for datetime.datetime
        item = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= item:
            try:
                date, time, level, message = l.decode("utf8", "ignore").split(" ", 3)
                dtime = datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
            except Exception:
                dtime = None
                date = "?"
                time = " "
                level = "?"
                message = l
            if item == -1 and dtime is not None and fro <= dtime:
                item = counter  # found our datetime.datetime
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
                ):  # if fro not set set it to first showed line
                    fro = dtime
            if perpagecheck >= perpage > 0:
                break

    if fro is None:  # still not set, empty log?
        fro = datetime.datetime.now()
    if reversed:
        data.reverse()
    return render_to_response(
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


@bottle.route(r"/admin")
@bottle.route(r"/admin", method="POST")
@login_required("ADMIN")
def admin():
    # convert to dict
    user = {name: toDict(y) for name, y in PYLOAD_API.getAllUserData().items()}
    perms = permlist()

    for data in user.values():
        data["perms"] = {}
        get_permission(data["perms"], data["permission"])
        data["perms"]["admin"] = data["role"] is 0

    s = bottle.request.environ.get("beaker.session")
    if bottle.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        for name in user:
            if bottle.request.POST.get("{}|admin".format(name), False):
                user[name]["role"] = 0
                user[name]["perms"]["admin"] = True
            elif name != s["name"]:
                user[name]["role"] = 1
                user[name]["perms"]["admin"] = False

            # set all perms to false
            for perm in perms:
                user[name]["perms"][perm] = False

            for perm in bottle.request.POST.getall("{}|perms".format(name)):
                user[name]["perms"][perm] = True

            user[name]["permission"] = set_permission(user[name]["perms"])

            PYLOAD_API.setUserPermission(
                name, user[name]["permission"], user[name]["role"]
            )

    return render_to_response(
        "admin.html", {"users": user, "permlist": perms}, [pre_processor]
    )


@bottle.route(r"/setup")
def setup():
    return base([_("Run pyLoad -s to access the setup.")])


@bottle.route(r"/info")
@login_required("STATUS")
def info():
    conf = PYLOAD_API.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    data = {
        "python": sys.version,
        "os": " ".join((os.name, sys.platform) + extra),
        "version": PYLOAD_API.getServerVersion(),
        "folder": os.path.abspath(PKGDIR),
        "config": os.path.abspath(os.path.join(HOMEDIR, '.pyload')),
        "download": os.path.abspath(conf["general"]["download_folder"]["value"]),
        "freespace": formatSize(PYLOAD_API.freeSpace()),
        "remote": conf["remote"]["port"]["value"],
        "webif": conf["webui"]["port"]["value"],
        "language": conf["general"]["language"]["value"],
    }

    return render_to_response("info.html", data, [pre_processor])
