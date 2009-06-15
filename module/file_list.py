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

class File_List(object):
    def __init__(self):
        self.version = LIST_VERSION
        self.files = []
        self.id = 0

    def set_core(self, core):
        self.core = core

    def new_pyfile(self)
        pyfile = PyLoadFile(self, url)
        pyfile.download_folder = self.core.config['download_folder']
        pyfile.id = self.id
        self.id += 1

        return pyfile

    def append(self, url):
        self.links.append(url)

    def save(self):
        output = open('links.pkl', 'wb')
        cPickle.dump(self, output, -1)


def load(core):
    try:
        pkl_file = open('links.pkl', 'rb')
        obj = cPickle.load(pkl_file)
    except:
        obj = File_List()

    if obj.version < LIST_VERSION:
        obj = File_List()

    obj.set_core(core)

    return obj
