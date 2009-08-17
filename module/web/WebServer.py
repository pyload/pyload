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

import threading

import bottle
import time
from bottle import abort
from bottle import db
from bottle import debug
from bottle import request
from bottle import response
from bottle import redirect
from bottle import route
from bottle import run
from bottle import send_file
from bottle import template
from bottle import validate


core = None

PATH = "./module/web/"
TIME = time.strftime("%a, %d %b %Y 00:00:00 +0000", time.localtime()) #set time to current day

@route('/', method= 'POST')
def home():
    #print request.GET
    print request.POST

    return template('default', page='home', links=core.get_downloads())

@route('/')
def login():
    return template('default', page='login')

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

        bottle.TEMPLATE_PATH.append('./module/web/templates/%s.tpl')

    def run(self):
        self.core.logger.info("Starting Webinterface on port %s" % self.core.config['webinterface']['port'])
        run(host='localhost', port=int(self.core.config['webinterface']['port']), quiet=True)
