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
from imp import find_module
import logging
import logging.handlers
from os import chdir
from os import listdir
from os import mkdir
from os import makedirs
from os import sep
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import join
from re import sub
import subprocess
from sys import argv
from sys import exit
from sys import path
from sys import stdout
import thread
import time
from time import sleep

from module.file_list import File_List
from module.network.Request import Request
import module.remote.SecureXMLRPCServer as Server
from module.thread_list import Thread_List
from module.web.ServerThread import WebServer

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
        self.configfile.read(join(self.path,'config'))
        for section in self.configfile.sections():
            self.config[section] = {}
            for option in self.configfile.options(section):
                self.config[section][option] = self.configfile.get(section, option)
                self.config[section][option] = False if self.config[section][option].lower() == 'false' else self.config[section][option]

    def set_option(self, section, option, value):
        self.config[option] = value
        self.configfile.set(section, option, str(value))
        self.configfile.write(open(join(self.path,'config'), "wb"))

    def read_option(self):
        return self.config

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
        self.path = dirname(__file__)
        
        self.config = {}
        self.plugin_folder = "module" + sep + "plugins"
        self.plugins_avaible = {}

        self.read_config()

        self.do_kill = False
        translation = gettext.translation("pyLoad", "locale", languages=[self.config['general']['language']])
        translation.install(unicode=True)

        self.check_install("Crypto", "pycrypto to decode container files")
        self.check_install("Image", "Python Image Libary (PIL) for captha reading")
        self.check_install("pycurl", "pycurl for lower memory footprint while downloading")
        self.check_install("django", "Django for webinterface")
        self.check_install("tesseract", "tesseract for captcha reading", False)
        self.check_install("gocr", "gocr for captcha reading", False)
        self.check_file(self.config['log']['log_folder'], _("folder for logs"), True)
        self.check_file(self.config['general']['download_folder'], _("folder for downloads"), True)
        self.check_file(self.config['general']['link_file'], _("file for links"))
        self.check_file(self.config['general']['failed_file'], _("file for failed links"))
        script_folders = ['scripts/download_preparing/', 'scripts/download_finished/', 'scripts/package_finished/', 'scripts/reconnected/']
        self.check_file(script_folders, _("folders for scripts"), True)
        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", "OpenSLL for secure connection", True)
            self.check_file(self.config['ssl']['cert'], _("ssl certificate"), False, True)
            self.check_file(self.config['ssl']['key'], _("ssl key"), False, True)

        if self.config['general']['debug_mode']:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level
            
        self.init_scripts()
        path.append(self.plugin_folder)
        self.create_plugin_index()

        self.server_methods = ServerMethods(self)
        self.file_list = File_List(self)
        self.thread_list = Thread_List(self)

        self.server_methods.check_update()

        self.init_server()
        self.init_webserver() # start webinterface like cli, gui etc


        self.logger.info(_("Downloadtime: %s") % self.server_methods.is_time_download()) # debug only

        #read url list @mkaay: pid, lid?
        linkFile = self.config['general']['link_file']
        pid = self.file_list.packager.addNewPackage(package_name=linkFile)
        lid = self.file_list.collector.addLink(linkFile)
        self.file_list.packager.addFileToPackage(pid, self.file_list.collector.popFile(lid))
        self.file_list.packager.pushPackage2Queue(pid)

        while True:
            sleep(2)
            if self.do_kill:
                self.logger.info("pyLoad quits")
                exit()

    def init_server(self):
        try:
            server_addr = (self.config['remote']['listenaddr'], int(self.config['remote']['port']))
            usermap = {self.config['remote']['username']: self.config['remote']['password']}
            if self.config['ssl']['activated']:
                self.server = Server.SecureXMLRPCServer(server_addr, self.config['ssl']['cert'], self.config['ssl']['key'], usermap)
                self.logger.info("Secure XMLRPC Server Started")
            else:
                self.server = Server.AuthXMLRPCServer(server_addr, usermap)
                self.logger.info("Auth XMLRPC Server Started")

            self.server.register_instance(self.server_methods)

            thread.start_new_thread(self.server.serve_forever, ())
        except Exception, e:
            self.logger.error("Failed starting socket server, CLI and GUI will not be available: %s" % str(e))
            if self.config['general']['debug_mode']:
                import traceback
                traceback.print_exc()

    
    def init_webserver(self):
        if self.config['webinterface']['activated']:
            self.webserver = WebServer(self)
            self.webserver.start()
        
    
    def init_logger(self, level):
        
        
        console = logging.StreamHandler(stdout)

        frm = logging.Formatter("%(asctime)s: %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")

        console.setFormatter(frm)

        self.logger = logging.getLogger("log") # settable in config

        if self.config['log']['file_log']:
            file_handler = logging.handlers.RotatingFileHandler(self.config['log']['log_folder'] + sep + 'log.txt', maxBytes=102400, backupCount=int(self.config['log']['log_count'])) #100 kib each
            file_handler.setFormatter(frm)
            self.logger.addHandler(file_handler)

        self.logger.addHandler(console) #if console logging
        self.logger.setLevel(level)


    def init_scripts(self):
        """ scan directory for scripts to execute"""
        f = lambda x: False if x.startswith("#") or x.endswith("~") else True
        self.scripts = {}
        #@TODO: windows save?!
        self.scripts['download_preparing'] = map(lambda x: 'scripts/download_preparing/' + x, filter(f, listdir('scripts/download_preparing')))
        self.scripts['download_finished'] = map(lambda x: 'scripts/download_finished/' + x, filter(f, listdir('scripts/download_finished')))
        self.scripts['package_finished'] = map(lambda x: 'scripts/package_finished/' + x, filter(f, listdir('scripts/package_finished')))
        self.scripts['reconnected'] = map(lambda x: 'scripts/reconnected/' + x, filter(f, listdir('scripts/reconnected')))

        for script_type, script_name in self.scripts.iteritems():
            if script_name != []:
                self.logger.info("Installed %s Scripts: %s" % (script_type, ", ".join(script_name)))

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

    def check_file(self, check_names, description="", folder=False, empty=True, essential=False):
        """check wether needed files are exists"""
        tmp_names = []
        if not type(check_names) == list:
            tmp_names.append(check_names)
        else:
            tmp_names.extend(check_names)
        file_created = True
        file_exists = True
        for tmp_name in tmp_names:
            if not exists(tmp_name):
                file_exists = False
                if empty:
                    try:
                        if folder:
                            tmp_name = tmp_name.replace("/", sep)
                            makedirs(tmp_name)
                        else:
                            open(tmp_name, "w")
                    except:
                        file_created = False
                else:
                    file_created = False
        if not file_exists:
            if file_created:
                print _("%s created") % description
            else:
                if not empty:
                    print _("could not find %s: %s") % (description, tmp_name)
                else:
                    print _("could not create %s: %s") % (description, tmp_name)
                if essential:
                    exit()

    def restart(self):
        pass

    #~ def update(self, file_update=None):
        #~ try:
            #~ if not file_update:
                #~ tmp_zip = __import__("tempfile").NamedTemporaryFile(suffix=".zip").name
                #~ file_update = Request().download("http://update.pyload.org/index.php?download=True", tmp_zip)
            #~ __import__("module.Unzip", globals(), locals(), "Unzip", -1).Unzip().extract(tmp_zip,"Test/")
            #~ self.logger.info(_("Updated pyLoad"))
        #~ except:
            #~ self.logger.info("Error on updating pyLoad")

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
        
    #~ def init_webserver(self):
        #~ self.webserver = WebServer(self)
        #~ if self.config['webinterface']['activated']:
            #~ self.webserver.start()
            
    ####################################
    ########## XMLRPC Methods ##########
    ####################################

class ServerMethods():
    def __init__(self, core):
        self.core = core

    def check_update(self):
        """checks newst version"""
        if self.core.config['updates']['search_updates']:
            version_check = Request().load("http://update.pyload.org/index.php?do=dev%s&download=%s" % (CURRENT_VERSION, self.core.config['updates']['install_updates']))
            if version_check == "":
                self.core.logger.info("No Updates for pyLoad")
                return False
            else:
                if self.core.config['updates']['install_updates']:
                    try:
                        tmp_zip_name = __import__("tempfile").NamedTemporaryFile(suffix=".zip").name
                        tmp_zip = open(tmp_zip_name, 'w')
                        tmp_zip.write(version_check)
                        tmp_zip.close()
                        __import__("module.Unzip", globals(), locals(), "Unzip", -1).Unzip().extract(tmp_zip_name, "Test/")
                        return True

                    except:
                        self.logger.core.info("Auto install Faild")
                        return False

                else:
                    self.core.logger.info("New pyLoad Version %s available" % version_check)
                    return True
        else:
            return False

    def status_downloads(self):
        downloads = []
        for pyfile in self.core.thread_list.py_downloading:
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
            return self.core.config[cat][var]
        else:
            raise Exception("not allowed!")
    
    def status_server(self):
        status = {}
        status['pause'] = self.core.thread_list.pause
        status['queue'] = len(self.core.file_list.data['queue'])
        status['speed'] = 0

        for pyfile in self.core.thread_list.py_downloading:
            status['speed'] += pyfile.status.get_speed()

        return status
    
    def file_exists(self, path): #@XXX: security?!
        return exists(path)
    
    def get_server_version(self):
        return CURRENT_VERSION
    
    def add_urls(self, links):
        for link in links:
            self.core.file_list.collector.addLink(link)
        self.core.file_list.save()
    
    def add_package(self, name, links):
        pid = self.new_package(name)
        self.core.file_list.packager.pushPackage2Queue(pid)
        fids = map(self.core.file_list.collector.addLink, links)
        map(lambda fid: self.move_file_2_package(fid, pid), fids)
        self.push_package_2_queue(pid)
    
    def new_package(self, name):
        id = self.core.file_list.packager.addNewPackage(name)
        self.core.file_list.save()
        return id
    
    def get_package_data(self, id):
        return self.core.file_list.packager.getPackageData(id)
    
    def get_package_files(self, id):
        return self.core.file_list.packager.getPackageFiles(id)
    
    def get_file_info(self, id):
        return self.core.file_list.getFileInfo(id)
    
    def del_links(self, ids):
        for id in ids:
            try:
                self.core.file_list.collector.removeFile(id)
            except:
                self.core.file_list.packages.removeFile(id)
        self.core.file_list.save()
    
    def del_packages(self, ids):
        for id in ids:
            self.core.file_list.packages.removePackage(id)
        self.core.file_list.save()
        
    def kill(self):
        self.core.do_kill = True
        return True
    
    def get_queue(self):
        data = []
        for q in self.core.file_list.data["queue"]:
            data.append(q.data)
        return data

    def get_collector_packages(self):
        data = []
        for q in self.core.file_list.data["packages"]:
            data.append(q.data)
        return data

    def get_collector_files(self):
        files = []
        for f in self.core.file_list.data["collector"]:
            files.append(f.id)
        return files
    
    def move_file_2_package(self, fid, pid):
        try:
            pyfile = self.core.file_list.collector.getFile(fid)
            self.core.file_list.packager.addFileToPackage(pid, pyfile)
        except:
            return
        else:
            self.core.file_list.collector.removeFile(fid)
    
    def push_package_2_queue(self, id):
        self.core.file_list.packager.pushPackage2Queue(id)

    #def move_urls_up(self, ids):
    #    for id in ids:
    #        self.core.file_list.move(id)
    #    self.core.file_list.save()

    #def move_urls_down(self, ids):
    #    for id in ids:
    #        self.core.file_list.move(id, 1)
    #    self.core.file_list.save()

    def is_time_download(self):
        start = self.core.config['downloadTime']['start'].split(":")
        end = self.core.config['downloadTime']['end'].split(":")
        return self.core.compare_time(start, end)

    def is_time_reconnect(self):
        start = self.core.config['reconnectTime']['start'].split(":")
        end = self.core.config['reconnectTime']['end'].split(":")
        return self.compare_time(start, end)

if __name__ == "__main__":
    pyload_core = Core()
    try:
        pyload_core.start()
    except KeyboardInterrupt:
        pyload_core.logger.info("killed pyLoad by Terminal")
        exit()
        
