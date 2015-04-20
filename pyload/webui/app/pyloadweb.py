# -*- coding: utf-8 -*-
# @author: RaNaN

from datetime import datetime
from operator import itemgetter, attrgetter

import time
import os
import sys
from os import listdir
from os.path import isdir, isfile, join, abspath
from sys import getfilesystemencoding
from urllib import unquote

from bottle import route, static_file, request, response, redirect, error

from pyload.webui import PYLOAD, PYLOAD_DIR, THEME_DIR, THEME, SETUP, env

from pyload.webui.app.utils import render_to_response, parse_permissions, parse_userdata, \
    login_required, get_permission, set_permission, permlist, toDict, set_session

from pyload.webui.filters import relpath, unquotepath

from pyload.utils import formatSize, fs_join, fs_encode, fs_decode

# Helper


def pre_processor():
    s = request.environ.get('beaker.session')
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    if user['is_authenticated']:
        status = PYLOAD.statusServer()
        info = PYLOAD.getInfoByPlugin("UpdateManager")
        captcha = PYLOAD.isCaptchaWaiting()

        # check if update check is available
        if info:
            if info['pyload'] == "True":
                update = info['version']
            if info['plugins'] == "True":
                plugins = True

    return {"user": user,
            'status': status,
            'captcha': captcha,
            'perms': perms,
            'url': request.url,
            'update': update,
            'plugins': plugins}


def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])


# Views
@error(403)
def error403(code):
    return "The parameter you passed has the wrong format"


@error(404)
def error404(code):
    return "Sorry, this page does not exist"


@error(500)
def error500(error):
    traceback = error.traceback
    if traceback:
        print traceback
    return base(["An Error occured, please enable debug mode to get more details.", error,
                 traceback.replace("\n", "<br>") if traceback else "No Traceback"])


@route('/<theme>/<file:re:(.+/)?[^/]+\.min\.[^/]+>')
def server_min(theme, file):
    filename = join(THEME_DIR, THEME, theme, file)
    if not isfile(filename):
        file = file.replace(".min.", ".")
    if file.endswith(".js"):
        return server_js(theme, file)
    else:
        return server_static(theme, file)


@route('/<theme>/<file:re:.+\.js>')
def server_js(theme, file):
    response.headers['Content-Type'] = "text/javascript; charset=UTF-8"

    if "/render/" in file or ".render." in file or True:
        response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                    time.gmtime(time.time() + 24 * 7 * 60 * 60))
        response.headers['Cache-control'] = "public"

        path = "/".join((theme, file))
        return env.get_template(path).render()
    else:
        return server_static(theme, file)


@route('/<theme>/<file:path>')
def server_static(theme, file):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 24 * 7 * 60 * 60))
    response.headers['Cache-control'] = "public"

    return static_file(file, root=join(THEME_DIR, THEME, theme))


@route('/favicon.ico')
def favicon():
    return static_file("icon.ico", root=join(PYLOAD_DIR, "docs", "resources"))


@route('/login', method="GET")
def login():
    if not PYLOAD and SETUP:
        redirect("/setup")
    else:
        return render_to_response("login.html", proc=[pre_processor])


@route('/nopermission')
def nopermission():
    return base([_("You dont have permission to access this page.")])


@route('/login', method='POST')
def login_post():
    user = request.forms.get("username")
    password = request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return render_to_response("login.html", {"errors": True}, [pre_processor])

    set_session(request, info)
    return redirect("/")


@route('/logout')
def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])


@route('/')
@route('/home')
@login_required("LIST")
def home():
    try:
        res = [toDict(x) for x in PYLOAD.statusDownloads()]
    except Exception:
        s = request.environ.get('beaker.session')
        s.delete()
        return redirect("/login")

    for link in res:
        if link['status'] == 12:
            link['information'] = "%s kB @ %s kB/s" % (link['size'] - link['bleft'], link['speed'])

    return render_to_response("home.html", {"res": res}, [pre_processor])


@route('/queue')
@login_required("LIST")
def queue():
    queue = PYLOAD.getQueue()

    queue.sort(key=attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 1}, [pre_processor])


@route('/collector')
@login_required('LIST')
def collector():
    queue = PYLOAD.getCollector()

    queue.sort(key=attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 0}, [pre_processor])


@route('/downloads')
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
        if isdir(fs_join(root, item)):
            folder = {
                'name': item,
                'path': item,
                'files': []
            }
            files = listdir(fs_join(root, item))
            for file in sorted([fs_decode(x) for x in files]):
                try:
                    if isfile(fs_join(root, item, file)):
                        folder['files'].append(file)
                except Exception:
                    pass

            data['folder'].append(folder)
        elif isfile(join(root, item)):
            data['files'].append(item)

    return render_to_response('downloads.html', {'files': data}, [pre_processor])


@route('/downloads/get/<path:path>')
@login_required("DOWNLOAD")
def get_download(path):
    path = unquote(path).decode("utf8")
    # @TODO some files can not be downloaded

    root = PYLOAD.getConfigValue("general", "download_folder")

    path = path.replace("..", "")
    return static_file(fs_encode(path), fs_encode(root))


@route('/settings')
@login_required('SETTINGS')
def config():
    conf = PYLOAD.getConfig()
    plugin = PYLOAD.getPluginConfig()
    conf_menu = []
    plugin_menu = []

    for entry in sorted(conf.keys()):
        conf_menu.append((entry, conf[entry].description))

    last_name = None
    for entry in sorted(plugin.keys()):
        desc = plugin[entry].description
        name, none, type = desc.partition("_")

        if type in PYLOAD.core.pluginManager.TYPES:
            if name == last_name or len([a for a, b in plugin.iteritems() if b.description.startswith(name + "_")]) > 1:
                desc = name + " (" + type.title() + ")"
            else:
                desc = name
            last_name = name
        plugin_menu.append((entry, desc))

    accs = PYLOAD.getAccounts(False)

    for data in accs:
        if data.trafficleft == -1:
            data.trafficleft = _("unlimited")
        elif not data.trafficleft:
            data.trafficleft = _("not available")
        else:
            data.trafficleft = formatSize(data.trafficleft)

        if data.validuntil == -1:
            data.validuntil = _("unlimited")
        elif not data.validuntil:
            data.validuntil = _("not available")
        else:
            t = time.localtime(data.validuntil)
            data.validuntil = time.strftime("%d.%m.%Y - %H:%M:%S", t)

        try:
            data.options['time'] = data.options['time'][0]
        except Exception:
            data.options['time'] = "0:00-0:00"

        if "limitDL" in data.options:
            data.options['limitdl'] = data.options['limitDL'][0]
        else:
            data.options['limitdl'] = "0"

    return render_to_response('settings.html',
                              {'conf': {'plugin': plugin_menu, 'general': conf_menu, 'accs': accs},
                               'types': PYLOAD.getAccountTypes()},
                              [pre_processor])


@route('/filechooser')
@route('/pathchooser')
@route('/filechooser/<file:path>')
@route('/pathchooser/<path:path>')
@login_required('STATUS')
def path(file="", path=""):
    type = "file" if file else "folder"

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
    except Exception:
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
    except Exception:
        folders = []

    files = []

    for f in folders:
        try:
            f = f.decode(getfilesystemencoding())
            data = {'name': f, 'fullpath': join(cwd, f)}
            data['sort'] = data['fullpath'].lower()
            data['modified'] = datetime.fromtimestamp(int(os.path.getmtime(join(cwd, f))))
            data['ext'] = os.path.splitext(f)[1]
        except Exception:
            continue

        data['type'] = 'dir' if os.path.isdir(join(cwd, f)) else 'file'

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


@route('/logs')
@route('/logs', method='POST')
@route('/logs/<item>')
@route('/logs/<item>', method='POST')
@login_required('LOGS')
def logs(item=-1):
    s = request.environ.get('beaker.session')

    perpage = s.get('perpage', 34)
    reversed = s.get('reversed', False)

    warning = ""
    conf = PYLOAD.getConfigValue("log", "file_log")
    color_template = PYLOAD.getConfigValue("log", "color_template") if PYLOAD.getConfigValue("log", "color_console") else ""
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (34, 34), (40, 40), (100, 100), (0, 'all'))
    fro = None

    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        try:
            fro = datetime.strptime(request.forms['from'], '%d.%m.%Y %H:%M:%S')
        except Exception:
            pass
        try:
            perpage = int(request.forms['perpage'])
            s['perpage'] = perpage

            reversed = bool(request.forms.get('reversed', False))
            s['reversed'] = reversed
        except Exception:
            pass

        s.save()

    try:
        item = int(item)
    except Exception:
        pass

    log = PYLOAD.getLog()
    if not perpage:
        item = 1

    if item < 1 or type(item) is not int:
        item = 1 if len(log) - perpage + 1 < 1 else len(log) - perpage + 1

    if type(fro) is datetime:  # we will search for datetime
        item = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= item:
            try:
                date, time, level, message = l.decode("utf8", "ignore").split(" ", 3)
                dtime = datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M:%S')
            except Exception:
                dtime = None
                date = '?'
                time = ' '
                level = '?'
                message = l
            if item == -1 and dtime is not None and fro <= dtime:
                item = counter  # found our datetime
            if item >= 0:
                data.append({'line': counter, 'date': date + " " + time, 'level': level, 'message': message})
                perpagecheck += 1
                if fro is None and dtime is not None:  # if fro not set set it to first showed line
                    fro = dtime
            if perpagecheck >= perpage > 0:
                break

    if fro is None:  # still not set, empty log?
        fro = datetime.now()
    if reversed:
        data.reverse()
    return render_to_response('logs.html', {'warning': warning, 'log': data, 'from': fro.strftime('%d.%m.%Y %H:%M:%S'),
                                            'reversed': reversed, 'perpage': perpage, 'perpage_p': sorted(perpage_p),
                                            'iprev': 1 if item - perpage < 1 else item - perpage,
                                            'inext': (item + perpage) if item + perpage < len(log) else item,
                                            'color_template': color_template.title()},
                              [pre_processor])


@route('/admin')
@route('/admin', method='POST')
@login_required("ADMIN")
def admin():
    # convert to dict
    user = dict((name, toDict(y)) for name, y in PYLOAD.getAllUserData().iteritems())
    perms = permlist()

    for data in user.itervalues():
        data['perms'] = {}
        get_permission(data['perms'], data['permission'])
        data['perms']['admin'] = data['role'] is 0

    s = request.environ.get('beaker.session')
    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        for name in user:
            if request.POST.get("%s|admin" % name, False):
                user[name]['role'] = 0
                user[name]['perms']['admin'] = True
            elif name != s['name']:
                user[name]['role'] = 1
                user[name]['perms']['admin'] = False

            # set all perms to false
            for perm in perms:
                user[name]['perms'][perm] = False

            for perm in request.POST.getall("%s|perms" % name):
                user[name]['perms'][perm] = True

            user[name]['permission'] = set_permission(user[name]['perms'])

            PYLOAD.setUserPermission(name, user[name]['permission'], user[name]['role'])

    return render_to_response("admin.html", {"users": user, "permlist": perms}, [pre_processor])


@route('/setup')
def setup():
    return base([_("Run pyload.py -s to access the setup.")])


@route('/info')
def info():
    conf = PYLOAD.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    data = {"python"   : sys.version,
            "os"       : " ".join((os.name, sys.platform) + extra),
            "version"  : PYLOAD.getServerVersion(),
            "folder"   : abspath(PYLOAD_DIR), "config": abspath(""),
            "download" : abspath(conf['general']['download_folder']['value']),
            "freespace": formatSize(PYLOAD.freeSpace()),
            "remote"   : conf['remote']['port']['value'],
            "webif"    : conf['webui']['port']['value'],
            "language" : conf['general']['language']['value']}

    return render_to_response("info.html", data, [pre_processor])
