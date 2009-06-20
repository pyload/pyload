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

LIST_VERSION = 1

import cPickle
from Py_Load_File import PyLoadFile
from module.remote.RequestObject import RequestObject

class File_List(object):
    def __init__(self, core):
        self.core = core
        self.files = []
        self.data = {'version': LIST_VERSION}
        self.load()

    def new_pyfile(self, url):
        url  = url.replace("\n", "")
        pyfile = PyLoadFile(self.core, url)
        pyfile.download_folder = self.core.config['download_folder']
        pyfile.id = self.get_id()

        return pyfile

    def append(self, url):
        new_file = self.new_pyfile(url)
        self.files.append(new_file)
        self.data[new_file.id] = Data(url)

    def extend(self, urls):
        for url in urls:
            self.append(url)

    def remove(self, pyfile):

        pass

        #if pyfile in self.files:
            #self.files.remove(pyfile)
#
        #del self.data[pyfile.id]

    def get_id(self):
        """return a free id"""
        id = 1
        while id in self.data.keys():
            id += 1

        return id
        
    def save(self):
        output = open('links.pkl', 'wb')
        cPickle.dump(self.data, output, -1)

        self.inform_client()

    def load(self):
        try:
            pkl_file = open('links.pkl', 'rb')
            obj = cPickle.load(pkl_file)
        except:
            obj = {'version': LIST_VERSION}

        if obj['version'] < LIST_VERSION:
            obj = {'version': LIST_VERSION}

        for key, value in obj.iteritems():
            if key != 'version':
                self.append(value.url)

        self.core.logger.info("Links loaded: "+  str(int(len(obj) - 1)))

    def inform_client(self):
        obj = RequestObject()
        obj.command = "file_list"
        obj.data = self.data

        self.core.server.push_all(obj)

class Data():
    def __init__(self, url):
        self.url = url
