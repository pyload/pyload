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
CURRENT_VERSION = '0.1'

import ConfigParser
import gettext
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

from module.file_list import File_List
from module.remote.RequestObject import RequestObject
from module.remote.SocketServer import ServerThread
from module.thread_list import Thread_List

class Core(object):
    """ pyLoad main
    """
    def __init__(self):
        self.config = {}
        self.config['plugin_folder'] = "plugins"
        self.plugins_avaible = {}

        self.read_config()

        self.do_kill = False

        translation = gettext.translation("pyLoad", "locale", languages=[self.config['language']])
        translation.install(unicode=True)

        self.check_create(self.config['log_folder'], _("folder for logs"))
        self.check_create(self.config['download_folder'], _("folder for downloads"))
        self.check_create(self.config['link_file'], _("file for links"), False)
        self.check_create(self.config['failed_file'], _("file for failed links"), False)

        self.init_logger(logging.DEBUG) # logging level

        #self.check_update()

        self.logger.info(_("Downloadtime: %s") % self.is_dltime()) # debug only

        path.append(self.config['plugin_folder'])
        self.create_plugin_index()

        self.init_server()

        self.file_list = File_List(self)
        self.thread_list = Thread_List(self)

    def read_config(self):
        """ read config and sets preferences
        """
        config = ConfigParser.SafeConfigParser()
        config.read('config')

        for section in config.sections():
            for option in config.options(section):
                self.config[option] = config.get(section, option)
                self.config[option] = False if self.config[option].lower() == 'false' else self.config[option]

    def create_plugin_index(self):
        for file_handler in glob(self.config['plugin_folder'] + sep + '*.py') + glob(self.config['plugin_folder'] + sep + 'DLC.pyc'):
            if file_handler != self.config['plugin_folder'] + sep + "Plugin.py":
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
        txt = open(self.config['link_file'], 'r')
        new_links = 0
        links = txt.readlines()
        for link in links:
            if link != "\n":
                self.file_list.append(link)
                new_links += 1

        txt.close()

        self.file_list.save()
        if new_links:
            self.logger.info("Parsed link from %s: %i" % (self.config['link_file'], new_links))

        txt = open(self.config['link_file'], 'w')
        txt.write("")
        txt.close()

    #def check_update(self):
        #"""checks newst version
        #"""
        #newst_version = urllib2.urlopen("http://pyload.nady.biz/files/version.txt").readline().strip()
        #if CURRENT_VERSION < newst_version:
            #self.logger.info(_("new update %s on pyload.org") % newst_version) #newer version out
        #elif CURRENT_VERSION == newst_version:
            #self.logger.info(_("newst version %s in use:") % CURRENT_VERSION) #using newst version
        #else:
            #self.logger.info(_("beta version %s in use:") % CURRENT_VERSION) #using beta version

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

        file_handler = logging.handlers.RotatingFileHandler(self.config['log_folder'] + sep + 'log.txt', maxBytes=102400, backupCount=int(self.config['log_count'])) #100 kib each
        console = logging.StreamHandler(stdout)

        frm = logging.Formatter("%(asctime)s: %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        file_handler.setFormatter(frm)
        console.setFormatter(frm)

        self.logger = logging.getLogger("log") # settable in config

        if self.config['file_log']:
            self.logger.addHandler(file_handler)

        self.logger.addHandler(console) #if console logging
        self.logger.setLevel(level)

    def is_dltime(self):
        start_h, start_m = self.config['start'].split(":")
        end_h, end_m = self.config['end'].split(":")

        if (start_h, start_m) == (end_h, end_m):
            return True

        hour, minute  = time.localtime()[3:5]

        if hour > int(start_h) and hour < int(end_h):
            return True
        elif hour < int(end_h) and int(start_h) > int(end_h):
            return True
        elif hour == int(start_h) and minute >= int(start_m):
            return True
        elif hour == int(end_h) and minute <= int(end_m):
            return True
        else:
            return False

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

    def format_time(self, seconds):
        seconds = int(seconds)
        if seconds > 60:
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)
            return "%.2i:%.2i:%.2i" % (hours, minutes, seconds)
        return _("%i seconds") % seconds

    def _test_print_status(self):

        if self.thread_list.py_downloading:

            for pyfile in self.thread_list.py_downloading:
                if pyfile.status.type == 'downloading':
                    print pyfile.status.filename + ": speed is", int(pyfile.status.get_speed()), "kb/s"
                    print pyfile.status.filename + ": finished in", self.format_time(pyfile.status.get_ETA())
                elif pyfile.status.type == 'waiting':
                    print pyfile.status.filename + ": wait", self.format_time(pyfile.status.waituntil - time.time())

    def start(self):
        """ starts the machine
        """
        self.read_links()
        while True:
            #self.thread_list.status()
            self._test_print_status()
            self.server_test()
            sleep(2)
            if self.do_kill: exit()

    def server_test(self):
        obj = RequestObject()
        obj.command = "update"
        obj.data = self.get_downloads()
        obj.status = self.server_status()
        self.server.push_all(obj)

    def server_status(self):
        status = {}
        status['pause'] = self.thread_list.pause
        status['queue'] = len(self.file_list.files)
        return status

    def init_server(self):
        self.server = ServerThread(self)
        self.server.start()
        
    def kill(self):
        self.do_kill = True
        exit()
        return True

    def shutdown(self):
        "abort all downloads and exit"
        self.thread_list.pause = True

        for pyfile in self.thread_list.py_downloading:
            pyfile.plugin.req.abort = True

        while self.thread_list.py_downloading:
            sleep(1)
            
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

if __name__ == "__main__":
    testLoader = Core()
    testLoader.start()

