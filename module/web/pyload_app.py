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

from webinterface import PYLOAD, PROJECT_DIR, SETUP, env

from utils import render_to_response, parse_permissions, parse_userdata, set_session

from module.Api import Output

##########
# Helper
##########


# TODO: useful but needs a rewrite, too
def pre_processor():
    s = request.environ.get('beaker.session')
    user = parse_userdata(s)
    perms = parse_permissions(s)
    status = {}
    captcha = False
    update = False
    plugins = False
    if user["is_authenticated"]:
        status = PYLOAD.statusServer()
        info = PYLOAD.getInfoByPlugin("UpdateManager")
        captcha = PYLOAD.isInteractionWaiting(Output.Captcha)

        # check if update check is available
        if info:
            if info["pyload"] == "True": update = True
            if info["plugins"] == "True": plugins = True


    return {"user": user,
            'status': status,
            'captcha': captcha,
            'perms': perms,
            'url': request.url,
            'update': update,
            'plugins': plugins}



def base(messages):
    return render_to_response('base.html', {'messages': messages}, [pre_processor])


@error(500)
def error500(error):
    print "An error occured while processing the request."
    if error.traceback:
        print error.traceback

    return base(["An error occured while processing the request.", error,
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

@route('/favicon.ico')
def favicon():
    return static_file("favicon.ico", root=join(PROJECT_DIR, "static", "img"))


##########
# Views
##########


@route('/login', method="GET")
def login():
    if not PYLOAD and SETUP:
        redirect("/setup")
    else:
        return render_to_response("login.html", proc=[pre_processor])


@route('/nopermission')
def nopermission():
    return base([_("You don't have permission to access this page.")])


@route("/login", method="POST")
def login_post():
    user = request.forms.get("username")
    password = request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return render_to_response("login.html", {"errors": True}, [pre_processor])

    set_session(request, info)
    return redirect("/")


@route("/logout")
def logout():
    s = request.environ.get('beaker.session')
    s.delete()
    return render_to_response("logout.html", proc=[pre_processor])

@route("/")
def index():
    return base(["It works!"])

