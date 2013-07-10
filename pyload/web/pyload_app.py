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
from os.path import join

from bottle import route, static_file, response, redirect, template

from webinterface import PYLOAD, PROJECT_DIR, SETUP, APP_PATH, UNAVAILALBE

from utils import login_required


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


@route('/')
def index():
    if UNAVAILALBE:
        return server_static("unavailable.html")

    if SETUP:
        # TODO show different page
        pass

    f = server_static('index.html')
    content = f.body.read()
    f.body = template(content, ws=PYLOAD.getWSAddress(), web=PYLOAD.getConfigValue('webinterface', 'port'))

    return f

# Very last route that is registered, could match all uris
@route('/<path:path>')
def server_static(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"
    resp = static_file(path, root=join(PROJECT_DIR, APP_PATH))
    # Also serve from .tmp folder in dev mode
    if resp.status_code == 404 and APP_PATH == "app":
        return static_file(path, root=join(PROJECT_DIR, '.tmp'))

    return resp