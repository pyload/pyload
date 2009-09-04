#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#Copyright (C) 2009 spoob, sebnapi, RaNaN
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
CURRENT_VERSION = '0.1.1'

import ConfigParser
import gettext
from glob import glob
import logging
import logging.handlers
from os import mkdir
from os import sep
from os.path import basename
from os.path import exists
from sys import argv
from sys import exit
from sys import path
from sys import stdout
import time
from time import sleep
import urllib2

from module.file_list import File_List
from module.remote.RequestObject import RequestObject
from module.remote.SocketServer import ServerThread
from module.thread_list import Thread_List
from module.web.WebServer import WebServer

class Core(object):
    """ pyLoad main
    """
    def __init__(self):
        self.config = {}
        self.plugin_folder = "module" + sep + "plugins"
        self.plugins_avaible = {}

        self.read_config()

        self.do_kill = False

        translation = gettext.translation("pyLoad", "locale", languages=[self.config['general']['language']])
        translation.install(unicode=True)

        self.check_create(self.config['log']['log_folder'], _("folder for logs"))
        self.check_create(self.config['general']['download_folder'], _("folder for downloads"))
        self.check_create(self.config['general']['link_file'], _("file for links"), False)
        self.check_create(self.config['general']['failed_file'], _("file for failed links"), False)

        if self.config['general']['debug_mode']:
            self.init_logger(logging.DEBUG) # logging level
            self.print_test_status = True
        else:
            self.init_logger(logging.INFO) # logging level
            self.print_test_status = False

        self.check_update()

        self.logger.info(_("Downloadtime: %s") % self.is_dltime()) # debug only

        path.append(self.plugin_folder)
        self.create_plugin_index()

        self.init_server()

        self.file_list = File_List(self)
        self.thread_list = Thread_List(self)

        #Webserver

        self.init_webserver()

    def read_config(self):
        """ read config and sets preferences
        """
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

    def create_plugin_index(self):
        for file_handler in glob(self.plugin_folder + sep + '*.py') + glob(self.plugin_folder + sep + 'DLC.pyc'):
            if file_handler != self.plugin_folder + sep + "Plugin.py":
                plugin_pattern = ""
                plugin_file = basename(file_handler).replace('.pyc', '').replace('.py', '')
                for line in open(file_handler, "r").readlines():
                    if "props['pattern']" in line:
                        plugin_pattern = line.split("r\"")[1].split("\"")[0]
                if plugin_pattern != "":
                    self.plugins_avaible[plugin_file] = plugin_pattern
                    self.logger.debug(plugin_file + _(" added"))
        self.logger.info(_("created index of plugins"))

    def read_links(self):
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

    def check_update(self):
        """checks newst version
        """
        if not self.config['updates']['search_updates']:
            return False
    
        newst_version = urllib2.urlopen("http://update.pyload.org/index.php?do=" + CURRENT_VERSION).readline()
        if newst_version == "True":
            if not self.config['updates']['install_updates']:
                self.logger.info("New version available, please run Updater")
            else:
                updater = __import__("pyLoadUpdater")
                updater.main()
        else:
            self.logger.info("pyLoad is up-to-date")

    def check_create(self, check_name, legend, folder=True):
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

    def is_dltime(self):
        start = self.config['downloadTime']['start'].split(":")
        end = self.config['downloadTime']['end'].split(":")

        return self.compare_time(start, end)
    
    def is_reconnect_time(self):

        start = self.config['reconnectTime']['start'].split(":")
        end = self.config['reconnectTime']['end'].split(":")

        return self.compare_time(start, end)

    def compare_time(self, start, end):

        if start == end:
            return True

        now  = time.localtime()[3:5]

        if start < now and end > now:
            return True
        elif start > end and (now > start or now < end):
            return True
        elif start < now and end < now and start > end:
            return True
        else:
            return False

    def format_time(self, seconds):
        seconds = int(seconds)
        if seconds > 60:
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
        return _("%i seconds") % seconds

    def get_downloads(self):
        list = []
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
            list.append(download)

        return list

    def server_send_status(self):
        obj = RequestObject()
        obj.command = "update"
        obj.data = self.get_downloads()
        obj.status = self.server_status()
        self.server.push_all(obj)

    def server_status(self):
        status = {}
        status['pause'] = self.thread_list.pause
        status['queue'] = len(self.file_list.files)
        status['speed'] = 0

        for pyfile in self.thread_list.py_downloading:
            status['speed'] += pyfile.status.get_speed()

        return status

    def init_server(self):

        try:
            self.server = ServerThread(self)
            self.server.start()
        except Exception, e:
            self.logger.error("failed starting socket server, CLi and Gui will not be available: %s" % str(e))

    def init_webserver(self):

        if not self.config['webinterface']['activated']:
            return False

        try:
            self.webserver = WebServer(self)
            self.webserver.start()
        except Exception, e:
            self.looger.error("failed starting webserver, no webinterface available: %s" % str(e))

    def kill(self):
        self.do_kill = True
        self.logger.info("Going to kill pyLoad")
        exit()
        return True

    def shutdown(self):
        "abort all downloads and exit"
        self.thread_list.pause = True

        for pyfile in self.thread_list.py_downloading:
            pyfile.plugin.req.abort = True

        while self.thread_list.py_downloading:
            sleep(1)
        self.logger.info("Going to shutdown pyLoad")
        exit()
    
    def add_links(self, links):
        self.file_list.extend(links)
        self.file_list.save()

    def remove_links(self, ids):
        for id in ids:
            self.file_list.remove_id(id)
        self.file_list.save()

    def get_links(self):
        return self.file_list.data

    def move_links_up(self, ids):

        for id in ids:
            self.file_list.move(id)

        self.file_list.save()

    def move_links_down(self, ids):

        for id in ids:
            self.file_list.move(id, 1)

        self.file_list.save()

    def toggle_pause(self):
        if self.thread_list.pause:
            self.thread_list.pause = False
            return False
        elif not self.thread_list.pause:
            self.thread_list.pause = True
            return True

    def start(self):
        """ starts the machine
        """
        if len(argv) > 1:
            shortOptions = 'pu:l:'
            longOptions = ['print', 'url=', 'list=']

            opts, extraparams = __import__("getopt").getopt(argv[1:], shortOptions, longOptions) 
            for option, params in opts:
                if option in ("-p", "--print"):
                    print "Print test output"
                    self.print_test_status = True
                elif option in ("-u", "--url"):
                    self.logger.info("Add url: " + params)
                    self.add_links([params])
                elif option in ("-l", "--list"):
                    list = open(params, 'r').readlines()
                    self.add_links(list)
                    self.logger.info("Add list:" + params)
                    
        self.read_links()

        while True:
            #self.thread_list.status()
            if self.print_test_status:
                self._test_print_status()
            self.server_send_status()
            sleep(2)
            if self.do_kill:
                self.logger.info("pyLoad quits")
                exit()

    def _test_print_status(self):

        if self.thread_list.py_downloading:
            for pyfile in self.thread_list.py_downloading:
                if pyfile.status.type == 'downloading':
                    print pyfile.status.filename + ": speed is", int(pyfile.status.get_speed()), "kb/s"
                    print pyfile.status.filename + ": finished in", self.format_time(pyfile.status.get_ETA())
                elif pyfile.status.type == 'waiting':
                    print pyfile.status.filename + ": wait", self.format_time(pyfile.status.waituntil - time.time())

if __name__ == "__main__":
    if len(argv) > 1:
        if argv[1] == "-v":
            print "pyLoad", CURRENT_VERSION
            exit()

    testLoader = Core()
    testLoader.start()
