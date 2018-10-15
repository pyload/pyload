# -*- coding: utf-8 -*-
import os
import shutil
import traceback
from builtins import _

import bottle

from pyload.utils.utils import decode, formatSize
from pyload.webui import PYLOAD
from pyload.webui.utils import apiver_check, login_required, render_to_response, toDict


def format_time(seconds):
    seconds = int(seconds)

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)


def get_sort_key(item):
    return item["order"]


@bottle.route(r"/json/<apiver>/status")
@bottle.route(r"/json/<apiver>/status", method="POST")
@apiver_check
@login_required("LIST")
def status():
    try:
        status = toDict(PYLOAD.statusServer())
        status["captcha"] = PYLOAD.isCaptchaWaiting()
        return status
    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/links")
@bottle.route(r"/json/<apiver>/links", method="POST")
@apiver_check
@login_required("LIST")
def links():
    try:
        links = [toDict(x) for x in PYLOAD.statusDownloads()]
        ids = []
        for link in links:
            ids.append(link["fid"])

            if link["status"] == 12:
                link["info"] = "{} @ {}/s".format(
                    link["format_eta"], formatSize(link["speed"])
                )
            elif link["status"] == 5:
                link["percent"] = 0
                link["size"] = 0
                link["bleft"] = 0
                link["info"] = _("waiting {}").format(link["format_wait"])
            else:
                link["info"] = ""

        data = {"links": links, "ids": ids}
        return data
    except Exception as e:
        traceback.print_exc()
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/packages")
@apiver_check
@login_required("LIST")
def packages():
    print("/json/packages")
    try:
        data = PYLOAD.getQueue()

        for package in data:
            package["links"] = []
            for file in PYLOAD.get_package_files(package["id"]):
                package["links"].append(PYLOAD.get_file_info(file))

        return data

    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/package/<id:int>")
@apiver_check
@login_required("LIST")
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

    except Exception:
        traceback.print_exc()
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/package_order/<ids>")
@apiver_check
@login_required("ADD")
def package_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.orderPackage(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/abort_link/<id:int>")
@apiver_check
@login_required("DELETE")
def abort_link(id):
    try:
        PYLOAD.stopDownloads([id])
        return {"response": "success"}
    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/link_order/<ids>")
@apiver_check
@login_required("ADD")
def link_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.orderFile(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/add_package")
@bottle.route(r"/json/<apiver>/add_package", method="POST")
@apiver_check
@login_required("ADD")
def add_package():
    name = bottle.request.forms.get("add_name", "New Package").strip()
    queue = int(bottle.request.forms["add_dest"])
    links = decode(bottle.request.forms["add_links"])
    links = links.split("\n")
    pw = bottle.request.forms.get("add_password", "").strip("\n\r")

    try:
        f = bottle.request.files["add_file"]

        if not name or name == "New Package":
            name = f.name

        fpath = os.path.join(
            PYLOAD.getConfigValue("general", "download_folder"), "tmp_" + f.filename
        )
        with open(fpath, "wb") as destination:
            shutil.copyfileobj(f.file, destination)
        links.insert(0, fpath)
    except Exception:
        pass

    name = name.decode("utf8", "ignore")
    links = list(filter(None, map(str.strip, links)))
    pack = PYLOAD.addPackage(name, links, queue)
    if pw:
        pw = pw.decode("utf8", "ignore")
        data = {"password": pw}
        PYLOAD.setPackageData(pack, data)


@bottle.route(r"/json/<apiver>/move_package/<dest:int>/<id:int>")
@apiver_check
@login_required("MODIFY")
def move_package(dest, id):
    try:
        PYLOAD.movePackage(dest, id)
        return {"response": "success"}
    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/edit_package", method="POST")
@apiver_check
@login_required("MODIFY")
def edit_package():
    try:
        id = int(bottle.request.forms.get("pack_id"))
        data = {
            "name": bottle.request.forms.get("pack_name").decode("utf8", "ignore"),
            "folder": bottle.request.forms.get("pack_folder").decode("utf8", "ignore"),
            "password": bottle.request.forms.get("pack_pws").decode("utf8", "ignore"),
        }

        PYLOAD.setPackageData(id, data)
        return {"response": "success"}

    except Exception:
        return bottle.HTTPError()


@bottle.route(r"/json/<apiver>/set_captcha")
@bottle.route(r"/json/<apiver>/set_captcha", method="POST")
@apiver_check
@login_required("ADD")
def set_captcha():
    if bottle.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        try:
            PYLOAD.setCaptchaResult(
                bottle.request.forms["cap_id"], bottle.request.forms["cap_result"]
            )
        except Exception:
            pass

    task = PYLOAD.getCaptchaTask()

    if task.tid >= 0:
        return {
            "captcha": True,
            "id": task.tid,
            "params": task.data,
            "result_type": task.resultType,
        }
    else:
        return {"captcha": False}


@bottle.route(r"/json/<apiver>/load_config/<category>/<section>")
@apiver_check
@login_required("SETTINGS")
def load_config(category, section):
    conf = None
    if category == "general":
        conf = PYLOAD.getConfigDict()
    elif category == "plugin":
        conf = PYLOAD.getPluginConfigDict()

    for key, option in conf[section].items():
        if key in ("desc", "outline"):
            continue

        if ";" in option["type"]:
            option["list"] = option["type"].split(";")

        option["value"] = decode(option["value"])

    return render_to_response(
        "settings_item.html", {"skey": section, "section": conf[section]}
    )


@bottle.route(r"/json/<apiver>/save_config/<category>", method="POST")
@apiver_check
@login_required("SETTINGS")
def save_config(category):
    for key, value in bottle.request.POST.items():
        try:
            section, option = key.split("|")
        except Exception:
            continue

        if category == "general":
            category = "core"

        PYLOAD.setConfigValue(section, option, decode(value), category)


@bottle.route(r"/json/<apiver>/add_account", method="POST")
@apiver_check
@login_required("ACCOUNTS")
def add_account():
    login = bottle.request.POST["account_login"]
    password = bottle.request.POST["account_password"]
    type = bottle.request.POST["account_type"]

    PYLOAD.updateAccount(type, login, password)


@bottle.route(r"/json/<apiver>/update_accounts", method="POST")
@apiver_check
@login_required("ACCOUNTS")
def update_accounts():
    deleted = []  # dont update deleted accs or they will be created again

    for name, value in bottle.request.POST.items():
        value = value.strip()
        if not value:
            continue

        tmp, user = name.split(";")
        plugin, action = tmp.split("|")

        if (plugin, user) in deleted:
            continue

        if action == "password":
            PYLOAD.updateAccount(plugin, user, value)
        elif action == "time" and "-" in value:
            PYLOAD.updateAccount(plugin, user, options={"time": [value]})
        elif action == "limitdl" and value.isdigit():
            PYLOAD.updateAccount(plugin, user, options={"limitDL": [value]})
        elif action == "delete":
            deleted.append((plugin, user))
            PYLOAD.removeAccount(plugin, user)


@bottle.route(r"/json/<apiver>/change_password", method="POST")
@apiver_check
def change_password():

    user = bottle.request.POST["user_login"]
    oldpw = bottle.request.POST["login_current_password"]
    newpw = bottle.request.POST["login_new_password"]

    if not PYLOAD.changePassword(user, oldpw, newpw):
        print("Wrong password")
        return bottle.HTTPError()
