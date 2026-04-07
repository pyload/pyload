import os
import sys
from functools import wraps

import flask
from flask.json import jsonify
from werkzeug.utils import secure_filename

from pyload.core.api import Role
from pyload.core.utils import format, fs

from ..helpers import get_permission, login_required, permlist, render_template, set_permission

bp = flask.Blueprint("json", __name__)


def expect_json(f):
    """
    Decorator: parses JSON and passes it as named arguments,
    enforces application/json content type
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not flask.request.is_json:
            return jsonify({
                "success": False,
                "error": "Request must be JSON"
            }), 415

        params = flask.request.get_json()
        if params is None:
            return jsonify({
                "success": False,
                "error": "Invalid or empty JSON"
            }), 400

        try:
            return f(**params)
        except TypeError:
            if sys.exc_info()[2].tb_next is None:
                return jsonify({
                    "success": False,
                    "error": "Invalid Parameters"
                }), 400
            else:
                raise

    return wrapper


@bp.route("/json/status", methods=["GET", "POST"], endpoint="status")
# @apiver_check
@login_required("LIST")
def status():
    api = flask.current_app.config["PYLOAD_API"]
    data = api.status_server()
    return jsonify(data)


@bp.route("/json/links", methods=["GET", "POST"], endpoint="links")
# @apiver_check
@login_required("LIST")
def links():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        links = api.status_downloads()
        ids = []
        for link in links:
            ids.append(link.fid)

            if link.status == 12:  #: downloading
                formatted_eta = link.format_eta
                formatted_speed = format.speed(link.speed)
                link.info = f"{formatted_eta} @ {formatted_speed}"

            elif link.status == 5:  #: waiting
                link.percent = 0
                link.size = 0
                link.bleft = 0
                link.info = api._("waiting {}").format(link.format_wait)
            else:
                link.info = ""

        return jsonify(links=links, ids=ids)

    except Exception as exc:
        return jsonify(False), 500


@bp.route("/json/package", methods=["GET"], endpoint="package")
# @apiver_check
@login_required("LIST")
def package():
    api = flask.current_app.config["PYLOAD_API"]
    try:
        id = int(flask.request.args.get('id'))
        data = api.get_package_data(id)

        tmp = data.links
        tmp.sort(key=lambda entry: entry.order)
        data.links = tmp
        return jsonify(data)

    except Exception:
        return jsonify(False), 500


@bp.route("/json/package_order", methods=["POST"], endpoint="package_order")
# @apiver_check
@login_required("MODIFY")
@expect_json
def package_order(pack_id, pos):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.order_package(int(pack_id), int(pos))
        return jsonify(response="success")

    except Exception:
        return jsonify(False), 500


@bp.route("/json/abort_link", methods=["POST"], endpoint="abort_link")
# @apiver_check
@login_required("MODIFY")
@expect_json
def abort_link(link_id):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.stop_downloads([link_id])
        return jsonify(response="success")

    except Exception:
        return jsonify(False), 500


@bp.route("/json/link_order", methods=["POST"], endpoint="link_order")
# @apiver_check
@login_required("MODIFY")
@expect_json
def link_order(file_id, pos):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.order_file(int(file_id), int(pos))
        return jsonify(response="success")

    except Exception:
        return jsonify(False), 500


@bp.route("/json/add_package", methods=["POST"], endpoint="add_package")
# @apiver_check
@login_required("ADD")
def add_package():
    api = flask.current_app.config["PYLOAD_API"]

    package_name = flask.request.form.get("add_name", "New Package").strip()
    queue = int(flask.request.form["add_dest"])
    links = [l.strip() for l in flask.request.form["add_links"].splitlines()]
    pw = flask.request.form.get("add_password", "").strip("\n\r")

    try:
        file = flask.request.files["add_file"]

        if file.filename:
            if not package_name or package_name == "New Package":
                package_name = file.filename

            safe_filename = secure_filename(file.filename)
            upload_path = os.path.join(api.get_cachedir(), "upload")
            os.makedirs(upload_path, exist_ok=True)
            file_path = fs.safejoin(upload_path, safe_filename)
            file.save(file_path)
            links.insert(0, file_path)

    except Exception:
        pass

    urls = [url for url in links if url.strip()]
    pack = api.add_package(package_name, urls, queue)
    if pw:
        data = {"password": pw}
        api.set_package_data(pack, data)

    return jsonify(True)


@bp.route("/json/move_package", methods=["POST"], endpoint="move_package")
# @apiver_check
@login_required("MODIFY")
@expect_json
def move_package(pack_id, dest):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        api.move_package(dest, pack_id)
        return jsonify(response="success")

    except Exception:
        return jsonify(False), 500


@bp.route("/json/edit_package", methods=["POST"], endpoint="edit_package")
# @apiver_check
@login_required("MODIFY")
@expect_json
def edit_package(pack_id, pack_name, pack_folder, pack_pwd):
    api = flask.current_app.config["PYLOAD_API"]
    try:
        pack_folder = secure_filename(pack_folder)
        data = {
            "name": pack_name,
            "_folder": pack_folder,
            "password": pack_pwd,
        }

        api.set_package_data(int(pack_id), data)
        return jsonify(response="success")

    except Exception:
        return jsonify(False), 500


@bp.route("/json/set_captcha", methods=["GET", "POST"], endpoint="set_captcha")
# @apiver_check
@login_required("STATUS")
def set_captcha():
    api = flask.current_app.config["PYLOAD_API"]

    if flask.request.method == "POST":
        tid = int(flask.request.form["cap_id"])
        result = flask.request.form["cap_result"]
        api.set_captcha_result(tid, result)

    task = api.get_captcha_task()
    if task.tid >= 0:
        data = {
            "captcha": True,
            "id": task.tid,
            "params": task.data,
            "result_type": task.result_type,
        }
    else:
        data = {"captcha": False}

    return jsonify(data)


@bp.route("/json/load_config", methods=["GET"], endpoint="load_config")
# @apiver_check
@login_required("SETTINGS")
def load_config():
    category = flask.request.args.get('category')
    section = flask.request.args.get('section')
    if category not in ("core", "plugin") or not section:
        return jsonify(False), 500

    conf = None
    api = flask.current_app.config["PYLOAD_API"]
    if category == "core":
        conf = api.get_config_dict()
    elif category == "plugin":
        conf = api.get_plugin_config_dict()

    for key, option in conf[section].items():
        if key in ("desc", "outline"):
            continue

        if ";" in option["type"]:
            option["list"] = option["type"].split(";")

    return render_template("settings_item.html", skey=section, section=conf[section])


@bp.route("/json/save_config", methods=["POST"], endpoint="save_config")
# @apiver_check
@login_required("SETTINGS")
@expect_json
def save_config(category, config):
    api = flask.current_app.config["PYLOAD_API"]
    if category not in ("core", "plugin"):
        return jsonify(False), 500

    for key, value in config.items():
        try:
            section, option = key.split("|")
        except ValueError:
            continue

        api.set_config_value(section, option, value, category)

    return jsonify(True)


@bp.route("/json/add_account", methods=["POST"], endpoint="add_account")
# @apiver_check
@login_required("ACCOUNTS")
@expect_json
# @fresh_login_required
def add_account(account_login, account_password, account_type):
    api = flask.current_app.config["PYLOAD_API"]
    if account_login:
        api.update_account(account_type, account_login, account_password)
        return jsonify(True)

    else:
        return jsonify(False)


@bp.route("/json/update_accounts", methods=["POST"], endpoint="update_accounts")
# @apiver_check
@login_required("ACCOUNTS")
# @fresh_login_required
def update_accounts():
    deleted = []  #: don't update deleted accounts, or they will be created again
    updated = {}
    api = flask.current_app.config["PYLOAD_API"]

    for name, value in flask.request.form.items():
        value = value.strip()
        if not value:
            continue

        tmp, user = name.split(";")
        plugin, action = tmp.split("|")

        if action == "delete":
            deleted.append((plugin,user, ))
            api.remove_account(plugin, user)

        elif action == "password":
            password, options = updated.get((plugin, user,), (None, {}))
            password = value
            updated[(plugin, user,)] = (password, options)
        elif action == "time" and "-" in value:
            password, options = updated.get((plugin, user,), (None, {}))
            options["time"] = [value]
            updated[(plugin, user,)] = (password, options)
        elif action == "limitdl" and value.isdigit():
            password, options = updated.get((plugin, user,), (None, {}))
            options["limit_dl"] = [value]
            updated[(plugin, user,)] = (password, options)

    for tmp, options in updated.items():
        plugin, user = tmp
        if (plugin, user,) in deleted:
            continue
        password, options = options
        api.update_account(plugin, user, password, options=options)

    return jsonify(True)


@bp.route("/json/change_password", methods=["POST"], endpoint="change_password")
# @apiver_check
# @fresh_login_required
@login_required("ADMIN")
@expect_json
def change_password(user_login, user_curpw, user_newpw):
    api = flask.current_app.config["PYLOAD_API"]
    done = api.change_password(user_login, user_curpw, user_newpw)
    if not done:
        return jsonify(False), 403  #: Wrong password

    return jsonify(True)

@bp.route("/json/add_user", methods=["POST"], endpoint="add_user")
# @apiver_check
@login_required("ADMIN")
# @fresh_login_required
def add_user():
    api = flask.current_app.config["PYLOAD_API"]

    user = flask.request.form["new_user"]
    password = flask.request.form["new_password"]
    role = Role.ADMIN if flask.request.form.get("new_role") == "on" else Role.USER
    perms = {}
    for perm in permlist():
        perms[perm] = False
    for perm in flask.request.form.getlist("new_perms"):
        perms[perm] = True

    perms = set_permission(perms)

    done = api.add_user(user, password, role, perms)
    if not done:
        return jsonify(False), 500  #: Duplicate user

    return jsonify(True)

@bp.route("/json/update_users", methods=["POST"], endpoint="update_users")
# @apiver_check
# @fresh_login_required
@login_required("ADMIN")
@expect_json
def update_users(update_data):
    api = flask.current_app.config["PYLOAD_API"]

    all_users = api.get_all_userdata()

    users = {}

    # NOTE: messy code...
    for userdata in all_users.values():
        name = userdata.name
        users[name] = {"perms": get_permission(userdata.permission)}
        users[name]["perms"]["admin"] = userdata.role == 0
        users[name]["role"] = userdata.role

    s = flask.session
    for name in list(users):
        data = users[name]
        if update_data.get(f"{name}|delete"):
            if name != s["name"]:
                api.remove_user(name)
                del users[name]
            continue
        if update_data.get(f"{name}|admin"):
            data["role"] = 0
            data["perms"]["admin"] = True
        elif name != s["name"]:
            data["role"] = 1
            data["perms"]["admin"] = False

        # set all perms to false
        for perm in permlist():
            data["perms"][perm] = False

        for perm in update_data.get(f"{name}|perms", []):
            data["perms"][perm] = True

        data["permission"] = set_permission(data["perms"])

        api.set_user_permission(name, data["permission"], data["role"])

    return jsonify(True)

@bp.route("/json/get_apikeys", methods=["POST"], endpoint="get_apikeys")
@login_required("ADMIN")
@expect_json
def get_apikeys(*, user=None):
    api = flask.current_app.config["PYLOAD_API"]
    user = user or flask.session["name"]
    return jsonify(api.get_apikeys(user))

@bp.route("/json/generate_apikey", methods=["POST"], endpoint="generate_apikey")
@login_required("ADMIN")
@expect_json
def generate_apikey(*, user, password, name, expires):
    api = flask.current_app.config["PYLOAD_API"]
    return jsonify(api.generate_apikey(user, password, name, expires))

@bp.route("/json/delete_apikey", methods=["POST"], endpoint="delete_apikey")
@login_required("ADMIN")
@expect_json
def delete_apikey(*, user, key):
    api = flask.current_app.config["PYLOAD_API"]
    return jsonify(api.delete_apikey(user, key))
