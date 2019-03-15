# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import os

import flask
from flask.json import jsonify

from pyload.core.utils import format_speed

from ..helpers import render_template, login_required


bp = flask.Blueprint("json", __name__, url_prefix="/json")


def format_time(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)


@bp.route("/status", methods=["GET", "POST"], endpoint="status")
# @apiver_check
@login_required("LIST")
def status():
    api = flask.current_app.config["PYLOAD_API"]
    data = api.statusServer()
    return jsonify(data)


@bp.route("/links", methods=["GET", "POST"], endpoint="links")
# @apiver_check
@login_required("LIST")
def links():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        links = api.statusDownloads()
        ids = []
        for link in links:
            ids.append(link["fid"])

            if link["status"] == 12:
                formatted_eta = link["format_eta"]
                formatted_speed = format_speed(link["speed"])
                link["info"] = f"{formatted_eta} @ {formatted_speed}"

            elif link["status"] == 5:
                link["percent"] = 0
                link["size"] = 0
                link["bleft"] = 0
                link["info"] = api._("waiting {}").format(link["format_wait"])
            else:
                link["info"] = ""

        return jsonify(links=links, ids=ids)

    except Exception as exc:
        flask.abort(500)

    return jsonify(False)


@bp.route("/packages", endpoint="packages")
# @apiver_check
@login_required("LIST")
def packages():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        data = api.getQueue()

        for package in data:
            package["links"] = []
            for file in api.get_package_files(package["id"]):
                package["links"].append(api.get_file_info(file))

        return jsonify(data)

    except Exception:
        flask.abort(500)

    return jsonify(False)


@bp.route("/package?=<int:id>", endpoint="package")
# @apiver_check
@login_required("LIST")
def package(id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        data = api.getPackageData(id)
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
        tmp.sort(key=lambda entry: entry["order"])
        data["links"] = tmp
        return jsonify(data)

    except Exception:
        flask.abort(500)

    return jsonify(False)


# NOTE: 'ids' is a string
@bp.route("/package_order?=<ids>", endpoint="package_order")
# @apiver_check
@login_required("ADD")
def package_order(ids):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        pid, pos = ids.split(",")
        api.orderPackage(int(pid), int(pos))
        return jsonify(response="success")
    except Exception:
        flask.abort(500)

    return jsonify(False)


@bp.route("/abort_link?=<int:id>", endpoint="abort_link")
# @apiver_check
@login_required("DELETE")
def abort_link(id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.stopDownloads([id])
        return jsonify(response="success")
    except Exception:
        flask.abort(500)

    return jsonify(False)


# NOTE: 'ids' is a string
@bp.route("/link_order?=<ids>", endpoint="link_order")
# @apiver_check
@login_required("ADD")
def link_order(ids):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        pid, pos = ids.split(",")
        api.orderFile(int(pid), int(pos))
        return jsonify(response="success")
    except Exception:
        flask.abort(500)

    return jsonify(False)


@bp.route("/add_package", methods=["POST"], endpoint="add_package")
# @apiver_check
@login_required("ADD")
def add_package():
    api = flask.current_app.config["PYLOAD_API"]

    name = flask.request.form.get("add_name", "New Package").strip()
    queue = int(flask.request.form["add_dest"])
    links = flask.request.form["add_links"].split("\n")
    pw = flask.request.form.get("add_password", "").strip("\n\r")

    try:
        f = flask.request.files["add_file"]

        if not name or name == "New Package":
            name = f.name

        fpath = os.path.join(
            api.getConfigValue("general", "storage_folder"), "tmp_" + f.filename
        )
        f.save(fpath)
        links.insert(0, fpath)

    except Exception:
        pass

    urls = [url for url in links if url.strip()]
    pack = api.addPackage(name, urls, queue)
    if pw:
        data = {"password": pw}
        api.setPackageData(pack, data)

    return jsonify(True)


@bp.route("/move_package?=<int:dest>,<int:id>", endpoint="move_package")
# @apiver_check
@login_required("MODIFY")
def move_package(dest, id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.movePackage(dest, id)
        return jsonify(response="success")
    except Exception:
        flask.abort(500)

    return jsonify(False)


@bp.route("/edit_package", methods=["POST"], endpoint="edit_package")
# @apiver_check
@login_required("MODIFY")
def edit_package():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        id = int(flask.request.form["pack_id"])
        data = {
            "name": flask.request.form["pack_name"],
            "folder": flask.request.form["pack_folder"],
            "password": flask.request.form["pack_pws"],
        }

        api.setPackageData(id, data)
        return jsonify(response="success")

    except Exception:
        flask.abort(500)

    return jsonify(False)


@bp.route("/set_captcha", methods=["GET", "POST"], endpoint="set_captcha")
# @apiver_check
@login_required("ADD")
def set_captcha():
    api = flask.current_app.config["PYLOAD_API"]

    if flask.request.method == "POST":
        tid = int(flask.request.form["cap_id"])
        result = flask.request.form["cap_result"]
        api.setCaptchaResult(tid, result)

    task = api.getCaptchaTask()
    if task.tid >= 0:
        data = {
            "captcha": True,
            "id": task.tid,
            "params": task.data,
            "result_type": task.resultType,
        }
    else:
        data = {"captcha": False}

    return jsonify(data)


@bp.route("/load_config?=<category>,<section>", endpoint="load_config")
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

    return render_template("settings_item.html", skey=section, section=conf[section])


@bp.route("/save_config?=<category>", methods=["POST"], endpoint="save_config")
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

        api.setConfigValue(section, option, value, category)

    return jsonify(True)


@bp.route("/add_account", methods=["POST"], endpoint="add_account")
# @apiver_check
@login_required("ACCOUNTS")
# @fresh_login_required
def add_account():
    api = flask.current_app.config["PYLOAD_API"]

    login = flask.request.form["account_login"]
    password = flask.request.form["account_password"]
    type = flask.request.form["account_type"]

    api.updateAccount(type, login, password)
    return jsonify(True)


@bp.route("/update_accounts", methods=["POST"], endpoint="update_accounts")
# @apiver_check
@login_required("ACCOUNTS")
# @fresh_login_required
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

    return jsonify(True)


@bp.route("/change_password", methods=["POST"], endpoint="change_password")
# @apiver_check
# @fresh_login_required
@login_required("ACCOUNTS")
def change_password():
    api = flask.current_app.config["PYLOAD_API"]

    user = flask.request.form["user_login"]
    oldpw = flask.request.form["login_current_password"]
    newpw = flask.request.form["login_new_password"]

    done = api.changePassword(user, oldpw, newpw)
    if not done:
        return "Wrong password", 500

    return jsonify(True)
