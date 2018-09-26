#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
from datetime import datetime
from operator import itemgetter, attrgetter

import time
import os
import sys
from os import listdir
from os.path import isdir, isfile, join, abspath
from sys import getfilesystemencoding
from urllib import unquote

from bottle import route, static_file, request, response, redirect, HTTPError, error

from webinterface import PYLOAD, PYLOAD_DIR, PROJECT_DIR, SETUP, PREFIX, env

from utils import render_to_response, parse_permissions, parse_userdata, \
    login_required, get_permission, set_permission, permlist, toDict, set_session

from filters import relpath, unquotepath

from module.utils import formatSize, save_join, fs_encode, fs_decode

# Helper

def pre_processor():
    s = request.environ.get('beaker.session')
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    if user["is_authenticated"]:
        status = PYLOAD.statusServer()
        info = PYLOAD.getInfoByPlugin("UpdateManager")
        captcha = PYLOAD.isCaptchaWaiting()

        # check if update check is available
        if info:
            if info["pyload"] == "True": update = True
            if info["plugins"] == "True": plugins = True


    return {"user": user,
            'status': status,
            'captcha': captcha,
            'perms': perms,
            'url': request.url,
            'update': update,
            'plugins': plugins}


def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])

def choose_path(browse_for, path=""):
    path = os.path.normpath(unquotepath(path))

    try:
        path = path.decode("utf8")
    except:
        pass

    if os.path.isfile(path):
        oldfile = path
        path = os.path.dirname(path)
    else:
        oldfile = ''

    abs = False

    if os.path.isdir(path):
        if os.path.isabs(path):
            cwd = os.path.abspath(path)
            abs = True
        else:
            cwd = relpath(path)
    else:
        cwd = os.getcwd()

    cwd = os.path.normpath(os.path.abspath(cwd))
    parentdir = os.path.dirname(cwd)
    if not abs:
        if os.path.abspath(cwd) == os.path.abspath("/"):
            cwd = relpath(cwd)
        else:
            cwd = relpath(cwd) + os.path.sep
        parentdir = relpath(parentdir) + os.path.sep

    if os.path.abspath(cwd) == os.path.abspath("/"):
        parentdir = ""


    # try:
    #     cwd = cwd.encode("utf8")
    # except:
    #     pass
    #
    try:
        folders = os.listdir(cwd)
    except:
        folders = []

    files = []

    for f in folders:
        try:
            # f = f.decode(getfilesystemencoding())
            data = {'name': f, 'fullpath': join(cwd, f)}
            data['sort'] = data['fullpath'].lower()
            data['modified'] = datetime.fromtimestamp(int(os.path.getmtime(join(cwd, f))))
            data['ext'] = os.path.splitext(f)[1]
        except:
            continue

        if os.path.isdir(join(cwd, f)):
            data['type'] = 'dir'
        else:
            data['type'] = 'file'

        if os.path.isfile(join(cwd, f)):
            data['size'] = os.path.getsize(join(cwd, f))

            power = 0
            while (data['size'] / 1024) > 0.3:
                power += 1
                data['size'] /= 1024.
            units = ('', 'K', 'M', 'G', 'T')
            data['unit'] = units[power] + 'Byte'
        else:
            data['size'] = ''

        files.append(data)

    files = sorted(files, key=itemgetter('type', 'sort'))

    return render_to_response('pathchooser.html',
            {'cwd'     : cwd, 'files': files, 'parentdir': parentdir, 'type': browse_for, 'oldfile': oldfile,
             'absolute': abs}, [])


## Views
@error(500)
def error500(error):
    print "An error occured while processing the request."
    if error.traceback:
        print error.traceback

    return base(["An Error occured, please enable debug mode to get more details.", error,
                 error.traceback.replace("\n", "<br>") if error.traceback else "No Traceback"])

# render js
@route("/media/js/<path:re:.+\.js>")
def js_dynamic(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 2))
    response.headers['Cache-control'] = "public"
    response.headers['Content-Type'] = "text/javascript; charset=UTF-8"

    try:
        # static files are not rendered
        if "static" not in path and "mootools" not in path:
            t = env.get_template("js/%s" % path)
            return t.render()
        else:
            return static_file(path, root=join(PROJECT_DIR, "media", "js"))
    except:
        return HTTPError(404, "Not Found")

@route('/media/<path:path>')
def server_static(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"
    return static_file(path, root=join(PROJECT_DIR, "media"))

@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root=join(PROJECT_DIR, "media", "img"))


@route('/robots.txt')
def robots():
    return static_file("robots.txt", root=join(PROJECT_DIR, "media", "txt"))


@route('/login', method="GET")
def login():
    if not PYLOAD and SETUP:
        redirect(PREFIX + "/setup")
    else:
        return render_to_response("login.html", proc=[pre_processor])


@route('/nopermission')
def nopermission():
    return base([_("You dont have permission to access this page.")])


@route("/login", method="POST")
def login_post():
    user = request.forms.get("username")
    password = request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return render_to_response("login.html", {"errors": True}, [pre_processor])

    set_session(request, info)
    return redirect(PREFIX + "/")


@route("/logout")
def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])


@route("/")
@route("/home")
@login_required("LIST")
def home():
    try:
        res = [toDict(x) for x in PYLOAD.statusDownloads()]
    except:
        s = request.environ.get('beaker.session')
        s.delete()
        return redirect(PREFIX + "/login")

    for link in res:
        if link["status"] == 12:
            link["information"] = "%s kB @ %s kB/s" % (link["size"] - link["bleft"], link["speed"])

    return render_to_response("home.html", {"res": res}, [pre_processor])


@route("/queue")
@login_required("LIST")
def queue():
    queue = PYLOAD.getQueue()

    queue.sort(key=attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 1}, [pre_processor])


@route("/collector")
@login_required('LIST')
def collector():
    queue = PYLOAD.getCollector()

    queue.sort(key=attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 0}, [pre_processor])


@route("/downloads")
@login_required('DOWNLOAD')
def downloads():
    root = PYLOAD.getConfigValue("general", "download_folder")

    if not isdir(root):
        return base([_('Download directory not found.')])
    data = {
        'folder': [],
        'files': []
    }

    items = listdir(fs_encode(root))

    for item in sorted([fs_decode(x) for x in items]):
        if isdir(save_join(root, item)):
            folder = {
                'name': item,
                'path': item,
                'files': []
            }
            files = listdir(save_join(root, item))
            for file in sorted([fs_decode(x) for x in files]):
                try:
                    if isfile(save_join(root, item, file)):
                        folder['files'].append(file)
                except:
                    pass

            data['folder'].append(folder)
        elif isfile(join(root, item)):
            data['files'].append(item)

    return render_to_response('downloads.html', {'files': data}, [pre_processor])


@route("/downloads/get/<path:re:.+>")
@login_required("DOWNLOAD")
def get_download(path):
    path = unquote(path).decode("utf8")
    #@TODO some files can not be downloaded

    root = PYLOAD.getConfigValue("general", "download_folder")

    path = path.replace("..", "")
    try:
        return static_file(fs_encode(path), fs_encode(root), download=True)

    except Exception, e:
        print e
        return HTTPError(404, "File not Found.")



@route("/settings")
@login_required('SETTINGS')
def config():
    conf = PYLOAD.getConfig()
    plugin = PYLOAD.getPluginConfig()

    conf_menu = []
    plugin_menu = []

    for entry in sorted(conf.keys()):
        conf_menu.append((entry, conf[entry].description))

    for entry in sorted(plugin.keys()):
        plugin_menu.append((entry, plugin[entry].description))

    accs = []

    for data in PYLOAD.getAccounts(False):
        if data.trafficleft == -1:
            trafficleft = _("unlimited")
        elif not data.trafficleft:
            trafficleft = _("not available")
        else:
            trafficleft = formatSize(data.trafficleft * 1024)

        if data.validuntil == -1:
            validuntil  = _("unlimited")
        elif not data.validuntil :
            validuntil  = _("not available")
        else:
            t = time.localtime(data.validuntil)
            validuntil  = time.strftime("%d.%m.%Y", t)

        if "time" in data.options:
            try:
                _time = data.options["time"][0]
            except:
                _time = ""
        else:
            _time = ""

        if "limitDL" in data.options:
            try:
                limitdl = data.options["limitDL"][0]
            except:
                limitdl = "0"
        else:
            limitdl = "0"

        accs.append({'type': data.type,
                     'login': data.login,
                     'valid': data.valid,
                     'premium': data.premium,
                     'trafficleft': trafficleft,
                     'validuntil': validuntil,
                     'limitdl': limitdl,
                     'time': _time})

    return render_to_response('settings.html',
            {'conf': {'plugin': plugin_menu, 'general': conf_menu, 'accs': accs}, 'types': PYLOAD.getAccountTypes()},
        [pre_processor])


@route("/filechooser")
@route("/filechooser/:file#.+#")
@login_required('STATUS')
def file(file=""):
    return choose_path("file", file)

@route("/pathchooser")
@route("/pathchooser/:path#.+#")
@login_required('STATUS')
def path(path=""):
    return choose_path("folder", path)


@route("/logs")
@route("/logs", method="POST")
@route("/logs/:item")
@route("/logs/:item", method="POST")
@login_required('LOGS')
def logs(item=-1):
    s = request.environ.get('beaker.session')

    perpage = s.get('perpage', 34)
    reversed = s.get('reversed', False)

    warning = ""
    conf = PYLOAD.getConfigValue("log","file_log")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (34, 34), (40, 40), (100, 100), (0, 'all'))
    fro = None

    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        try:
            fro = datetime.strptime(request.forms['from'], '%d.%m.%Y %H:%M:%S')
        except:
            pass
        try:
            perpage = int(request.forms['perpage'])
            s['perpage'] = perpage

            reversed = bool(request.forms.get('reversed', False))
            s['reversed'] = reversed
        except:
            pass

        s.save()

    try:
        item = int(item)
    except:
        pass

    log = PYLOAD.getLog()
    if not perpage:
        item = 0

    if item < 1 or type(item) is not int:
        item = 1 if len(log) - perpage + 1 < 1 or perpage == 0 else len(log) - perpage + 1

    if type(fro) is datetime: # we will search for datetime
        item = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= item:
            try:
                date, time, level, message = l.decode("utf8", "ignore").split(" ", 3)
                dtime = datetime.strptime(date + ' ' + time, '%d.%m.%Y %H:%M:%S')
            except:
                dtime = None
                date = '?'
                time = ' '
                level = '?'
                message = l
            if item == -1 and dtime is not None and fro <= dtime:
                item = counter #found our datetime
            if item >= 0:
                data.append({'line': counter, 'date': date + " " + time, 'level': level, 'message': message})
                perpagecheck += 1
                if fro is None and dtime is not None: #if fro not set set it to first showed line
                    fro = dtime
            if perpagecheck >= perpage > 0:
                break

    if fro is None: #still not set, empty log?
        fro = datetime.now()
    if reversed:
        data.reverse()
    return render_to_response('logs.html', {'warning': warning, 'log': data, 'from': fro.strftime('%d.%m.%Y %H:%M:%S'),
                                            'reversed': reversed, 'perpage': perpage, 'perpage_p': sorted(perpage_p),
                                            'iprev': 1 if item - perpage < 1 else item - perpage,
                                            'inext': (item + perpage) if item + perpage < len(log) else item},
        [pre_processor])


@route("/admin")
@route("/admin", method="POST")
@login_required("ADMIN")
def admin():
    # convert to dict
    user = dict([(name, toDict(y)) for name, y in PYLOAD.getAllUserData().iteritems()])
    perms = permlist()

    for data in user.itervalues():
        data["perms"] = {}
        get_permission(data["perms"], data["permission"])
        data["perms"]["admin"] = True if data["role"] is 0 else False


    s = request.environ.get('beaker.session')
    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        for name in user:
            if request.POST.get("%s|admin" % name, False):
                user[name]["role"] = 0
                user[name]["perms"]["admin"] = True
            elif name != s["name"]:
                user[name]["role"] = 1
                user[name]["perms"]["admin"] = False

            # set all perms to false
            for perm in perms:
                user[name]["perms"][perm] = False

            
            for perm in request.POST.getall("%s|perms" % name):
                user[name]["perms"][perm] = True

            user[name]["permission"] = set_permission(user[name]["perms"])

            PYLOAD.setUserPermission(name, user[name]["permission"], user[name]["role"])

    return render_to_response("admin.html", {"users": user, "permlist": perms}, [pre_processor])


@route("/setup")
def setup():
    if PYLOAD or not SETUP:
        return base([_("Run pyLoadCore.py -s to access the setup.")])

    return render_to_response('setup.html', {"user": False, "perms": False})


@route("/info")
@login_required('STATUS')
def info():
    conf = PYLOAD.getConfigDict()

    if hasattr(os, "uname"):
        extra = os.uname()
    else:
        extra = tuple()

    data = {"python": sys.version,
            "os": " ".join((os.name, sys.platform) + extra),
            "version": PYLOAD.getServerVersion(),
            "folder": abspath(PYLOAD_DIR), "config": abspath(""),
            "download": abspath(conf["general"]["download_folder"]["value"]),
            "freespace": formatSize(PYLOAD.freeSpace()),
            "remote": conf["remote"]["port"]["value"],
            "webif": conf["webinterface"]["port"]["value"],
            "language": conf["general"]["language"]["value"]}

    return render_to_response("info.html", data, [pre_processor])
