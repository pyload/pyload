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
    
    @author: mkaay, spoob
"""
from __future__ import with_statement

from os.path import exists

from xml.dom.minidom import parse

from shutil import copy

class XMLConfigParser():
    def __init__(self, data):
        self.xml = None
        self.version = "0.1"
        self.file = data
        self.file_default = self.file.replace(".xml", "_default.xml")
        self.config = {}
        self.data = {}
        self.types = {}
        self.loadData()
        self.root = None
    
    def loadData(self):
        file = self.file
        if not exists(self.file):
            self._copyConfig()
        with open(file, 'r') as fh:
            self.xml = parse(fh)
        if not self.xml.documentElement.getAttribute("version") == self.version:
            self._copyConfig()
            with open(file, 'r') as fh:
                self.xml = parse(fh)
            if not self.xml.documentElement.getAttribute("version") == self.version:
                print "Cant Update %s" % self.file
                exit() #ok?
        self._read_config()

    def _copyConfig(self):
        try:
            copy(self.file_default, self.file)
        except:
            print "%s not found" % self.file_default
            exit() #ok?

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
        data = {}
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                section = node.tagName
                config[section] = {}
                data[section] = {}
                data[section]["options"] = {}
                data[section]["name"] = node.getAttribute("name")
                for opt in node.childNodes:
                    if opt.nodeType == opt.ELEMENT_NODE:
                        data[section]["options"][opt.tagName] = {}
                        try:
                            config[section][opt.tagName] = format(opt.firstChild.data)
                            data[section]["options"][opt.tagName]["value"] = format(opt.firstChild.data)
                        except:
                            config[section][opt.tagName] = ""
                        data[section]["options"][opt.tagName]["name"] = opt.getAttribute("name")
                        data[section]["options"][opt.tagName]["type"] = opt.getAttribute("type")
                        data[section]["options"][opt.tagName]["input"] = opt.getAttribute("input")
        self.config = config
        self.data = data
    
    def get(self, section, option, default=None):
        try:
            return self.config[section][option]
        except:
            return default
    
    def getConfig(self):
        return self.config
        
    def set(self, section, data, value):
        root = self.root
        replace = False
        sectionNode = False
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if section == node.tagName:
                    sectionNode = node
                    for opt in node.childNodes:
                        if opt.nodeType == opt.ELEMENT_NODE:
                            if data["option"] == opt.tagName:
                                replace = opt
                    self._setAttributes(node, data)
        text = self.xml.createTextNode(str(value))
        if replace:
            replace.replaceChild(text, replace.firstChild)    
        else:
            newNode = self.xml.createElement(data["option"])
            newNode.appendChild(text)
            if sectionNode:
                sectionNode.appendChild(newNode)
            else:
                newSection = self.xml.createElement(section)
                newSection.appendChild(newNode)
                root.appendChild(newSection)
            self._setAttributes(newSection, data)        
        self.saveData()
        self.loadData()

    def _setAttributes(self, node, data):
        node.setAttribute("name", node.tagName)
        option = node.getElementsByTagName(data["option"])[0]
        option.setAttribute("name", data["name"])
        option.setAttribute("type", data["type"])
        try:
            option.setAttribute("input", data["input"])
        except:
            pass
    
    def getType(self, section, option):
        try:
            return self.data[section]["options"][option]["type"]
        except:
            return "str"
    
    def getInputValues(self, section, option):
        try:
            return self.data[section]["options"][option]["input"].split(";")
        except:
            return []
    
    def getDisplayName(self, section, option=None):
        try:
            if option:
                return self.data[section]["options"][option]["name"]
            else:
                return self.data[section]["name"]
        except:
            if option:
                return option
            else:
                return section
