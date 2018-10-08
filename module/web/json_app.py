#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join
from traceback import print_exc
from shutil import copyfileobj

from bottle import route, request, HTTPError

from webinterface import PYLOAD

from utils import login_required, render_to_response, toDict

from module.utils import decode, formatSize


def format_time(seconds):
    seconds = int(seconds)

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)


def get_sort_key(item):
    return item["order"]


@route("/json/status")
@route("/json/status", method="POST")
@login_required('LIST')
def status():
    try:
        status = toDict(PYLOAD.statusServer())
        status['captcha'] = PYLOAD.isCaptchaWaiting()
        return status
    except:
        return HTTPError()


@route("/json/links")
@route("/json/links", method="POST")
@login_required('LIST')
def links():
    try:
        links = [toDict(x) for x in PYLOAD.statusDownloads()]
        ids = []
        for link in links:
            ids.append(link['fid'])

            if link['status'] == 12:
                link['info'] = "%s @ %s/s" % (link['format_eta'], formatSize(link['speed']))
            elif link['status'] == 5:
                link['percent'] = 0
                link['size'] = 0
                link['bleft'] = 0
                link['info'] = _("waiting %s") % link['format_wait']
            else:
                link['info'] = ""

        data = {'links': links, 'ids': ids}
        return data
    except Exception, e:
        print_exc()
        return HTTPError()


@route("/json/packages")
@login_required('LIST')
def packages():
    print "/json/packages"
    try:
        data = PYLOAD.getQueue()

        for package in data:
            package['links'] = []
            for file in PYLOAD.get_package_files(package['id']):
                package['links'].append(PYLOAD.get_file_info(file))

        return data

    except:
        return HTTPError()


@route("/json/package/<id:int>")
@login_required('LIST')
def package(id):
    try:
        data = toDict(PYLOAD.getPackageData(id))
        data["links"] = [toDict(x) for x in data["links"]]

        for pyfile in data["links"]:
            if pyfile["status"] == 0:
                pyfile["icon"] = "status_finished.png"
            elif pyfile["status"] in (2, 3):
                pyfile["icon"] = "status_queue.png"
            elif pyfile["status"] in (9, 1):
                pyfile["icon"] = "status_offline.png"
            elif pyfile["status"] == 5:
                pyfile["icon"] = "status_waiting.png"
            elif pyfile["status"] == 8:
                pyfile["icon"] = "status_failed.png"
            elif pyfile["status"] == 4:
                pyfile["icon"] = "arrow_right.png"
            elif pyfile["status"] in (11, 13):
                pyfile["icon"] = "status_proc.png"
            else:
                pyfile["icon"] = "status_downloading.png"

        tmp = data["links"]
        tmp.sort(key=get_sort_key)
        data["links"] = tmp
        return data

    except:
        print_exc()
        return HTTPError()


@route("/json/package_order/:ids")
@login_required('ADD')
def package_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.orderPackage(int(pid), int(pos))
        return {"response": "success"}
    except:
        return HTTPError()


@route("/json/abort_link/<id:int>")
@login_required('DELETE')
def abort_link(id):
    try:
        PYLOAD.stopDownloads([id])
        return {"response": "success"}
    except:
        return HTTPError()


@route("/json/link_order/:ids")
@login_required('ADD')
def link_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.orderFile(int(pid), int(pos))
        return {"response": "success"}
    except:
        return HTTPError()


@route("/json/add_package")
@route("/json/add_package", method="POST")
@login_required('ADD')
def add_package():
    name = request.forms.get("add_name", "New Package").strip()
    queue = int(request.forms['add_dest'])
    links = decode(request.forms['add_links'])
    links = links.split("\n")
    pw = request.forms.get("add_password", "").strip("\n\r")

    try:
        f = request.files['add_file']

        if not name or name == "New Package":
            name = f.name

        fpath = join(PYLOAD.getConfigValue("general", "download_folder"), "tmp_" + f.filename)
        destination = open(fpath, 'wb')
        copyfileobj(f.file, destination)
        destination.close()
        links.insert(0, fpath)
    except:
        pass

    name = name.decode("utf8", "ignore")

    links = map(lambda x: x.strip(), links)
    links = filter(lambda x: x != "", links)

    pack = PYLOAD.addPackage(name, links, queue)
    if pw:
        pw = pw.decode("utf8", "ignore")
        data = {"password": pw}
        PYLOAD.setPackageData(pack, data)


@route("/json/move_package/<dest:int>/<id:int>")
@login_required('MODIFY')
def move_package(dest, id):
    try:
        PYLOAD.movePackage(dest, id)
        return {"response": "success"}
    except:
        return HTTPError()


@route("/json/edit_package", method="POST")
@login_required('MODIFY')
def edit_package():
    try:
        id = int(request.forms.get("pack_id"))
        data = {"name": request.forms.get("pack_name").decode("utf8", "ignore"),
                "folder": request.forms.get("pack_folder").decode("utf8", "ignore"),
                 "password": request.forms.get("pack_pws").decode("utf8", "ignore")}

        PYLOAD.setPackageData(id, data)
        return {"response": "success"}

    except:
        return HTTPError()


@route("/json/set_captcha")
@route("/json/set_captcha", method="POST")
@login_required('ADD')
def set_captcha():
    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        try:
            PYLOAD.setCaptchaResult(request.forms["cap_id"], request.forms["cap_result"])
        except:
            pass

    task = PYLOAD.getCaptchaTask()

    if task.tid >= 0:
        return {'captcha': True,
                'id': task.tid,
                'params': task.data,
                'result_type' : task.resultType}
    else:
        return {'captcha': False}


@route("/json/load_config/:category/:section")
@login_required("SETTINGS")
def load_config(category, section):
    conf = None
    if category == "general":
        conf = PYLOAD.getConfigDict()
    elif category == "plugin":
        conf = PYLOAD.getPluginConfigDict()

    for key, option in conf[section].iteritems():
        if key in ("desc","outline"): continue

        if ";" in option["type"]:
            option["list"] = option["type"].split(";")

        option["value"] = decode(option["value"])

    return render_to_response("settings_item.html", {"skey": section, "section": conf[section]})


@route("/json/save_config/:category", method="POST")
@login_required("SETTINGS")
def save_config(category):
    for key, value in request.POST.iteritems():
        try:
            section, option = key.split("|")
        except:
            continue

        if category == "general": category = "core"

        PYLOAD.setConfigValue(section, option, decode(value), category)


@route("/json/add_account", method="POST")
@login_required("ACCOUNTS")
def add_account():
    login = request.POST["account_login"]
    password = request.POST["account_password"]
    type = request.POST["account_type"]

    PYLOAD.updateAccount(type, login, password)


@route("/json/update_accounts", method="POST")
@login_required("ACCOUNTS")
def update_accounts():
    deleted = [] #dont update deleted accs or they will be created again

    for name, value in request.POST.iteritems():
        value = value.strip()
        if not value: continue
        
        tmp, user = name.split(";")
        plugin, action = tmp.split("|")

        if (plugin, user) in deleted: continue

        if action == "password":
            PYLOAD.updateAccount(plugin, user, value)
        elif action == "time" and "-" in value:
            PYLOAD.updateAccount(plugin, user, options={"time": [value]})
        elif action == "limitdl" and value.isdigit():
            PYLOAD.updateAccount(plugin, user, options={"limitDL": [value]})
        elif action == "delete":
            deleted.append((plugin,user))
            PYLOAD.removeAccount(plugin, user)

@route("/json/change_password", method="POST")
def change_password():

    user = request.POST["user_login"]
    oldpw = request.POST["login_current_password"]
    newpw = request.POST["login_new_password"]

    if not PYLOAD.changePassword(user, oldpw, newpw):
        print "Wrong password"
        return HTTPError()
