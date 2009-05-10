#!/usr/bin/python
# -*- coding: utf-8 -*- 
# 
#Copyright (C) 2009 sp00b, sebnapi
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
CURRENT_VERSION = '0.1'

#python imports
import ConfigParser
from glob import glob
from string import find, split
from os import sep, chdir, mkdir, curdir, name, system
from os.path import exists, abspath, dirname, basename
from sys import path, exit
from logging import warning, basicConfig
import urllib2
import re
from time import sleep

#my imports
from download_thread import Download_Thread
from thread_list import Thread_List
from Py_Load_File import PyLoadFile

basicConfig(filename='Logs/faild.txt', format = '%(message)s')

class Core(object):
    """ pyLoad main 
    """
    def __init__(self):
        self.download_folder = ""
        self.link_file = "links.txt"
        #self.applicationPath = ""
        self.search_updates = False
        self.plugins_folder = ""
        self.read_config()
        self.thread_list = Thread_List(self)
        self.create_download_folder(self.download_folder)
        self.create_link_file(self.link_file)
        self.check_update()
        
    def read_config(self):
        """ sets self.download_folder, self.applicationPath, self.search_updates and self.plugins_folder
        """
        #self.applicationPath = dirname(abspath(__file__)) + sep
        config = ConfigParser.ConfigParser()
        #config.read(self.applicationPath + 'config')
        config.read('config')
        self.download_folder = config.get('general', 'downloadFolder')
        self.search_updates = config.get('updates', 'searchUpdates')
        self.plugins_folder = 'Plugins'
        path.append(self.plugins_folder)
        
    def get_avial_plugins(self, plugin_folder):
        """ searches the plugin-folder for plugins
        """
        #for file in glob(plugin_folder + "/" + '*.py'):
            #if file.endswith('.py'):
                #self.plugin_file = basename(file).replace('.py', '')
                #print self.plugin_file
                #try:
                    #self.new_plugin = __import__(self.plugin_file)
                    #if self.new_plugin.plugin_type in "hoster" or self.new_plugin.plugin_type in "container":
                        #print "Plugin geladen: " + self.new_plugin.plugin_name
                        #self.plugins[self.plugin_file] = __import__(self.plugin_file)
                #except:
                    #print "Fehlerhaftes Plugin: " + self.plugin_file
        pluginlist = []
        import os
        for f in os.listdir(plugin_folder):
            if f.split(".")[1] == "py":
                pluginlist.append(__import__(f.split('.')[0],globals(),locals(),[]))
        print pluginlist
        for modul in pluginlist:
            instance = modul.Test_plug()
            print instance.Function()
            print instance.pluginProp ['name'] 
        print "s"
                
    def _get_links(self, link_file):
        """ funktion nur zum testen ohne gui bzw. tui
        """
        links = open(link_file, 'r').readlines()
        self.extend_links(links)               

    def append_link(self, link):
        if link not in self.thread_list.get_loaded_urls():
            plugin_name, plugin = self.get_hoster(link)
            if plugin != None:
                self.__new_py_load_file(link, plugin_name, plugin)
            else:
                return False
    
    def extend_links(self, links):
        for link in links:
            self.append_link(link)

    def check_update(self):
        """checks newst version
        """
        newst_version = urllib2.urlopen("http://pyload.nady.biz/files/version.txt").readline().strip()
        if CURRENT_VERSION < newst_version:
            print "Neues Update " + newst_version + " auf pyload.de.rw" #newer version out
        elif CURRENT_VERSION == newst_version:
            print "Neuste Version " + CURRENT_VERSION + " in benutzung" #using newst version
        else:
            print "Beta Version " + CURRENT_VERSION + " in benutzung" #using beta version

    def create_download_folder(self, download_folder):
        """ if download_folder not exists create one
        """
        if not exists(download_folder): #if download folder not exists
            try:
                mkdir(download_folder) #create download folder
                print "Ordner fuer Downloads erstellt: %s" + download_folder
            except:
                print "Konnte Ordner fuer Downloads nicht erstellen"
                exit()
    
    def create_link_file(self, link_file):
        """ if link_file not exists create one
        """
        if not exists(link_file): #if file for links not exists
            try:
                open(link_file,'w').close() #create file for links
                print "Datei fuer Links erstellt: " + link_file
            except:
                print "Konnte Datei fuer Links nicht erstellen"
                exit()
    
    #def addLinks(self, newLinks, atTheBeginning):
        #pass
        
    def get_hoster(self, url):
        """ searches the right plugin for an url
        """
        for plugin_name, plugin in self.plugins.items():
            if re.match(plugin.plugin_pattern, url) != None: #guckt ob übergebende url auf muster des plugins passt
                return [plugin_name, plugin]
        #logger: kein plugin gefunden
        return None
            
            
    def __new_py_load_file(self, url, plugin_name, plugin):
        new_file = PyLoadFile(plugin, plugin_name, url)
        new_file.download_folder = self.download_folder
        self.thread_list.append_py_load_file(new_file)
        return True
    
    def _test_print_status(self):
        if len(self.thread_list.threads)>0:
            for pyfile in self.thread_list.py_load_files:
                if pyfile.status != None:
                    fn = pyfile.status.filename
                    p = round(float(pyfile.status.downloaded_kb)/pyfile.status.total_kb, 2)
                    s = round(pyfile.status.rate, 2)
                    del pyfile.status
                    pyfile.status = None
                    print fn + ": " + str(p) + " @ " + str(s) + "kB/s"
    
    def start(self):
        """ starts the machine
        """
        while True:
            self._get_links(self.link_file)
            self.thread_list.status()
            self._test_print_status()
            sleep(0.1)
            if len(self.thread_list.threads) == 0:
                break

testLoader = Core()
testLoader.get_avial_plugins('Plugins')
