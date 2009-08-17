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


debug(True)
core = None

PATH = "./module/web/"

@route('/')
def hello_world():
    return template('default', string=str(core.get_downloads()))

@route('/favicon.ico')
def favicon():
    send_file('pyload.ico', PATH + 'static/')

@route('static/:section/:filename')
def static_folder(section, filename):
    send_file(filename, root=(PATH + 'static/' + section))

@route('/static/:filename')
def static_file(filename):
    send_file(filename, root=(PATH + 'static/'))

class WebServer(threading.Thread):
    def __init__(self, pycore):
        threading.Thread.__init__(self)

        global core
        core = pycore
        self.core = pycore
        self.setDaemon(True)
        
        bottle.TEMPLATE_PATH.append('./module/web/templates/%s.tpl')

    def run(self):
        run(host='localhost', port=8080)