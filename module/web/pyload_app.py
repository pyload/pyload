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
from copy import deepcopy
from datetime import datetime
from itertools import chain
from operator import itemgetter
import os

import time
from os import listdir
from os.path import isdir
from os.path import isfile
from os.path import join
from sys import getfilesystemencoding
from hashlib import sha1
from urllib import unquote

from bottle import route, static_file, request, response, redirect, HTTPError, error

from webinterface import PYLOAD, PROJECT_DIR, SETUP

from utils import render_to_response, parse_permissions, parse_userdata, login_required
from filters import relpath, unquotepath

from module.utils import formatSize, decode

# Helper

def pre_processor():
    s = request.environ.get('beaker.session')
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    if user["is_authenticated"]:
        status = PYLOAD.status_server()
    captcha = False
    if user["is_authenticated"]:
        captcha = PYLOAD.is_captcha_waiting()
    return {"user": user,
            'status': status,
            'captcha': captcha,
            'perms': perms}


def get_sort_key(item):
    return item[1]["order"]


def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])


## Views
@error(500)
def error500(error):
    if request.header.get('X-Requested-With') == 'XMLHttpRequest':
                    return HTTPError(500, error.traceback)
    
    return base(["An Error occured, please enable debug mode to get more details.", error,
                 error.traceback.replace("\n", "<br>") if error.traceback else "No Traceback"])


@route('/media/:path#.+#')
def server_static(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"
    return static_file(path, root=join(PROJECT_DIR, "media"))

@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root=join(PROJECT_DIR, "media", "img"))

@route('/login', method="GET")
def login():
    if not PYLOAD and SETUP:
        redirect("/setup")
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

    s = request.environ.get('beaker.session')
    s["authenticated"] = True
    s["id"] = info["id"]
    s["name"] = info["name"]
    s["role"] = info["role"]
    s["perms"] = info["permission"]
    s["template"] = info["template"]
    s.save()

    return redirect("/")

@route("/logout")
def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])


@route("/")
@route("/home")
@login_required("see_downloads")
def home():
    try:
        res = PYLOAD.status_downloads()
    except:
        s = request.environ.get('beaker.session')
        s.delete()
        return redirect("/login")

    for link in res:
        if link["status"] == 12:
            link["information"] = "%s kB @ %s kB/s" % (link["size"] - link["kbleft"], link["speed"])

    return render_to_response("home.html", {"res": res}, [pre_processor])


@route("/queue")
@login_required("see_downloads")
def queue():
    queue = PYLOAD.get_queue_info()

    data = zip(queue.keys(), queue.values())
    data.sort(key=get_sort_key)

    return render_to_response('queue.html', {'content': data}, [pre_processor])

@route("/collector")
@login_required('see_downloads')
def collector():
    queue = PYLOAD.get_collector_info()

    data = zip(queue.keys(), queue.values())
    data.sort(key=get_sort_key)

    return render_to_response('collector.html', {'content': data}, [pre_processor])

@route("/downloads")
@login_required('download')
def downloads():
    root = PYLOAD.get_conf_val("general", "download_folder")

    if not isdir(root):
        return base([_('Download directory not found.')])
    data = {
        'folder': [],
        'files': []
    }

    for item in sorted(listdir(root)):
        if isdir(join(root, item)):
            folder = {
                'name': decode(item),
                'path': decode(item),
                'files': []
            }
            for file in sorted(listdir(join(root, item))):
                try:
                    if isfile(join(root, item, file)):
                        folder['files'].append(decode(file))
                except:
                    pass

            data['folder'].append(folder)
        elif isfile(join(root, item)):
            data['files'].append(item)

    return render_to_response('downloads.html', {'files': data}, [pre_processor])

@route("/downloads/get/:path#.+#")
@login_required("download")
def get_download(path):
    path = unquote(path)
    #@TODO some files can not be downloaded

    root = PYLOAD.get_conf_val("general", "download_folder")

    path = path.replace("..", "")
    try:
        return static_file(path, root)

    except Exception, e:
        print e
        return HTTPError(404, "File not Found.")

@route("/settings")
@route("/settings", method="POST")
@login_required('settings')
def config():
    conf = PYLOAD.get_config()
    plugin = PYLOAD.get_plugin_config()
    accs = PYLOAD.get_accounts()
    messages = []

    for section in chain(conf.itervalues(), plugin.itervalues()):
        for key, option in section.iteritems():
            if key == "desc": continue

            if ";" in option["type"]:
                option["list"] = option["type"].split(";")

    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        errors = []

        for key, value in request.POST.iteritems():
            if not "|" in key: continue
            sec, skey, okey = key.split("|")[:]

            if sec == "General":
                if conf.has_key(skey):
                    if conf[skey].has_key(okey):
                        try:
                            if str(conf[skey][okey]['value']) != value:
                                PYLOAD.set_conf_val(skey, okey, value)
                        except Exception, e:
                            errors.append("%s | %s : %s" % (skey, okey, e))
                    else:
                        continue
                else:
                    continue

            elif sec == "Plugin":
                if plugin.has_key(skey):
                    if plugin[skey].has_key(okey):
                        try:
                            if str(plugin[skey][okey]['value']) != value:
                                PYLOAD.set_conf_val(skey, okey, value, "plugin")
                        except Exception, e:
                            errors.append("%s | %s : %s" % (skey, okey, e))
                    else:
                        continue
                else:
                    continue
            elif sec == "Accounts":
                if ";" in okey:
                    action, name = okey.split(";")
                    if action == "delete":
                        PYLOAD.remove_account(skey, name)

                if okey == "newacc" and value:
                    # add account

                    pw = request.POST.get("Accounts|%s|newpw" % skey)
                    PYLOAD.update_account(skey, value, pw)

        for pluginname, accdata in accs.iteritems():
            for data in accdata:
                newpw = request.POST.get("Accounts|%s|password;%s" % (pluginname, data["login"]), "").strip()
                new_time = request.POST.get("Accounts|%s|time;%s" % (pluginname, data["login"]), "").strip()

                if newpw or (
                new_time and (not data["options"].has_key("time") or [new_time] != data["options"]["time"])):
                    PYLOAD.update_account(pluginname, data["login"], newpw, {"time": [new_time]})

        if errors:
            messages.append(_("Error occured when setting the following options:"))
            messages.append("")
            messages += errors
        else:
            messages.append(_("All options were set correctly."))

    accs = deepcopy(PYLOAD.get_accounts(False, False))
    for accounts in accs.itervalues():
        for data in accounts:
            if data["trafficleft"] == -1:
                data["trafficleft"] = _("unlimited")
            elif not data["trafficleft"]:
                data["trafficleft"] = _("not available")
            else:
                data["trafficleft"] = formatSize(data["trafficleft"] * 1024)

            if data["validuntil"] == -1:
                data["validuntil"] = _("unlimited")
            elif not data["validuntil"]:
                data["validuntil"] = _("not available")
            else:
                t = time.localtime(data["validuntil"])
                data["validuntil"] = time.strftime("%d.%m.%Y", t)

            if data["options"].has_key("time"):
                try:
                    data["time"] = data["options"]["time"][0]
                except:
                    data["time"] = "invalid"

    return render_to_response('settings.html',
                              {'conf': {'Plugin': plugin, 'General': conf, 'Accounts': accs}, 'errors': messages},
                              [pre_processor])

@route("/package_ui.js")
@login_required('see_downloads')
def package_ui():
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"
    return render_to_response('package_ui.js')


@route("/filechooser")
@route("/pathchooser")
@route("/filechooser/:file#.+#")
@route("/pathchooser/:path#.+#")
@login_required('status')
def path(file="", path=""):
    if file:
        type = "file"
    else:
        type = "folder"

    path = os.path.normpath(unquotepath(path))

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

    try:
        cwd = cwd.encode("utf8")
    except:
        pass

    cwd = os.path.normpath(os.path.abspath(cwd))
    parentdir = os.path.dirname(cwd)
    if not abs:
        if os.path.abspath(cwd) == "/":
            cwd = relpath(cwd)
        else:
            cwd = relpath(cwd) + os.path.sep
        parentdir = relpath(parentdir) + os.path.sep

    if os.path.abspath(cwd) == "/":
        parentdir = ""

    try:
        folders = os.listdir(cwd)
    except:
        folders = []

    files = []

    for f in folders:
        try:
            f = f.decode(getfilesystemencoding())
            data = {}
            data['name'] = f
            data['fullpath'] = join(cwd, f)
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
                              {'cwd': cwd, 'files': files, 'parentdir': parentdir, 'type': type, 'oldfile': oldfile,
                               'absolute': abs}, [])

@route("/logs")
@route("/logs", method="POST")
@route("/logs/:item")
@route("/logs/:item", method="POST")
@login_required('status')
def logs(item=-1):
    s = request.environ.get('beaker.session')

    perpage = s.get('perpage', 34)
    reversed = s.get('reversed', False)

    warning = ""
    conf = PYLOAD.get_config()
    if not conf['log']['file_log']['value']:
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

    log = PYLOAD.get_log()
    if not perpage:
        item = 0

    if item < 1 or type(item) is not int:
        item = 1 if len(log) - perpage + 1 < 1 else len(log) - perpage + 1

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
@login_required("settings")
def admin():
    return base(["Comming Soon."])


@route("/setup")
def setup():
    if PYLOAD or not SETUP:
        return base([_("Run pyLoadCore.py -s to access the setup.")])

    return render_to_response('setup.html', {"user" : False, "perms": False})
