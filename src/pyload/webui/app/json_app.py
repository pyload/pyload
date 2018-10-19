# -*- coding: utf-8 -*-

import os
import shutil
from builtins import _

import flask
from pyload.webui.app import app

from pyload.utils.utils import decode, formatSize
from pyload.webui.app.utils import (apiver_check, login_required, render_to_response,
                                    toDict)
from pyload.webui.server_thread import PYLOAD_API


bp = flask.Blueprint('json', __name__, url_prefix='/json')

def format_time(seconds):
    seconds = int(seconds)

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)


def get_sort_key(item):
    return item["order"]


@bp.route(r"/json/<apiver>/status", methods=['GET', 'POST'])
@apiver_check
@login_required("LIST")
def status():
    try:
        status = toDict(PYLOAD_API.statusServer())
        status["captcha"] = PYLOAD_API.isCaptchaWaiting()
        return status
    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/links", methods=['GET', 'POST'])
@apiver_check
@login_required("LIST")
def links():
    try:
        links = [toDict(x) for x in PYLOAD_API.statusDownloads()]
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
        return flask.abort(500)


@bp.route(r"/json/<apiver>/packages")
@apiver_check
@login_required("LIST")
def packages():
    print("/json/packages")
    try:
        data = PYLOAD_API.getQueue()

        for package in data:
            package["links"] = []
            for file in PYLOAD_API.get_package_files(package["id"]):
                package["links"].append(PYLOAD_API.get_file_info(file))

        return data

    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/package/<id:int>")
@apiver_check
@login_required("LIST")
def package(id):
    try:
        data = toDict(PYLOAD_API.getPackageData(id))
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
        return flask.abort(500)


@bp.route(r"/json/<apiver>/package_order/<ids>")
@apiver_check
@login_required("ADD")
def package_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD_API.orderPackage(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/abort_link/<id:int>")
@apiver_check
@login_required("DELETE")
def abort_link(id):
    try:
        PYLOAD_API.stopDownloads([id])
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/link_order/<ids>")
@apiver_check
@login_required("ADD")
def link_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD_API.orderFile(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/add_package", methods=['GET', 'POST'])
@apiver_check
@login_required("ADD")
def add_package():
    name = flask.request.form.get("add_name", "New Package").strip()
    queue = int(flask.request.form["add_dest"])
    links = decode(flask.request.form["add_links"])
    links = links.split("\n")
    pw = flask.request.form.get("add_password", "").strip("\n\r")

    try:
        f = flask.request.files["add_file"]

        if not name or name == "New Package":
            name = f.name

        fpath = os.path.join(
            PYLOAD_API.getConfigValue("general", "download_folder"), "tmp_" + f.filename
        )
        f.save(fpath)
        links.insert(0, fpath)
        
    except Exception:
        pass

    name = name.decode("utf-8", "ignore")
    links = list(filter(None, map(str.strip, links)))
    pack = PYLOAD_API.addPackage(name, links, queue)
    if pw:
        pw = pw.decode("utf-8", "ignore")
        data = {"password": pw}
        PYLOAD_API.setPackageData(pack, data)


@bp.route(r"/json/<apiver>/move_package/<dest:int>/<id:int>")
@apiver_check
@login_required("MODIFY")
def move_package(dest, id):
    try:
        PYLOAD_API.movePackage(dest, id)
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/edit_package", methods=['POST'])
@apiver_check
@login_required("MODIFY")
def edit_package():
    try:
        id = int(flask.request.form.get("pack_id"))
        data = {
            "name": flask.request.form.get("pack_name").decode("utf-8", "ignore"),
            "folder": flask.request.form.get("pack_folder").decode("utf-8", "ignore"),
            "password": flask.request.form.get("pack_pws").decode("utf-8", "ignore"),
        }

        PYLOAD_API.setPackageData(id, data)
        return {"response": "success"}

    except Exception:
        return flask.abort(500)


@bp.route(r"/json/<apiver>/set_captcha", methods=['GET', 'POST'])
@apiver_check
@login_required("ADD")
def set_captcha():
    if flask.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        try:
            PYLOAD_API.setCaptchaResult(
                flask.request.form["cap_id"], flask.request.form["cap_result"]
            )
        except Exception:
            pass

    task = PYLOAD_API.getCaptchaTask()

    if task.tid >= 0:
        return {
            "captcha": True,
            "id": task.tid,
            "params": task.data,
            "result_type": task.resultType,
        }
    else:
        return {"captcha": False}


@bp.route(r"/json/<apiver>/load_config/<category>/<section>")
@apiver_check
@login_required("SETTINGS")
def load_config(category, section):
    conf = None
    if category == "general":
        conf = PYLOAD_API.getConfigDict()
    elif category == "plugin":
        conf = PYLOAD_API.getPluginConfigDict()

    for key, option in conf[section].items():
        if key in ("desc", "outline"):
            continue

        if ";" in option["type"]:
            option["list"] = option["type"].split(";")

        option["value"] = decode(option["value"])

    return render_to_response(
        "settings_item.html", {"skey": section, "section": conf[section]}
    )


@bp.route(r"/json/<apiver>/save_config/<category>", methods=['POST'])
@apiver_check
@login_required("SETTINGS")
def save_config(category):
    for key, value in flask.request.form.items():
        try:
            section, option = key.split("|")
        except Exception:
            continue

        if category == "general":
            category = "core"

        PYLOAD_API.setConfigValue(section, option, decode(value), category)


@bp.route(r"/json/<apiver>/add_account", methods=['POST'])
@apiver_check
@login_required("ACCOUNTS")
def add_account():
    login = flask.request.form["account_login"]
    password = flask.request.form["account_password"]
    type = flask.request.form["account_type"]

    PYLOAD_API.updateAccount(type, login, password)


@bp.route(r"/json/<apiver>/update_accounts", methods=['POST'])
@apiver_check
@login_required("ACCOUNTS")
def update_accounts():
    deleted = []  #: dont update deleted accs or they will be created again

    for name, value in flask.request.form.items():
        value = value.strip()
        if not value:
            continue

        tmp, user = name.split(";")
        plugin, action = tmp.split("|")

        if (plugin, user) in deleted:
            continue

        if action == "password":
            PYLOAD_API.updateAccount(plugin, user, value)
        elif action == "time" and "-" in value:
            PYLOAD_API.updateAccount(plugin, user, options={"time": [value]})
        elif action == "limitdl" and value.isdigit():
            PYLOAD_API.updateAccount(plugin, user, options={"limitDL": [value]})
        elif action == "delete":
            deleted.append((plugin, user))
            PYLOAD_API.removeAccount(plugin, user)


@bp.route(r"/json/<apiver>/change_password", methods=['POST'])
@apiver_check
def change_password():

    user = flask.request.form["user_login"]
    oldpw = flask.request.form["login_current_password"]
    newpw = flask.request.form["login_new_password"]

    if not PYLOAD_API.changePassword(user, oldpw, newpw):
        print("Wrong password")
        return flask.abort(500)
