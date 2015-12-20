# -*- coding: utf-8 -*-
# @author: RaNaN

import datetime
import operator
import os
import sys
import time
import urllib

import bottle

from pyload.webui import PYLOAD, PYLOAD_DIR, THEME_DIR, THEME, SETUP, env

from pyload.webui.App.utils import render_to_response, parse_permissions, parse_userdata, \
    login_required, get_permission, set_permission, permlist, toDict, set_session

from pyload.utils.filters import relpath, unquotepath

from pyload.utils import formatSize, fs_join, fs_encode, fs_decode

# Helper


def pre_processor():
    s = bottle.request.environ.get('beaker.session')
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
            'url': bottle.request.url,
            'update': update,
            'plugins': plugins}


def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])


# Views
@bottle.error(403)
def error403(code):
    return "The parameter you passed has the wrong format"


@bottle.error(404)
def error404(code):
    return "Sorry, this page does not exist"


@bottle.error(500)
def error500(error):
    traceback = error.traceback
    if traceback:
        print traceback
    return base(["An Error occured, please enable debug mode to get more details.", error,
                 traceback.replace("\n", "<br>") if traceback else "No Traceback"])


@bottle.route('/<theme>/<file:re:(.+/)?[^/]+\.min\.[^/]+>')
def server_min(theme, file):
    filename = os.path.join(THEME_DIR, THEME, theme, file)
    if not os.path.isfile(filename):
        file = file.replace(".min.", ".")
    if file.endswith(".js"):
        return server_js(theme, file)
    else:
        return server_static(theme, file)


@bottle.route('/<theme>/<file:re:.+\.js>')
def server_js(theme, file):
    bottle.response.headers['Content-Type'] = "text/javascript; charset=UTF-8"

    if "/render/" in file or ".render." in file or True:
        bottle.response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                    time.gmtime(time.time() + 24 * 7 * 60 * 60))
        bottle.response.headers['Cache-control'] = "public"

        path = "/".join((theme, file))
        return env.get_template(path).render()
    else:
        return server_static(theme, file)


@bottle.route('/<theme>/<file:re:(.+/)?[^/]+\.[^/]+>')
def server_static(theme, file):
    bottle.response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 24 * 7 * 60 * 60))
    bottle.response.headers['Cache-control'] = "public"

    return bottle.static_file(file, root=os.path.join(THEME_DIR, THEME, theme))


@bottle.route('/favicon.ico')
def favicon():
    return bottle.static_file("icon.ico", root=os.path.join(PYLOAD_DIR, "docs", "resources"))


@bottle.route('/login', method="GET")
def login():
    if not PYLOAD and SETUP:
        bottle.redirect("/setup")
    else:
        return render_to_response("login.html", proc=[pre_processor])


@bottle.route('/nopermission')
def nopermission():
    return base([_("You dont have permission to access this page.")])


@bottle.route('/login', method='POST')
def login_post():
    user = bottle.request.forms.get("username")
    password = bottle.request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return render_to_response("login.html", {"errors": True}, [pre_processor])

    set_session(info)
    return bottle.redirect("/")


@bottle.route('/logout')
def logout():
    s = bottle.request.environ.get('beaker.session')
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])


@bottle.route('/')
@bottle.route('/home')
@login_required("LIST")
def home():
    try:
        res = [toDict(x) for x in PYLOAD.statusDownloads()]
    except Exception:
        s = bottle.request.environ.get('beaker.session')
        s.delete()
        return bottle.redirect("/login")

    for link in res:
        if link['status'] == 12:
            link['information'] = "%s kB @ %s kB/s" % (link['size'] - link['bleft'], link['speed'])

    return render_to_response("home.html", {"res": res}, [pre_processor])


@bottle.route('/queue')
@login_required("LIST")
def queue():
    queue = PYLOAD.getQueue()

    queue.sort(key=operator.attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 1}, [pre_processor])


@bottle.route('/collector')
@login_required('LIST')
def collector():
    queue = PYLOAD.getCollector()

    queue.sort(key=operator.attrgetter("order"))

    return render_to_response('queue.html', {'content': queue, 'target': 0}, [pre_processor])


@bottle.route('/downloads')
@login_required('DOWNLOAD')
def downloads():
    root = PYLOAD.getConfigValue("general", "download_folder")

    if not os.path.isdir(root):
        return base([_('Download directory not found.')])
    data = {
        'folder': [],
        'files': []
    }

    items = os.listdir(fs_encode(root))

    for item in sorted([fs_decode(x) for x in items]):
        if os.path.isdir(fs_join(root, item)):
            folder = {
                'name': item,
                'path': item,
                'files': []
            }
            files = os.listdir(fs_join(root, item))
            for file in sorted([fs_decode(x) for x in files]):
                try:
                    if os.path.isfile(fs_join(root, item, file)):
                        folder['files'].append(file)
                except Exception:
                    pass

            data['folder'].append(folder)
        elif os.path.isfile(os.path.join(root, item)):
            data['files'].append(item)

    return render_to_response('downloads.html', {'files': data}, [pre_processor])


@bottle.route('/downloads/get/<path:path>')
@login_required("DOWNLOAD")
def get_download(path):
    path = urllib.unquote(path).decode("utf8")
    #@TODO some files can not be downloaded

    root = PYLOAD.getConfigValue("general", "download_folder")

    path = path.replace("..", "")
    return bottle.static_file(fs_encode(path), fs_encode(root))


@bottle.route('/settings')
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


@bottle.route('/filechooser')
@bottle.route('/pathchooser')
@bottle.route('/filechooser/<file:path>')
@bottle.route('/pathchooser/<path:path>')
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
            cwd = os.relpath(path)
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
            cwd = os.relpath(cwd)
        else:
            cwd = os.relpath(cwd) + os.path.sep
        parentdir = os.relpath(parentdir) + os.path.sep

    if os.path.abspath(cwd) == "/":
        parentdir = ""

    try:
        folders = os.listdir(cwd)
    except Exception:
        folders = []

    files = []

    for f in folders:
        try:
            f = f.decode(sys.getfilesystemencoding())
            data = {'name': f, 'fullpath': os.path.join(cwd, f)}
            data['sort'] = data['fullpath'].lower()
            data['modified'] = datetime.datetime.fromtimestamp(int(os.path.getmtime(os.path.join(cwd, f))))
            data['ext'] = os.path.splitext(f)[1]
        except Exception:
            continue

        data['type'] = 'dir' if os.path.isdir(os.path.join(cwd, f)) else 'file'

        if os.path.isfile(os.path.join(cwd, f)):
            data['size'] = os.path.getsize(os.path.join(cwd, f))

            power = 0
            while (data['size'] / 1024) > 0.3:
                power += 1
                data['size'] /= 1024.
            units = ('', 'K', 'M', 'G', 'T')
            data['unit'] = units[power] + 'Byte'
        else:
            data['size'] = ''

        files.append(data)

    files = sorted(files, key=operator.itemgetter('type', 'sort'))

    return render_to_response('pathchooser.html',
                              {'cwd': cwd, 'files': files, 'parentdir': parentdir, 'type': type, 'oldfile': oldfile,
                               'absolute': abs}, [])


@bottle.route('/logs')
@bottle.route('/logs', method='POST')
@bottle.route('/logs/<item>')
@bottle.route('/logs/<item>', method='POST')
@login_required('LOGS')
def logs(item=-1):
    s = bottle.request.environ.get('beaker.session')

    perpage = s.get('perpage', 34)
    reversed = s.get('reversed', False)

    warning = ""
    conf = PYLOAD.getConfigValue("log", "file_log")
    if not conf:
        warning = "Warning: File log is disabled, see settings page."

    perpage_p = ((20, 20), (50, 50), (100, 100), (250, 250), (0, 'all'))
    fro = None

    if bottle.request.environ.get('REQUEST_METHOD', "GET") == "POST":
        try:
            fro = datetime.datetime.strptime(bottle.request.forms['from'], '%d.%m.%Y %H:%M:%S')
        except Exception:
            pass
        try:
            perpage = int(bottle.request.forms['perpage'])
            s['perpage'] = perpage

            reversed = bool(bottle.request.forms.get('reversed', False))
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

    if type(fro) is datetime.datetime:  #: we will search for datetime.datetime
        item = -1

    data = []
    counter = 0
    perpagecheck = 0
    for l in log:
        counter += 1

        if counter >= item:
            try:
                date, time, level, message = l.decode("utf8", "ignore").split(" ", 3)
                dtime = datetime.datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M:%S')
            except Exception:
                dtime = None
                date = '?'
                time = ' '
                level = '?'
                message = l

            if item == -1 and dtime is not None and fro <= dtime:
                item = counter  #: found our datetime.datetime

            if item >= 0:
                data.append({'line': counter, 'date': date + " " + time, 'level': level, 'message': message})
                perpagecheck += 1
                if fro is None and dtime is not None:  #: if fro not set set it to first showed line
                    fro = dtime

            if perpagecheck >= perpage > 0:
                break

    if fro is None:  #: still not set, empty log?
        fro = datetime.datetime.now()
    if reversed:
        data.reverse()
    return render_to_response('logs.html', {'warning': warning, 'log': data, 'from': fro.strftime('%d.%m.%Y %H:%M:%S'),
                                            'reversed': reversed, 'perpage': perpage, 'perpage_p': sorted(perpage_p),
                                            'iprev': 1 if item - perpage < 1 else item - perpage,
                                            'inext': (item + perpage) if item + perpage < len(log) else item,
                                            'color_console': PYLOAD.getConfigValue("log", "color_console")},
                              [pre_processor])


@bottle.route('/admin')
@bottle.route('/admin', method='POST')
@login_required("ADMIN")
def admin():
    # convert to dict
    user = dict((name, toDict(y)) for name, y in PYLOAD.getAllUserData().iteritems())
    perms = permlist()

    for data in user.itervalues():
        data['perms'] = {}
        get_permission(data['perms'], data['permission'])
        data['perms']['admin'] = data['role'] is 0

    s = bottle.request.environ.get('beaker.session')
    if bottle.request.environ.get('REQUEST_METHOD', "GET") == "POST":
        for name in user:
            if bottle.request.POST.get("%s|admin" % name, False):
                user[name]['role'] = 0
                user[name]['perms']['admin'] = True
            elif name != s['name']:
                user[name]['role'] = 1
                user[name]['perms']['admin'] = False

            # set all perms to false
            for perm in perms:
                user[name]['perms'][perm] = False

            for perm in bottle.request.POST.getall("%s|perms" % name):
                user[name]['perms'][perm] = True

            user[name]['permission'] = set_permission(user[name]['perms'])

            PYLOAD.setUserPermission(name, user[name]['permission'], user[name]['role'])

    return render_to_response("admin.html", {"users": user, "permlist": perms}, [pre_processor])


@bottle.route('/setup')
def setup():
    return base([_("Run pyload.py -s to access the setup.")])


@bottle.route('/info')
def info():
    conf = PYLOAD.getConfigDict()
    extra = os.uname() if hasattr(os, "uname") else tuple()

    data = {"python"   : sys.version,
            "os"       : " ".join((os.name, sys.platform) + extra),
            "version"  : PYLOAD.getServerVersion(),
            "folder"   : os.path.abspath(PYLOAD_DIR), "config": os.path.abspath(""),
            "download" : os.path.abspath(conf['general']['download_folder']['value']),
            "freespace": formatSize(PYLOAD.freeSpace()),
            "remote"   : conf['remote']['port']['value'],
            "webif"    : conf['webui']['port']['value'],
            "language" : conf['general']['language']['value']}

    return render_to_response("info.html", data, [pre_processor])
