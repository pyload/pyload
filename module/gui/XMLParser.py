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
    
    @author: mkaay
"""
from __future__ import with_statement

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

import os

class XMLParser():
    def __init__(self, data, dfile=""):
        self.mutex = QMutex()
        self.mutex.lock()
        self.xml = QDomDocument()
        self.file = data
        self.dfile = dfile
        self.mutex.unlock()
        self.loadData()
        self.root = self.xml.documentElement()
    
    def loadData(self):
        self.mutex.lock()
        f = self.file
        if not os.path.exists(f):
            f = self.dfile
        with open(f, 'r') as fh:
            content = fh.read()
        self.xml.setContent(content)
        self.mutex.unlock()
    
    def saveData(self):
        self.mutex.lock()
        content = self.xml.toString()
        with open(self.file, 'w') as fh:
            fh.write(content)
        self.mutex.unlock()
        return content
    
    def parseNode(self, node, ret_type="list"):
        if ret_type == "dict":
            childNodes = {}
        else:
            childNodes = []
        child = node.firstChild()
        while True:
            n = child.toElement()
            if n.isNull():
                break
            else:
                if ret_type == "dict":
                    childNodes[str(n.tagName())] = n
                else:
                    childNodes.append(n)
            child = child.nextSibling()
        return childNodes
