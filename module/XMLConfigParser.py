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

from xml.dom.minidom import parse

class XMLConfigParser():
    def __init__(self, data):
        self.xml = None
        self.file = data
        self.config = {}
        self.loadData()
        self.root = None
    
    def loadData(self):
        with open(self.file, 'r') as fh:
            self.xml = parse(fh)
        self._read_config()
    
    def saveData(self):
        with open(self.file, 'w') as fh:
            self.xml.writexml(fh)
    
    def _read_config(self):
        def format(val):
            if val.lower() == "true":
                return True
            elif val.lower() == "false":
                return False
            else:
                return val
        root = self.xml.documentElement
        self.root = root
        config = {}
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                section = node.tagName
                config[section] = {}
                for opt in node.childNodes:
                    if opt.nodeType == opt.ELEMENT_NODE:
                        config[section][opt.tagName] = format(opt.firstChild.data)
        self.config = config
    
    def get(self, section, option, default=None):
        try:
            return self.config[section][option]
        except:
            return default
    
    def getConfig(self):
        return self.config
    
    def set(self, section, option, value):
        root = self.root
        replace = False
        sectionNode = False
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if section == node.tagName:
                    sectionNode = node
                    for opt in node.childNodes:
                        if opt.nodeType == opt.ELEMENT_NODE:
                            if option == opt.tagName:
                                replace = opt
        text = self.createTextNode(value)
        if replace:
            replace.replaceChild(text, replace.firstChild)
        else:
            newNode = self.createElement(option)
            newNode.appendChild(text)
            if sectionNode:
                sectionNode.appendChild(newNode)
            else:
                newSection = self.createElement(section)
                newSection.appendChild(newNode)
                root.appendChild(newSection)
        self.saveData()
        self.loadData()
