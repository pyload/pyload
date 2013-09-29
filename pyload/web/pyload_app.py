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
import time
from os.path import join, exists

from bottle import route, static_file, response, request, redirect, template

from webinterface import PYLOAD, PROJECT_DIR, SETUP, APP_PATH, UNAVAILALBE

from utils import login_required, add_json_header, select_language

from pyload.utils import json_dumps

APP_ROOT = join(PROJECT_DIR, APP_PATH)

# Cache file names that are available gzipped
GZIPPED = {}


@route('/icons/<path:path>')
def serve_icon(path):
    # TODO
    return redirect('/images/icon.png')
    # return static_file(path, root=join("tmp", "icons"))


@route("/download/:fid")
@login_required('Download')
def download(fid, api):
    path, name = api.getFilePath(fid)
    return static_file(name, path, download=True)


@route("/i18n")
@route("/i18n/:lang")
def i18n(lang=None):
    add_json_header(response)

    if lang is None:
        pass
        # TODO use lang from PYLOAD.config or setup
    else:
        # TODO auto choose language
        lang = select_language(["en"])

    return json_dumps({})

@route('/')
def index():
    if UNAVAILALBE:
        return serve_static("unavailable.html")

    resp = serve_static('index.html')
    # set variable depending on setup mode
    setup = 'false' if SETUP is None else 'true'
    ws = PYLOAD.getWSAddress() if PYLOAD else False
    web = PYLOAD.getConfigValue('webinterface', 'port') if PYLOAD else False

    # Render variables into the html page
    if resp.status_code == 200:
        content = resp.body.read()
        resp.body = template(content, ws=ws, web=web, setup=setup)
        resp.content_length = len(resp.body)

    return resp

# Very last route that is registered, could match all uris
@route('/<path:path>')
def serve_static(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"

    # save if this resource is available as gz
    if path not in GZIPPED:
        GZIPPED[path] = exists(join(APP_ROOT, path + ".gz"))

    # gzipped and clients accepts it
    # TODO: index.html is not gzipped, because of template processing
    if GZIPPED[path] and "gzip" in request.get_header("Accept-Encoding", "") and path != "index.html":
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['Content-Encoding'] = 'gzip'
        path += ".gz"

    resp = static_file(path, root=APP_ROOT)
    # Also serve from .tmp folder in dev mode
    if resp.status_code == 404 and APP_PATH == "app":
        return static_file(path, root=join(PROJECT_DIR, '.tmp'))

    return resp