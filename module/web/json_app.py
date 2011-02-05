#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from os.path import join
from traceback import print_exc
from shutil import copyfileobj

from bottle import route, request, HTTPError, validate

from webinterface import PYLOAD

from utils import login_required


def format_time(seconds):
    seconds = int(seconds)

    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)

def get_sort_key(item):
    return item["order"]


@route("/json/status")
@route("/json/status", method="POST")
@login_required('can_see_dl')
def status():
    try:
        status = PYLOAD.status_server()
        status['captcha'] = PYLOAD.is_captcha_waiting()
        return status
    except:
        return HTTPError()


@route("/json/links")
@route("/json/links", method="POST")
@login_required('can_see_dl')
def links():
    try:
        links = PYLOAD.status_downloads()
        ids = []
        for link in links:
            ids.append(link['id'])

            if link['status'] == 12:
                link['info'] = "%s @ %s kb/s" % (link['format_eta'], round(link['speed'], 2))
            elif link['status'] == 5:
                link['percent'] = 0
                link['size'] = 0
                link['kbleft'] = 0
                link['info'] = _("waiting %s") % link['format_wait']
            else:
                link['info'] = ""

        data = {'links': links, 'ids': ids}
        return data
    except Exception, e:
        return HTTPError()

@route("/json/queue")
@login_required('can_see_dl')
def queue():
    try:
        return PYLOAD.get_queue()

    except:
        return HTTPError()


@route("/json/pause")
@login_required('can_change_satus')
def pause():
    try:
        return PYLOAD.pause_server()

    except:
        return HTTPError()


@route("/json/unpause")
@login_required('can_change_status')
def unpause():
    try:
        return PYLOAD.unpause_server()

    except:
        return HTTPError()


@route("/json/cancel")
@login_required('can_change_status')
def cancel():
    try:
        return PYLOAD.stop_downloads()
    except:
        return HTTPError()

@route("/json/packages")
@login_required('can_see_dl')
def packages():
    try:
        data = PYLOAD.get_queue()

        for package in data:
            package['links'] = []
            for file in PYLOAD.get_package_files(package['id']):
                package['links'].append(PYLOAD.get_file_info(file))

        return data

    except:
        return HTTPError()

@route("/json/package/:id")
@validate(id=int)
@login_required('pyload.can_see_dl')
def package(id):
    try:
        data = PYLOAD.get_package_data(id)

        for pyfile in data["links"].itervalues():
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
            elif pyfile["status"] in (11, 13):
                pyfile["icon"] = "status_proc.png"
            else:
                pyfile["icon"] = "status_downloading.png"

        tmp = data["links"].values()
        tmp.sort(key=get_sort_key)
        data["links"] = tmp
        return data

    except:
        return HTTPError()

@route("/json/package_order/:ids")
@login_required('can_add')
def package_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.order_package(int(pid), int(pos))
        return "success"
    except:
        return HTTPError()

@route("/json/link/:id")
@validate(id=int)
@login_required('can_see_dl')
def link(id):
    try:
        data = PYLOAD.get_file_info(id)
        return data
    except:
        return HTTPError()

@route("/json/remove_link/:id")
@validate(id=int)
@login_required('can_delete')
def remove_link(id):
    try:
        PYLOAD.del_links([id])
        return "success"
    except Exception, e:
        return HTTPError()

@route("/json/restart_link/:id")
@validate(id=int)
@login_required('can_add')
def restart_link(id):
    try:
        PYLOAD.restart_file(id)
        return "success"
    except Exception:
        return HTTPError()

@route("/json/abort_link/:id")
@validate(id=int)
@login_required('can_delete')
def abort_link(id):
    try:
        PYLOAD.stop_download("link", id)
        return "success"
    except:
        return HTTPError()

@route("/json/link_order/:ids")
@login_required('can_add')
def link_order(ids):
    try:
        pid, pos = ids.split("|")
        PYLOAD.order_file(int(pid), int(pos))
        return "success"
    except:
        return HTTPError()

@route("/json/add_package")
@route("/json/add_package", method="POST")
@login_required('can_add')
def add_package():
    name = request.forms['add_name']
    queue = int(request.forms['add_dest'])
    links = request.forms['add_links'].split("\n")
    pw = request.forms.get("add_password", "").strip("\n\r")

    try:
        f = request.files['add_file']

        if name is None or name == "":
            name = f.name

        fpath = join(PYLOAD.get_conf_val("general", "download_folder"), "tmp_" + f.filename)
        destination = open(fpath, 'wb')
        copyfileobj(f.file, destination)
        destination.close()
        links.insert(0, fpath)
    except:
        pass

    if name is None or name == "":
        return HTTPError()

    links = map(lambda x: x.strip(), links)
    links = filter(lambda x: x != "", links)

    pack = PYLOAD.add_package(name, links, queue)
    if pw:
        data = {"password": pw}
        PYLOAD.set_package_data(pack, data)

    return "success"


@route("/json/remove_package/:id")
@validate(id=int)
@login_required('can_delete')
def remove_package(id):
    try:
        PYLOAD.del_packages([id])
        return "success"
    except Exception, e:
        return HTTPError()

@route("/json/restart_package/:id")
@validate(id=int)
@login_required('can_add')
def restart_package(id):
    try:
        PYLOAD.restart_package(id)
        return "success"
    except Exception:
        print_exc()
        return HTTPError()

@route("/json/move_package/:dest/:id")
@validate(dest=int, id=int)
@login_required('can_add')
def move_package(dest, id):
    try:
        PYLOAD.move_package(dest, id)
        return "success"
    except:
        return HTTPError()

@route("/json/edit_package", method="POST")
@login_required('can_add')
def edit_package():
    try:
        id = int(request.forms.get("pack_id"))
        data = {"name": request.forms.get("pack_name"),
                "folder": request.forms.get("pack_folder"),
                "priority": request.forms.get("pack_prio"),
                "password": request.forms.get("pack_pws")}

        PYLOAD.set_package_data(id, data)
        return "success"

    except:
        return HTTPError()

@route("/json/set_captcha")
@route("/json/set_captcha", method="POST")
@login_required('can_add')
def set_captcha():
    if request.environ.get('REQUEST_METHOD', "GET") == "POST":
        try:
            PYLOAD.set_captcha_result(request.forms["cap_id"], request.forms["cap_text"])
        except:
            pass

    id, binary, typ = PYLOAD.get_captcha_task()

    if id:
        binary = base64.standard_b64encode(str(binary))
        src = "data:image/%s;base64,%s" % (typ, binary)

        return {'captcha': True, 'src': src, 'id': id}
    else:
        return {'captcha': False}


@route("/json/delete_finished")
@login_required('pyload.can_delete')
def delete_finished():
    return {"del": PYLOAD.delete_finished()}

@route("/json/restart_failed")
@login_required('pyload.can_delete')
def restart_failed():
    return PYLOAD.restart_failed()