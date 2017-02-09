# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import, unicode_literals

import time
from os.path import exists, join

from bottle import redirect, request, response, route, static_file, template

from pyload.utils import json_dumps
from pyload.webui.interface import APP_DIR, PREFIX, PYLOAD, SETUP, UNAVAILALBE
from pyload.webui.utils import add_json_header, login_required, select_language

# Cache file names that are available gzipped
GZIPPED = {}


@route('/icons/<path:path>')
def serve_icon(path):
    # TODO: send real file, no redirects
    return redirect(PREFIX if PREFIX else '../images/icon.png')
    # return static_file(path, root=join("tmp", "icons"))


@route("/download/:fid")
@login_required('Download')
def download(fid, api):
    # TODO: check owner ship
    path, name = api.get_file_path(fid)
    return static_file(name, path, download=True)


@route("/i18n")
@route("/i18n/:lang")
def i18n(lang=None):
    add_json_header(response)

    if lang is None:
        pass
        # TODO: use lang from PYLOAD.config or setup
    else:
        # TODO: auto choose language
        lang = select_language(("en",))

    return json_dumps({})


@route('/')
def index():
    # the browser should not set this, but remove in case to to avoid cached
    # requests
    if 'HTTP_IF_MODIFIED_SINCE' in request.environ:
        del request.environ['HTTP_IF_MODIFIED_SINCE']

    if UNAVAILALBE:
        return serve_static("unavailable.html")

    resp = serve_static('index.html')
    # set variable depending on setup mode
    setup = 'false' if SETUP is None else 'true'
    ws = PYLOAD.get_ws_address() if PYLOAD else False
    external = PYLOAD.get_config_value('webui', 'external') if PYLOAD else None
    web = None
    if PYLOAD:
        web = PYLOAD.get_config_value('webui', 'port')
    elif SETUP:
        web = SETUP.config.get('webui', 'port')

    # Render variables into the html page
    if resp.status_code == 200:
        content = resp.body.read()
        resp.body = template(content, ws=ws, web=web,
                             setup=setup, external=external, prefix=PREFIX)
        resp.content_length = len(resp.body) + 1

    # these page should not be cached at all
    resp.headers.append("Cache-Control", "no-cache")
    # they are rendered and last modified would be wrong
    if "Last-Modified" in resp.headers:
        del resp.headers['Last-Modified']

    return resp

# Very last route that is registered, could match all uris


@route('/<path:path>')
def serve_static(path):
    # save if this resource is available as gz
    if path not in GZIPPED:
        GZIPPED[path] = exists(join(APP_DIR, path + ".gz"))

    # gzipped and clients accepts it
    # TODO: index.html is not gzipped, because of template processing
    gzipped = False
    if GZIPPED[path] and "gzip" in request.get_header("Accept-Encoding", "") and path != "index.html":
        gzipped = True
        path += ".gz"

    resp = static_file(path, root=APP_DIR)

    if path.endswith(".html") or path.endswith(".html.gz"):
        # tell the browser all html files must be revalidated
        resp.headers['Cache-Control'] = "must-revalidate"
    elif resp.status_code == 200:
        # expires after 7 days
        resp.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
        resp.headers['Cache-control'] = "public"

    if gzipped:
        resp.headers['Vary'] = 'Accept-Encoding'
        resp.headers['Content-Encoding'] = 'gzip'

    return resp
