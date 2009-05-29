#!/usr/bin/python
# -*- coding: utf-8 -*- 
# 
#Copyright (C) 2009 sp00b, sebnapi, RaNaN
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
import logging
import logging.handlers
import time
import urllib2
from glob import glob
from os import mkdir
from os import sep
from os.path import basename
from os.path import exists
from sys import exit
from sys import path
from sys import stdout
from time import sleep

from module.Py_Load_File import PyLoadFile
from module.remote.SocketServer import ServerThread
from module.thread_list import Thread_List

class Core(object):
    """ pyLoad main 
    """
    def __init__(self):
        self.check_update()

        self.config = {}
        self.config['plugin_folder'] = "Plugins"
        self.config['link_file'] = "links.txt"
        self.plugins_avaible = {}
        self.search_updates = False

        self.read_config()
        print "Downloadtime:", self.is_dltime() # debug only

        self.thread_list = Thread_List(self)
        
        self.check_create(self.config['download_folder'], "Ordner für Downloads")
        self.check_create(self.config['log_folder'], "Ordner für Logs")
        self.check_create(self.config['link_file'], "Datei für Links", False)

        self.init_logger(logging.DEBUG) # logging level

        path.append(self.config['plugin_folder'])
        self.create_plugin_index()
        
    def read_config(self):
        """ read config and sets preferences
        """
        config = ConfigParser.SafeConfigParser()
        config.read('config')

        for section in config.sections():
            for option in config.options(section):
                self.config[option] = config.get(section, option)
		self.config[option] = False if self.config[option].lower == 'False' else self.config[option]
    
        self.config['download_folder'] = config.get('general', 'downloadFolder')
        self.config['link_file'] = config.get('general', 'linkFile')
        self.config['search_updates'] = config.getboolean('updates', 'searchUpdates')
        self.config['log_folder'] = config.get('log', 'logFolder')
        self.config['reconnectMethod'] = config.get('general', 'reconnectMethod')

    def create_plugin_index(self):
        for file_handler in glob(self.config['plugin_folder'] + sep + '*.py'):
            if file_handler != self.config['plugin_folder'] + sep + "Plugin.py":
                plugin_pattern = ""
                plugin_file = basename(file_handler).replace('.py', '')
                for line in open(file_handler, "r").readlines():
                    if "props['pattern']" in line:
                        plugin_pattern = line.split("r\"")[1].split("\"")[0]
                if plugin_pattern != "":
                    self.plugins_avaible[plugin_file] = plugin_pattern
                    self.logger.debug(plugin_file + " hinzugefuegt")
        print "Index der Plugins erstellt"

##    def check_needed_plugins(self):
##        links = open(self.link_file, 'r').readlines()
##        plugins_indexed = pickle.load(open(self.plugin_index, "r"))
##        for link in links:
##            link = link.replace("\n", "")
##            for plugin_file in plugins_indexed.keys():
##                if re.search(plugins_indexed[plugin_file], link) != None:
##                    self.plugins_needed[plugin_file] = plugins_indexed[plugin_file]
##        print "Benoetigte Plugins: " + str(self.plugins_needed.keys())
##
##    def import_needed_plugins(self):
##        for needed_plugin in self.plugins_needed.keys():
##            self.import_plugin(needed_plugin)
##
##    def import_plugin(self, needed_plugin):
##        try:
##            new_plugin = __import__(needed_plugin)
##            self.plugins_dict[new_plugin] = self.plugins_needed[needed_plugin]
##            #if new_plugin.plugin_type in "hoster" or new_plugin.plugin_type in "container":
##            #   print "Plugin geladen: " + new_plugin.plugin_name
##            #plugins[plugin_file] = __import__(plugin_file)
##        except:
##            print "Fehlerhaftes Plugin: " + needed_plugin
##

    def _get_links(self, link_file):
        """ funktion nur zum testen ohne gui bzw. tui
        """
        links = open(link_file, 'r').readlines()
        self.extend_links(links)               

    def append_link(self, link):
        if link not in self.thread_list.get_loaded_urls():
            self.__new_py_load_file(link)
                
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

    def check_create(self, check_name, legend, folder=True):
        if not exists(check_name):
            try:
                if folder:
                    mkdir(check_name)
                else:
                    open(check_name, "w")
                print legend, "erstellt"
            except:
                print "Konnte", legend, "nicht erstellen"
                exit()
    
    #def addLinks(self, newLinks, atTheBeginning):
        #pass
        
#    def get_hoster(self, url):
#        """ searches the right plugin for an url
#        """
#        for plugin, plugin_pattern in self.plugins_avaible.items():
#            if re.match(plugin_pattern, url) != None: #guckt ob übergebende url auf muster des plugins passt
#                return plugin
#        #logger: kein plugin gefunden
#        return None
            
            
    def __new_py_load_file(self, url):
        new_file = PyLoadFile(self, url)
        new_file.download_folder = self.config['download_folder']
        self.thread_list.append_py_load_file(new_file)
        return True
    
    def init_logger(self, level):
        handler = logging.handlers.RotatingFileHandler(self.config['log_folder'] + sep + 'log.txt', maxBytes=12800, backupCount=10) #100 kb
        console = logging.StreamHandler(stdout) 
        #handler = logging.FileHandler('Logs/log.txt') 
        frm = logging.Formatter("%(asctime)s: %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S") 
        handler.setFormatter(frm)
        console.setFormatter(frm)
        
        self.logger = logging.getLogger() # settable in config
        self.logger.addHandler(handler)
        self.logger.addHandler(console) #if console logging
        self.logger.setLevel(level)


    def is_dltime(self):
        start_h, start_m = self.config['start'].split(":")
        end_h, end_m = self.config['end'].split(":")

        #@todo: doesnt work at the moment
        hour, minute  = time.localtime()[3:5]

        if hour > int(start_h) and hour < int(end_h):
            return True
        elif hour == int(start_h) and minute >= int(start_m):
            return True
        elif hour == int(end_h) and minute <= int(end_m):
            return True
        else:
            return False

    def _test_print_status(self):
        if self.thread_list.py_downloading:
                
            for pyfile in self.thread_list.py_downloading:
                if pyfile.status.type == 'downloading':
                    print pyfile.status.filename + ": speed is", int(pyfile.status.get_speed()), "kb/s"
                    print pyfile.status.filename + ": finished in", int(pyfile.status.get_ETA()), "seconds"
                elif pyfile.status.type == 'waiting':
                    print pyfile.status.filename + ": wait", int(pyfile.status.waituntil - time.time()), "seconds"
    
    def start(self):
        """ starts the machine
        """
        self._get_links(self.config['link_file'])
        while True:
            #self.thread_list.status()
            self._test_print_status()
            sleep(2)
            if len(self.thread_list.threads) == 0:
                break

if __name__ == "__main__":

    testLoader = Core()
    if testLoader.config['remoteactivated']:
        server = ServerThread(testLoader)
   	server.start()
    
    testLoader.start()
