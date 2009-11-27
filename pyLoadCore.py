#!/usr/bin/env python
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
    
    @author: spoob
    @author: sebnapi
    @author: RaNaN
    @author: mkaay
    @version: v0.3
"""

CURRENT_VERSION = '0.3'

import ConfigParser
import gettext
from glob import glob
import logging
import logging.handlers
from os import mkdir
from os import sep
from os import chdir
from os.path import basename
from os.path import exists
from os.path import dirname
from os.path import abspath
import subprocess
from sys import argv
from sys import exit
from sys import path
from sys import stdout
import time
from time import sleep
import urllib2
from imp import find_module
from re import sub
try: 
    find_module("Crypto")
except ImportError:
    print "Install pycrypto to use pyLoad"
    exit()
from module.file_list import File_List
from module.thread_list import Thread_List
from module.web.WebServer import WebServer
from module.remote.SecureXMLRPCServer import SecureXMLRPCServer
from module.network.Request import Request
import thread

class Core(object):
    """ pyLoad Core """
    def __init__(self):
        if len(argv) > 1:
            if argv[1] == "-v":
                print "pyLoad", CURRENT_VERSION
                exit()
            
    def read_config(self):
        """ read config and sets preferences """
        self.configfile = ConfigParser.SafeConfigParser()
        self.configfile.read('config')
        for section in self.configfile.sections():
            self.config[section] = {}
            for option in self.configfile.options(section):
                self.config[section][option] = self.configfile.get(section, option)
                self.config[section][option] = False if self.config[section][option].lower() == 'false' else self.config[section][option]

    def set_option(self, section, option, value):
        self.config[option] = value
        self.configfile.set(section, option, str(value))
        self.configfile.write(open('config', "wb"))

    def read_option(self):
        return self.config

    def init_webserver(self):
#        if not self.config['webinterface']['activated']:
#            return False
        return False
        try:
            self.webserver = WebServer()
            self.webserver.start()
        except Exception, e:
            self.logger.error("Failed starting webserver, no webinterface available: %s" % str(e))
            exit()

    def shutdown(self):
        "abort all downloads and exit"
        self.thread_list.pause = True

        for pyfile in self.thread_list.py_downloading:
            pyfile.plugin.req.abort = True

        while self.thread_list.py_downloading:
            sleep(1)
        self.logger.info("Going to shutdown pyLoad")
        exit()

    def toggle_pause(self):
        if self.thread_list.pause:
            self.thread_list.pause = False
            return False
        elif not self.thread_list.pause:
            self.thread_list.pause = True
            return True

    def start(self):
        """ starts the machine"""
        chdir(dirname(abspath(__file__)) + sep)
        
        self.config = {}
        self.plugin_folder = "module" + sep + "plugins"
        self.plugins_avaible = {}

        self.read_config()

        self.do_kill = False
        translation = gettext.translation("pyLoad", "locale", languages=[self.config['general']['language']])
        translation.install(unicode=True)
    
        self.check_install("pycurl", "pycurl for lower memory footprint while downloading")
        self.check_install("tesseract", "tesseract for captcha reading", False)
        self.check_install("gocr", "gocr for captcha reading", False)
        self.check_file(self.config['log']['log_folder'], _("folder for logs"))
        self.check_file(self.config['general']['download_folder'], _("folder for downloads"))
        self.check_file(self.config['general']['link_file'], _("file for links"), False)
        self.check_file(self.config['general']['failed_file'], _("file for failed links"), False)

        if self.config['general']['debug_mode']:
            self.init_logger(logging.DEBUG) # logging level
            self.print_test_status = True
        else:
            self.init_logger(logging.INFO) # logging level
            self.print_test_status = False

        self.check_update()

        self.logger.info(_("Downloadtime: %s") % self.is_time_download()) # debug only

        path.append(self.plugin_folder)
        self.create_plugin_index()

        self.init_server()

        self.file_list = File_List(self)
        self.thread_list = Thread_List(self)

#        Webserver
        #self.self.server()
        self.init_webserver()
        
                    
        self.read_url_list(self.config['general']['link_file'])
        
        while True:
            sleep(2)
            if self.do_kill:
                self.logger.info("pyLoad quits")
                exit()
    
    def init_server(self):
        try:
            server_addr = (self.config['remote']['listenaddr'], int(self.config['remote']['port']))
            usermap = {
                self.config['remote']['username']: self.config['remote']['password']
            }
            self.server = SecureXMLRPCServer(server_addr, self.config['ssl']['cert'], self.config['ssl']['key'], usermap)
            self.server.register_introspection_functions()
            self.server.register_function(self.status_downloads)
            self.server.register_function(self.status_server)
            self.server.register_function(self.kill)
            self.server.register_function(self.del_urls)
            self.server.register_function(self.add_urls)
            self.server.register_function(self.get_urls)
            self.server.register_function(self.move_urls_up)
            self.server.register_function(self.move_urls_down)
            self.server.register_function(self.is_time_download)
            self.server.register_function(self.is_time_reconnect)
            self.server.register_function(self.get_conf_val)
            self.server.register_function(self.file_exists)
            self.server.register_function(self.get_server_version)
            self.logger.info("SecureXMLRPC Server Started")
            thread.start_new_thread(self.server.serve_forever, ())
        except Exception, e:
            self.logger.error("Failed starting socket server, CLI and GUI will not be available: %s" % str(e))

    def init_logger(self, level):
        
        file_handler = logging.handlers.RotatingFileHandler(self.config['log']['log_folder'] + sep + 'log.txt', maxBytes=102400, backupCount=int(self.config['log']['log_count'])) #100 kib each
        console = logging.StreamHandler(stdout)

        frm = logging.Formatter("%(asctime)s: %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        file_handler.setFormatter(frm)
        console.setFormatter(frm)

        self.logger = logging.getLogger("log") # settable in config

        if self.config['log']['file_log']:
            self.logger.addHandler(file_handler)

        self.logger.addHandler(console) #if console logging
        self.logger.setLevel(level)

    def check_install(self, check_name, legend, python=True, essential=False):
        """check wether needed tools are installed"""
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)
        except:
            print "Install", legend
            if essential: exit()

    def check_file(self, check_name, legend, folder=True):
        """check wether needed files are exists"""
        if not exists(check_name):
            try:
                if folder:
                    mkdir(check_name)
                else:
                    open(check_name, "w")
                print _("%s created") % legend
            except:
                print _("could not create %s") % legend
                exit()
                
    def check_update(self):
        """checks newst version"""
        if not self.config['updates']['search_updates']:
            return False
        
        newst_version = Request().load("http://update.pyload.org/index.php?do=" + CURRENT_VERSION)
        if newst_version == "True":
            if not self.config['updates']['install_updates']:
                self.logger.info("New Version of pyLoad available")
            else:
                updater = __import__("pyLoadUpdater")
                updater.main()
        else:
            self.logger.info("No Updates for pyLoad")

    def create_plugin_index(self):
        for file_handler in glob(self.plugin_folder + sep + '*.py') + glob(self.plugin_folder + sep + 'DLC.pyc'):
            plugin_pattern = ""
            plugin_file = sub("(\.pyc|\.py)", "", basename(file_handler))
            if plugin_file == "DLC":
                plugin_pattern = "(?!http://).*\.dlc"
            else:
                for line in open(file_handler, "r").readlines():
                    if "props['pattern']" in line:
                        plugin_pattern = line.split("r\"")[1].split("\"")[0]
                        break
            if plugin_pattern != "":
                self.plugins_avaible[plugin_file] = plugin_pattern
                self.logger.debug(plugin_file + _(" added"))
        self.logger.info(_("created index of plugins"))

    def compare_time(self, start, end):
        if start == end: return True

        now  = time.localtime()[3:5]
        if start < now and end > now: return True
        elif start > end and (now > start or now < end): return True
        elif start < now and end < now and start > end: return True
        else: return False
        
    ####################################
    ########## XMLRPC Methods ##########
    ####################################
        
    def status_downloads(self):
        downloads = []
        for pyfile in self.thread_list.py_downloading:
            download = {}
            download['id'] = pyfile.id
            download['name'] = pyfile.status.filename
            download['speed'] = pyfile.status.get_speed()
            download['eta'] = pyfile.status.get_ETA()
            download['kbleft'] = pyfile.status.kB_left()
            download['size'] = pyfile.status.size()
            download['percent'] = pyfile.status.percent()
            download['status'] = pyfile.status.type
            download['wait_until'] = pyfile.status.waituntil
            download['plugin'] = pyfile.status.plugin
            downloads.append(download)
        return downloads
    
    def get_conf_val(self, cat, var):
        if var != "username" and var != "password":
            return self.config[cat][var]
        else:
            raise Exception("not allowed!")
    
    def status_server(self):
        status = {}
        status['pause'] = self.thread_list.pause
        status['queue'] = len(self.file_list.files)
        status['speed'] = 0

        for pyfile in self.thread_list.py_downloading:
            status['speed'] += pyfile.status.get_speed()

        return status
    
    def file_exists(self, path): #@XXX: security?!
        return exists(path)
    
    def get_server_version(self):
        return CURRENT_VERSION
    
    def add_urls(self, links):
        for link in links:
            self.file_list.collector.addLink(link)
        self.file_list.save()
    
    def del_urls(self, ids):
        for id in ids:
            self.file_list.remove_id(id)
        self.file_list.save()
        
    def kill(self):
        self.do_kill = True
        return True
    
    def get_urls(self):
        return self.file_list.data

    def move_urls_up(self, ids):
        for id in ids:
            self.file_list.move(id)
        self.file_list.save()

    def move_urls_down(self, ids):
        for id in ids:
            self.file_list.move(id, 1)
        self.file_list.save()
        
    def read_url_list(self, url_list):
        """read links from txt"""
        txt = open(self.config['general']['link_file'], 'r')
        new_links = 0
        links = txt.readlines()
        for link in links:
            if link != "\n":
                self.file_list.append(link)
                new_links += 1

        txt.close()

        self.file_list.save()
        if new_links:
            self.logger.info("Parsed link from %s: %i" % (self.config['general']['link_file'], new_links))

        txt = open(self.config['general']['link_file'], 'w')
        txt.write("")
        txt.close()

    def is_time_download(self):
        start = self.config['downloadTime']['start'].split(":")
        end = self.config['downloadTime']['end'].split(":")
        return self.compare_time(start, end)

    def is_time_reconnect(self):
        start = self.config['reconnectTime']['start'].split(":")
        end = self.config['reconnectTime']['end'].split(":")
        return self.compare_time(start, end)

if __name__ == "__main__":
    pyload_core = Core()
    pyload_core.start()
