#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@author: mkaay



from builtins import str
from builtins import object
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

import os

class XMLParser(object):
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
