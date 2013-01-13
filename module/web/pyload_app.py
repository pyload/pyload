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

from bottle import route, static_file, request, response, redirect, HTTPError, error
from jinja2 import TemplateNotFound

from webinterface import PYLOAD, PROJECT_DIR, SETUP, env

from utils import render_to_response, login_required, set_session, get_user_api, is_mobile


##########
# Helper
##########

# TODO: useful but needs a rewrite, too
def pre_processor():
    s = request.environ.get('beaker.session')
    api = get_user_api(s)
    user = None
    status = None

    if api is not None:
        user = api.user
        status = api.getServerStatus()

    return {"user": user,
            'server': status,
            'url': request.url }


def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])


@error(500)
def error500(error):
    print "An error occurred while processing the request."
    if error.traceback:
        print error.traceback

    return base(["An error occurred while processing the request.", error,
                 error.traceback.replace("\n", "<br>") if error.traceback else "No Traceback"])

# TODO: not working
# @route("/static/js/<path:re:.+\.js>")
def js_dynamic(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 2))
    response.headers['Cache-control'] = "public"
    response.headers['Content-Type'] = "text/javascript; charset=UTF-8"

    try:
        # static files are not rendered
        if "static" not in path:
            t = env.get_template("js/%s" % path)
            return t.render()
        else:
            return static_file(path, root=join(PROJECT_DIR, "static", "js"))
    except:
        return HTTPError(404, "Not Found")

@route('/static/<path:path>')
def server_static(path):
    response.headers['Expires'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT",
                                                time.gmtime(time.time() + 60 * 60 * 24 * 7))
    response.headers['Cache-control'] = "public"
    return static_file(path, root=join(PROJECT_DIR, "static"))

@route('/templates/<path:path>')
def serve_template(path):
    """ Serve backbone templates """
    args = path.split("/")
    args.insert(1, "backbone")
    try:
        return render_to_response("/".join(args))
    except TemplateNotFound, e:
        print e
        return HTTPError(404, "Not Found")

@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root=join(PROJECT_DIR, "static", "img"))


##########
# Views
##########


@route('/login', method="GET")
def login():
    # set mobilecookie to reduce is_mobile check-time
    response.set_cookie("mobile", str(is_mobile()))
    if not PYLOAD and SETUP:
        redirect("/setup")
    else:
        return render_to_response("login.html", proc=[pre_processor])

@route('/nopermission')
def nopermission():
    return base([_("You don't have permission to access this page.")])


@route("/login", method="POST")
def login_post():
    username = request.forms.get("username")
    password = request.forms.get("password")
    user = PYLOAD.checkAuth(username, password)
    if not user:
        return render_to_response("login.html", {"errors": True}, [pre_processor])
    set_session(request, user)
    return redirect("/")

@route("/toggle_mobile")
def toggle_mobile():
    response.set_cookie("mobile", str(not is_mobile()))
    return redirect("/")

@route("/logout")
def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return render_to_response("login.html", {"logout": True}, proc=[pre_processor])

@route("/")
@login_required()
def index(api):
    return render_to_response("dashboard.html", proc=[pre_processor])

@route("/settings")
@login_required()
def settings(api):
    return render_to_response("settings.html", proc=[pre_processor])

@route("/admin")
@login_required()
def admin(api):
    return render_to_response("admin.html", proc=[pre_processor])

