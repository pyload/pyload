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
    def __init__(self, data, forceDefault=False):
        self.xml = None
        self.version = "0.1"
        self.file = data
        self.file_default = self.file.replace(".xml", "_default.xml")
        self.forceDefault = forceDefault
        self.config = {}
        self.data = {}
        self.types = {}
        self.loadData()
        self.root = self.xml.documentElement
        if not forceDefault:
            self.defaultParser = XMLConfigParser(data, True)
    
    def loadData(self):
        file = self.file
        if self.forceDefault:
            file = self.file_default
        if not exists(self.file) and self.forceDefault:
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
        self.root = self.xml.documentElement
        self._read_config()

    def _copyConfig(self):
        try:
            copy(self.file_default, self.file)
        except:
            print "%s not found" % self.file_default
            exit() #ok?

    def saveData(self):
        if self.forceDefault:
            return
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
            if self.forceDefault:
                return default
            return self.defaultParser.get(section, option, default)
    
    def getConfig(self):
        return Config(self)
    
    def getConfigDict(self):
        return self.config
        
    def set(self, section, data, value):
        root = self.root
        replace = False
        sectionNode = False
        if type(data) == str:
            data = {"option": data}
        if not self.checkInput(section, data["option"], value):
            raise Exception("invalid input")
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if section == node.tagName:
                    sectionNode = node
                    for opt in node.childNodes:
                        if opt.nodeType == opt.ELEMENT_NODE:
                            if data["option"] == opt.tagName:
                                replace = opt
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
        self._setAttributes(section, data)        
        self.saveData()
        self.loadData()
    
    def remove(self, section, option):
        root = self.root
        for node in root.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if section == node.tagName:
                    for opt in node.childNodes:
                        if opt.nodeType == opt.ELEMENT_NODE:
                            if option == opt.tagName:
                                node.removeChild(opt)
                                self.saveData()
                                return
                                

    def _setAttributes(self, node, data):
        option = self.root.getElementsByTagName(node)[0].getElementsByTagName(data["option"])[0]
        try:
            option.setAttribute("name", data["name"])
        except:
            pass
        try:
            option.setAttribute("type", data["type"])
        except:
            pass
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
            if not self.data[section]["options"][option]["input"]:
                return []
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
    
    def isValidSection(self, section):
        try:
            self.config[section]
            return True
        except:
            return False
    
    def checkInput(self, section, option, value):
        oinput = self.getInputValues(section, option)
        print oinput
        if oinput:
            for i in oinput:
                if i == value:
                    return True
            return False
        otype = self.getType(section, option)
        if not otype:
            return True
        if otype == "int" and (type(value) == int or re.match("^\d+$")):
            return True
        elif otype == "bool" and (type(value) == bool or re.match("^(true|false|True|False)$")):
            return True
        elif otype == "time" and re.match("^[0-2]{0,1}\d:[0-5]{0,1}\d$"):
            return True
        elif otype == "ip" and re.match("^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"):
            return True
        elif otype == "str":
            return True
        else:
            return False
    
class Config(object):
    def __init__(self, parser):
        self.parser = parser
    
    def __getitem__(self, key):
        if self.parser.isValidSection(key):
            return Section(self.parser, key)
        raise Exception("invalid section")
    
    def keys(self):
        return self.parser.config.keys()

class Section(object):
    def __init__(self, parser, section):
        self.parser = parser
        self.section = section
    
    def __getitem__(self, key):
        return self.parser.get(self.section, key)
    
    def __setitem__(self, key, value):
        self.parser.set(self.section, key, value)
