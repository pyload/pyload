# -*- coding: utf-8 -*-
#@author: RaNaN

from __future__ import absolute_import
from __future__ import unicode_literals
import time
from os.path import join, exists

from bottle import route, static_file, response, request, redirect, template

from .webinterface import PYLOAD, PROJECT_DIR, SETUP, APP_PATH, UNAVAILALBE, PREFIX

from .utils import login_required, add_json_header, select_language

from pyload.utils import json_dumps

APP_ROOT = join(PROJECT_DIR, APP_PATH)

# Cache file names that are available gzipped
GZIPPED = {}


@route('/icons/<path:path>')
def serve_icon(path):
    # TODO: send real file, no redirects
    return redirect(PREFIX if PREFIX else '/' + '../images/icon.png')
    # return static_file(path, root=join("tmp", "icons"))


@route("/download/:fid")
@login_required('Download')
def download(fid, api):
    # TODO: check owner ship
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
    # the browser should not set this, but remove in case to to avoid cached requests
    if 'HTTP_IF_MODIFIED_SINCE' in request.environ:
        del request.environ['HTTP_IF_MODIFIED_SINCE']

    if UNAVAILALBE:
        return serve_static("unavailable.html")

    resp = serve_static('index.html')
    # set variable depending on setup mode
    setup = 'false' if SETUP is None else 'true'
    ws = PYLOAD.getWSAddress() if PYLOAD else False
    external = PYLOAD.getConfigValue('webui', 'external') if PYLOAD else None
    web = None
    if PYLOAD:
        web = PYLOAD.getConfigValue('webui', 'port')
    elif SETUP:
        web = SETUP.config['webui']['port']

    # Render variables into the html page
    if resp.status_code == 200:
        content = resp.body.read()
        resp.body = template(content, ws=ws, web=web, setup=setup, external=external, prefix=PREFIX)
        resp.content_length = len(resp.body) + 1

    # these page should not be cached at all
    resp.headers.append("Cache-Control", "no-cache")
    # they are rendered and last modified would be wrong
    if "Last-Modified" in resp.headers:
        del resp.headers["Last-Modified"]

    return resp

# Very last route that is registered, could match all uris
@route('/<path:path>')
def serve_static(path):
    # save if this resource is available as gz
    if path not in GZIPPED:
        GZIPPED[path] = exists(join(APP_ROOT, path + ".gz"))

    # gzipped and clients accepts it
    # TODO: index.html is not gzipped, because of template processing
    gzipped = False
    if GZIPPED[path] and "gzip" in request.get_header("Accept-Encoding", "") and path != "index.html":
        gzipped = True
        path += ".gz"

    resp = static_file(path, root=APP_ROOT)

    # Also serve from .tmp folder in dev mode
    if resp.status_code == 404 and APP_PATH == "app":
        resp = static_file(path, root=join(PROJECT_DIR, '.tmp'))

    if path.endswith(".html") or path.endswith(".html.gz"):
        # tell the browser all html files must be revalidated
        resp.headers["Cache-Control"] = "must-revalidate"
    elif resp.status_code == 200:
        # expires after 7 days
        resp.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
        resp.headers['Cache-control'] = "public"

    if gzipped:
        resp.headers['Vary'] = 'Accept-Encoding'
        resp.headers['Content-Encoding'] = 'gzip'

    return resp
