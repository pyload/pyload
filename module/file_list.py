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

LIST_VERSION = 3

from threading import RLock
from download_thread import Status
import cPickle
import re
from module.remote.RequestObject import RequestObject

class File_List(object):
    def __init__(self, core):
        self.core = core
        self.files = []
        self.data = {'version': LIST_VERSION, 'order': []}
        self.lock = RLock()
        self.load()

    def new_pyfile(self, url, folder):
        url  = url.replace("\n", "")
        pyfile = PyLoadFile(self.core, url)
        pyfile.download_folder = self.core.config['general']['download_folder']
        pyfile.id = self.get_id()
        pyfile.folder = folder

        return pyfile

    def append(self, url, folder=""):
        if not url:
            return False
        #@TODO: filter non existence and invalid links
        #re.compile("https?://[-a-z0-9\.]{4,}(?::\d+)?/[^#?]+(?:#\S+)?",re.IGNORECASE)
        new_file = self.new_pyfile(url, folder)
        self.files.append(new_file)
        self.data[new_file.id] = Data(url, folder)
        self.data['order'].append(int(new_file.id))

    def extend(self, urls):
        for url in urls:
            self.append(url)

    def remove(self, pyfile):
        if not self.core.config['general']['debug_mode']:
            if pyfile in self.files:
                self.files.remove(pyfile)

            self.data['order'].remove(pyfile.id)
            del self.data[pyfile.id]

    def remove_id(self, pyid):
        #also abort download
        pyid = int(pyid)
        found = False
        for pyfile in self.files:
            if pyfile.id == pyid:
                self.files.remove(pyfile)
                found = True
                break

        if not found:
            for pyfile in self.core.thread_list.py_downloading:
                if pyfile.id == pyid:
                    pyfile.plugin.req.abort = True
                    break
            return False

        self.data['order'].remove(pyid)
        del self.data[pyid]

    def get_id(self):
        """return a free id"""
        id = 1
        while id in self.data.keys():
            id += 1

        return id

    def move(self, id, offset=-1):
        
        for pyfile in self.files:
            if pyfile.id == id:
                index = self.files.index(pyfile)
                pyfile = self.files.pop(index)
                self.files.insert(index + offset, pyfile)
                break

        index = self.data['order'].index(id)
        pyfile = self.data['order'].pop(index)
        self.data['order'].insert(index + offset, pyfile)

    def save(self):
        self.lock.acquire()

        output = open('links.pkl', 'wb')
        cPickle.dump(self.data, output, -1)

        self.inform_client()
        
        self.lock.release()

    def load(self):
        try:
            pkl_file = open('links.pkl', 'rb')
            obj = cPickle.load(pkl_file)
        except:
            obj = {'version': LIST_VERSION, 'order': []}

        if obj['version'] < LIST_VERSION:
            obj = {'version': LIST_VERSION, 'order': []}

        for i in obj['order']:
            self.append(obj[i].url, obj[i].folder)

        self.core.logger.info("Links loaded: " + str(int(len(obj) - 2)))

    def inform_client(self):
        obj = RequestObject()
        obj.command = "file_list"
        obj.data = self.data

        self.core.server.push_all(obj)

class Data():
    def __init__(self, url, folder=""):
        self.url = url
        self.folder = folder

class PyLoadFile:
    """ represents the url or file
    """
    def __init__(self, parent, url):
        self.parent = parent
        self.id = None
        self.url = url
        self.folder = None
        self.filename = "filename"
        self.download_folder = ""
        self.modul = __import__(self._get_my_plugin())
        pluginClass = getattr(self.modul, self.modul.__name__)
        self.plugin = pluginClass(self)
        self.status = Status(self)

    def _get_my_plugin(self):
        """ searches the right plugin for an url
        """
        for plugin, plugin_pattern in self.parent.plugins_avaible.items():
            if re.match(plugin_pattern, self.url) != None:
                return plugin

        return "Plugin"

    def init_download(self):

        if self.parent.config['proxy']['activated']:
            self.plugin.req.add_proxy(self.parent.config['proxy']['protocol'], self.parent.config['proxy']['adress'])

        #@TODO: check dependicies, ocr etc

