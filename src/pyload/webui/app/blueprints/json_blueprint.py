# -*- coding: utf-8 -*-

import os
from builtins import _

import flask

from pyload.utils.utils import decode, formatSize
from pyload.webui.app.utils import apiver_check, login_required, render_template, toDict

bp = flask.Blueprint("json", __name__, url_prefix="/json")


def format_time(seconds):
    seconds = int(seconds)

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)


def get_sort_key(item):
    return item["order"]


@bp.route(r"/status", methods=["GET", "POST"], endpoint="status")
# @apiver_check
@login_required("LIST")
def status():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        status = toDict(api.statusServer())
        status["captcha"] = api.isCaptchaWaiting()
        return status
    except Exception:
        return flask.abort(500)


@bp.route(r"/links", methods=["GET", "POST"], endpoint="links")
# @apiver_check
@login_required("LIST")
def links():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        links = [toDict(x) for x in api.statusDownloads()]
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


@bp.route(r"/packages", endpoint="packages")
# @apiver_check
@login_required("LIST")
def packages():
    print("/json/packages")
    api = flask.current_app.config["PYLOAD_API"]
    try:
        data = api.getQueue()

        for package in data:
            package["links"] = []
            for file in api.get_package_files(package["id"]):
                package["links"].append(api.get_file_info(file))

        return data

    except Exception:
        return flask.abort(500)


@bp.route(r"/package/<int:id>", endpoint="package")
# @apiver_check
@login_required("LIST")
def package(id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        data = toDict(api.getPackageData(id))
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


@bp.route(r"/package_order/<ids>", endpoint="package_order")
# @apiver_check
@login_required("ADD")
def package_order(ids):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        pid, pos = ids.split("|")
        api.orderPackage(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/abort_link/<int:id>", endpoint="abort_link")
# @apiver_check
@login_required("DELETE")
def abort_link(id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.stopDownloads([id])
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/link_order/<ids>", endpoint="link_order")
# @apiver_check
@login_required("ADD")
def link_order(ids):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        pid, pos = ids.split("|")
        api.orderFile(int(pid), int(pos))
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/add_package", methods=["GET", "POST"], endpoint="add_package")
# @apiver_check
@login_required("ADD")
def add_package():
    name = flask.request.form.get("add_name", "New Package").strip()
    queue = int(flask.request.form["add_dest"])
    links = decode(flask.request.form["add_links"])
    links = links.split("\n")
    pw = flask.request.form.get("add_password", "").strip("\n\r")
    api = flask.current_app.config["PYLOAD_API"]

    try:
        f = flask.request.files["add_file"]

        if not name or name == "New Package":
            name = f.name

        fpath = os.path.join(
            api.getConfigValue("general", "download_folder"), "tmp_" + f.filename
        )
        f.save(fpath)
        links.insert(0, fpath)

    except Exception:
        pass

    name = name.decode("utf-8", "ignore")
    links = list(filter(None, map(str.strip, links)))
    pack = api.addPackage(name, links, queue)
    if pw:
        pw = pw.decode("utf-8", "ignore")
        data = {"password": pw}
        api.setPackageData(pack, data)


@bp.route(r"/move_package/<int:dest>/<int:id>", endpoint="move_package")
# @apiver_check
@login_required("MODIFY")
def move_package(dest, id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.movePackage(dest, id)
        return {"response": "success"}
    except Exception:
        return flask.abort(500)


@bp.route(r"/edit_package", methods=["POST"], endpoint="edit_package")
# @apiver_check
@login_required("MODIFY")
def edit_package():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        id = int(flask.request.form.get("pack_id"))
        data = {
            "name": flask.request.form.get("pack_name").decode("utf-8", "ignore"),
            "folder": flask.request.form.get("pack_folder").decode("utf-8", "ignore"),
            "password": flask.request.form.get("pack_pws").decode("utf-8", "ignore"),
        }

        api.setPackageData(id, data)
        return {"response": "success"}

    except Exception:
        return flask.abort(500)


@bp.route(r"/set_captcha", methods=["GET", "POST"], endpoint="set_captcha")
# @apiver_check
@login_required("ADD")
def set_captcha():
    api = flask.current_app.config["PYLOAD_API"]
    if flask.request.environ.get("REQUEST_METHOD", "GET") == "POST":
        try:
            api.setCaptchaResult(
                flask.request.form["cap_id"], flask.request.form["cap_result"]
            )
        except Exception:
            pass

    task = api.getCaptchaTask()

    if task.tid >= 0:
        return {
            "captcha": True,
            "id": task.tid,
            "params": task.data,
            "result_type": task.resultType,
        }
    else:
        return {"captcha": False}


@bp.route(r"/load_config/<category>/<section>", endpoint="load_config")
# @apiver_check
@login_required("SETTINGS")
def load_config(category, section):
    conf = None
    api = flask.current_app.config["PYLOAD_API"]
    if category == "general":
        conf = api.getConfigDict()
    elif category == "plugin":
        conf = api.getPluginConfigDict()

    for key, option in conf[section].items():
        if key in ("desc", "outline"):
            continue

        if ";" in option["type"]:
            option["list"] = option["type"].split(";")

        option["value"] = decode(option["value"])

    return render_template(
        "settings_item.html", {"skey": section, "section": conf[section]}
    )


@bp.route(r"/save_config/<category>", methods=["POST"], endpoint="save_config")
# @apiver_check
@login_required("SETTINGS")
def save_config(category):
    api = flask.current_app.config["PYLOAD_API"]
    for key, value in flask.request.form.items():
        try:
            section, option = key.split("|")
        except Exception:
            continue

        if category == "general":
            category = "core"

        api.setConfigValue(section, option, decode(value), category)


@bp.route(r"/add_account", methods=["POST"], endpoint="add_account")
# @apiver_check
@login_required("ACCOUNTS")
def add_account():
    api = flask.current_app.config["PYLOAD_API"]
    login = flask.request.form["account_login"]
    password = flask.request.form["account_password"]
    type = flask.request.form["account_type"]

    api.updateAccount(type, login, password)


@bp.route(r"/update_accounts", methods=["POST"], endpoint="update_accounts")
# @apiver_check
@login_required("ACCOUNTS")
def update_accounts():
    deleted = []  #: dont update deleted accs or they will be created again
    api = flask.current_app.config["PYLOAD_API"]

    for name, value in flask.request.form.items():
        value = value.strip()
        if not value:
            continue

        tmp, user = name.split(";")
        plugin, action = tmp.split("|")

        if (plugin, user) in deleted:
            continue

        if action == "password":
            api.updateAccount(plugin, user, value)
        elif action == "time" and "-" in value:
            api.updateAccount(plugin, user, options={"time": [value]})
        elif action == "limitdl" and value.isdigit():
            api.updateAccount(plugin, user, options={"limitDL": [value]})
        elif action == "delete":
            deleted.append((plugin, user))
            api.removeAccount(plugin, user)


@bp.route(r"/change_password", methods=["POST"])
# @apiver_check
def change_password():
    api = flask.current_app.config["PYLOAD_API"]
    user = flask.request.form["user_login"]
    oldpw = flask.request.form["login_current_password"]
    newpw = flask.request.form["login_new_password"]

    if not api.changePassword(user, oldpw, newpw):
        print("Wrong password")
        return flask.abort(500)
