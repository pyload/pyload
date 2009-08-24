#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 RaNaN
#
#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 3 of the License,
#or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
###

import random
import threading
import time

import bottle
from bottle import abort
from bottle import redirect
from bottle import request
from bottle import response
from bottle import route
from bottle import run
from bottle import send_file
from bottle import template
from bottle import validate


core = None

PATH = "./module/web/"
TIME = time.strftime("%a, %d %b %Y 00:00:00 +0000", time.localtime()) #set time to current day
USERS = {}

@route('/login', method='POST')
def do_login():
    #print request.GET


    username = core.config['webinterface']['username']
    pw = core.config['webinterface']['password']

    if request.POST['u'] == username and request.POST['p'] == pw:
        
        id = int(random.getrandbits(16))
        ua = request.HEADER("HTTP_USER_AGENT")
        ip = request.HEADER("REMOTE_ADDR")

        auth = {}

        auth['ua'] = ua
        auth['ip'] = ip
        auth['user'] = username

        USERS[id] = auth

        response.COOKIES['user'] = username
        response.COOKIES['id'] = id

        return template('default', page='loggedin', user=username)
    else:
        return template('default', page='login')

@route('/login')
def login():

    if check_auth(request):
        redirect("/")

    return template('default', page='login')

@route('/logout')
def logout():
    try:
        del USERS[int(request.COOKIES.get('id'))]
    except:
        pass
    
    redirect("/login")

@route('/')
def home():

    if not check_auth(request):
        redirect("/login")

    username = request.COOKIES.get('user')

    dls = core.get_downloads()

    for dl in dls:
        dl['eta'] = str(core.format_time(dl['eta']))
        dl['wait_until'] = str(core.format_time(dl['wait_until'] - time.time()))

        
    return template('default', page='home', links=dls, user=username, status=core.server_status())

@route('/queue')
def queue():

    if not check_auth(request):
        redirect("/login")

    username = request.COOKIES.get('user')

    return template('default', page='queue', links=core.get_links(), user=username, status=core.server_status())

@route('/downloads')
def downloads():

    if not check_auth(request):
        redirect("/login")

    username = request.COOKIES.get('user')

    return template('default', page='downloads', links=core.get_downloads(), user=username, status=core.server_status())


@route('/logs')
def logs():

    if not check_auth(request):
        redirect("/login")

    username = request.COOKIES.get('user')

    return template('default', page='logs', links=core.get_downloads(), user=username, status=core.server_status())

@route('/json/links')
def get_links():
    response.header['Cache-Control'] = 'no-cache, must-revalidate'
    response.content_type = 'application/json'

    if not check_auth(request):
        abort(404, "No Access")

    json = '{ "downloads": ['

    downloads = core.get_downloads()

    for dl in downloads:
        json += '{'
        json += '"id": "%s", "name": "%s", "speed": "%s", "eta": "%s", "kbleft": "%s", "size": "%s", "percent": "%s", "wait": "%s", "status": "%s"'\
            % (str(dl['id']), str(dl['name']), str(dl['speed']), str(core.format_time(dl['eta'])), dl['kbleft'], dl['size'], dl['percent'], str(core.format_time(dl['wait_until'] - time.time())), dl['status'])

        json += "},"

    if json.endswith(","): json = json[:-1]

    json += "] }"

    return json
@route('/json/status')
def get_status():
    response.header['Cache-Control'] = 'no-cache, must-revalidate'
    response.content_type = 'application/json'

    if not check_auth(request):
        abort(404, "No Access")

    data = core.server_status()

    if data['pause']:
        status = "paused"
    else:
        status = "running"

    json = '{ "status": "%s", "speed": "%s", "queue": "%s" }' % (status, str(int(data['speed'])), str(data['queue']))

    return json

@route('/json/addlinks', method='POST')
def add_links():
    response.header['Cache-Control'] = 'no-cache, must-revalidate'
    response.content_type = 'application/json'

    if not check_auth(request):
        abort(404, "No Access")

    links = request.POST['links'].split('\n')

    core.add_links(links)
    
    return "{}"

@route('/json/pause')
def pause():
    response.header['Cache-Control'] = 'no-cache, must-revalidate'
    response.content_type = 'application/json'

    if not check_auth(request):
        abort(404, "No Access")

    core.thread_list.pause = True

    return "{}"

@route('/json/pause')
def pause():
    response.header['Cache-Control'] = 'no-cache, must-revalidate'
    response.content_type = 'application/json'

    if not check_auth(request):
        abort(404, "No Access")

    core.thread_liste.pause = False

    return "{}"


@route('/favicon.ico')
def favicon():
    redirect('/static/favicon.ico')

@route('static/:section/:filename')
def static_folder(section, filename):
    
    if request.HEADER("HTTP_IF_MODIFIED_SINCE") == TIME: abort(304, "Not Modified")

    response.header['Last-Modified'] = TIME
    send_file(filename, root=(PATH + 'static/' + section))

@route('/static/:filename')
def static_file(filename):

    if request.HEADER("HTTP_IF_MODIFIED_SINCE") == TIME: abort(304, "Not Modified")
    
    response.header['Last-Modified'] = TIME
    send_file(filename, root=(PATH + 'static/'))


def check_auth(req):

    try:
        user = req.COOKIES.get('user')
        id = int(req.COOKIES.get('id'))
        ua = req.HEADER("HTTP_USER_AGENT")
        ip = req.HEADER("REMOTE_ADDR")

        if USERS[id]['user'] == user and USERS[id]['ua'] == ua and USERS[id]['ip'] == ip:
            return True
    except:
        return False

    return False


class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)

        global core, TIME
        core = pycore
        self.core = pycore
        self.setDaemon(True)
        
        if pycore.config['general']['debug_mode']:
            bottle.debug(True)
            TIME = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())
        else:
            bottle.debug(False)

        #@TODO remove
        TIME = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())

        bottle.TEMPLATE_PATH.append('./module/web/templates/%s.tpl')

    def run(self):
        self.core.logger.info("Starting Webinterface on port %s" % self.core.config['webinterface']['port'])
        run(host='localhost', port=int(self.core.config['webinterface']['port']), quiet=True)
