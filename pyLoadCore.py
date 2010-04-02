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
    @version: v0.3.2
"""
CURRENT_VERSION = '0.3.2'

from copy import deepcopy
from getopt import GetoptError
from getopt import getopt
import gettext
from glob import glob
from imp import find_module
import logging
import logging.handlers
from operator import attrgetter
from os import _exit
from os import chdir
from os import execv
from os import makedirs
from os import name as platform
from os import remove
from os import sep
from os import statvfs
from os.path import abspath
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isabs
from os.path import join
from re import sub
import signal
import subprocess
import sys
from sys import argv
from sys import executable
from sys import exit
from sys import path
from sys import stdout
from sys import version_info
from tempfile import NamedTemporaryFile
import thread
import time
from time import sleep
from xmlrpclib import Binary

from module.CaptchaManager import CaptchaManager
from module.HookManager import HookManager
from module.PullEvents import PullManager
from module.XMLConfigParser import XMLConfigParser
from module.file_list import File_List
from module.network.Request import getURL
import module.remote.SecureXMLRPCServer as Server
from module.thread_list import Thread_List
from module.web.ServerThread import WebServer

class Core(object):
    """ pyLoad Core """

    def __init__(self):
        self.doDebug = False
        self.arg_links = []
        self.path = abspath(dirname(__file__))
        chdir(self.path)

        #check if no config exists, assume its first run
        if not exists(join(self.path, "module", "config", "core.xml")):
            print "No configuration file found."
            print "Startig Configuration Assistent"
            print ""
            
            from module.setup import Setup
            self.xmlconfig = XMLConfigParser(self.make_path("module", "config", "core.xml"))
            self.config = self.xmlconfig.getConfig()

            s = Setup(self.path, self.config)
            try:
                result = s.start()
                if not result:
                    remove(join(self.path, "module", "config", "core.xml"))
            except Exception, e:
                print e
                remove(join(self.path, "module", "config", "core.xml"))

            exit()

        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vca:hdus', ["version", "clear", "add=", "help", "debug", "user", "setup"])
                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad", CURRENT_VERSION
                        exit()
                    elif option in ("-c", "--clear"):
                        try: 
                            remove(join("module", "links.pkl"))
                            print "Removed Linklist"
                        except:
                            print "No Linklist found"
                    elif option in ("-a", "--add"):
                        self.arg_links.append(argument)
                        print "Added %s" % argument
                    elif option in ("-h", "--help"):
                        self.print_help()
                        exit()
                    elif option in ("-d", "--debug"):
                        self.doDebug = True
                    elif option in ("-u", "--user"):
                        from module.setup import Setup
                        self.xmlconfig = XMLConfigParser(self.make_path("module", "config", "core.xml"))
                        self.config = self.xmlconfig.getConfig()
                        s = Setup(self.path, self.config)
                        s.set_user()
                        exit()
                    elif option in ("-s", "--setup"):
                        from module.setup import Setup
                        self.xmlconfig = XMLConfigParser(self.make_path("module", "config", "core.xml"))
                        self.config = self.xmlconfig.getConfig()
                        s = Setup(self.path, self.config)
                        s.start()
                        exit()

            except GetoptError:
                print 'Unknown Argument(s) "%s"' % " ".join(argv[1:])
                self.print_help()
                exit()

    def print_help(self):
        print ""
        print "pyLoad %s  Copyright (c) 2008-2010 the pyLoad Team" % CURRENT_VERSION
        print ""
        print "Usage: [python] pyLoadCore.py [options]"
        print ""
        print "<Options>"
        print "  -v, --version", " " * 9, "Print version to terminal"
        print "  -c, --clear", " " * 11, "Delete the saved linklist"
        print "  -a, --add=<link/list>", " " * 1, "Add the specified links"
        print "  -u, --user", " " * 12, "Set new User and password"
        print "  -d, --debug", " " * 11, "Enable debug mode"
        print "  -s, --setup", " " * 11, "Run Setup Assistent"
        print "  -h, --help", " " * 12, "Display this help screen"
        print ""

    def toggle_pause(self):
        if self.thread_list.pause:
            self.thread_list.pause = False
            return False
        elif not self.thread_list.pause:
            self.thread_list.pause = True
            return True

    def quit(self, a, b):
        self.shutdown()
        self.logger.info(_("Received Quit signal"))
        _exit(1)

    def start(self):
        """ starts the machine"""

        try: signal.signal(signal.SIGQUIT, self.quit)
        except: pass
  
        self.config = {}
        self.plugins_avaible = {}

        self.plugin_folder = self.make_path("module", "plugins")

        self.xmlconfig = XMLConfigParser(self.make_path("module", "config", "core.xml"))
        self.config = self.xmlconfig.getConfig()
        if self.doDebug == True:
            self.config['general']['debug_mode'] = True
        self.parser_plugins = XMLConfigParser(self.make_path("module", "config", "plugin.xml"))

        self.config['ssl']['cert'] = self.make_path(self.config['ssl']['cert'])
        self.config['ssl']['key'] = self.make_path(self.config['ssl']['key'])

        self.do_kill = False
        self.do_restart = False
        translation = gettext.translation("pyLoad", self.make_path("locale"), languages=[self.config['general']['language']])
        translation.install(unicode=(True if sys.getfilesystemencoding().lower().startswith("utf") else False))
        
        self.check_install("Crypto", _("pycrypto to decode container files"))
        self.check_install("Image", _("Python Image Libary (PIL) for captha reading"))
        self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_install("django", _("Django for webinterface"))
        self.check_install("tesseract", _("tesseract for captcha reading"), False)
        self.check_install("gocr", _("gocr for captcha reading"), False)
        
        self.check_file(self.make_path(self.config['log']['log_folder']), _("folder for logs"), True)
        self.check_file(self.make_path(self.config['general']['download_folder']), _("folder for downloads"), True)
        self.check_file(self.make_path(self.config['general']['link_file']), _("file for links"))
        self.check_file(self.make_path(self.config['general']['failed_file']), _("file for failed links"))
        
        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", _("OpenSSL for secure connection"), True)
            self.check_file(self.make_path(self.config['ssl']['cert']), _("ssl certificate"), False, True)
            self.check_file(self.make_path(self.config['ssl']['key']), _("ssl key"), False, True)
        
        self.downloadSpeedLimit = int(self.xmlconfig.get("general", "download_speed_limit", 0))

        if self.config['general']['debug_mode']:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level
            
        self.init_hooks()
        path.append(self.plugin_folder)
        self.create_plugin_index()
        
        self.lastGuiConnected = 0
        
        self.server_methods = ServerMethods(self)
        self.file_list = File_List(self)
        self.pullManager = PullManager(self)
        self.thread_list = Thread_List(self)
        self.captchaManager = CaptchaManager(self)
        
        self.last_update_check = 0
        self.update_check_interval = 6 * 60 * 60
        self.update_available = self.check_update()
        self.logger.info(_("Downloadtime: %s") % self.server_methods.is_time_download())

        self.init_server()
        self.init_webserver()

        linkFile = self.config['general']['link_file']
        
        packs = self.server_methods.get_queue()
        found = False
        for data in packs:
            if data["package_name"] == linkFile:
                found = data["id"]
                break
        if found == False:
            pid = self.file_list.packager.addNewPackage(package_name=linkFile)
        else:
            pid = found
        lid = self.file_list.collector.addLink(linkFile)
        try:
            self.file_list.packager.addFileToPackage(pid, self.file_list.collector.popFile(lid))
            if self.arg_links:
                for link in self.arg_links:
                    lid = self.file_list.collector.addLink(link)
                    self.file_list.packager.addFileToPackage(pid, self.file_list.collector.popFile(lid))

            self.file_list.packager.pushPackage2Queue(pid)
            self.file_list.continueAborted()
        except:
            pass

        freeSpace = self.freeSpace()
        if freeSpace > 10000:
            self.logger.info(_("Free space: %sGB") % (freeSpace / 1000))
        else:
            self.logger.info(_("Free space: %sMB") % self.freeSpace())

        self.thread_list.pause = False

        while True:
            sleep(2)
            if self.do_restart:
                self.logger.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.logger.info(_("pyLoad quits"))
                exit()
            if self.last_update_check + self.update_check_interval <= time.time():
                self.update_available = self.check_update()

    def init_server(self):
        try:
            server_addr = (self.config['remote']['listenaddr'], int(self.config['remote']['port']))
            usermap = {self.config['remote']['username']: self.config['remote']['password']}
            if self.config['ssl']['activated']:
                self.server = Server.SecureXMLRPCServer(server_addr, self.config['ssl']['cert'], self.config['ssl']['key'], usermap)
                self.logger.info(_("Secure XMLRPC Server Started"))
            else:
                self.server = Server.AuthXMLRPCServer(server_addr, usermap)
                self.logger.info(_("Auth XMLRPC Server Started"))

            self.server.register_instance(self.server_methods)

            thread.start_new_thread(self.server.serve_forever, ())
        except Exception, e:
            self.logger.error(_("Failed starting XMLRPC server CLI and GUI will not be available: %s") % str(e))
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
            file_handler = logging.handlers.RotatingFileHandler(join(self.path, self.config['log']['log_folder'], 'log.txt'), maxBytes=102400, backupCount=int(self.config['log']['log_count'])) #100 kib each
            file_handler.setFormatter(frm)
            self.logger.addHandler(file_handler)

        self.logger.addHandler(console) #if console logging
        self.logger.setLevel(level)

    def init_hooks(self):
        self.hookManager = HookManager(self)

    def check_install(self, check_name, legend, python=True, essential=False):
        """check wether needed tools are installed"""
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)
        except:
            print _("Install %s") % legend
            if essential: exit()

    def check_file(self, check_names, description="", folder=False, empty=True, essential=False):
        """check wether needed files exists"""
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
    
    def isGUIConnected(self):
        return self.lastGuiConnected + 10 > time.time()
    
    def restart(self):
        self.shutdown()
        execv(executable, [executable, "pyLoadCore.py"])

    def create_plugin_index(self):
        plugins = glob(join(self.plugin_folder, "hoster", "*.py"))
        plugins += glob(join(self.plugin_folder, "decrypter", "*.py"))
        plugins += glob(join(self.plugin_folder, "container", "*.py"))
        plugins += glob(join(self.plugin_folder, "container", "DLC_*.pyc"))
        for file_handler in  plugins:
            plugin_pattern = ""
            plugin_file = sub("(\.pyc|\.py)", "", basename(file_handler))
            if plugin_file.startswith("DLC"):
                if plugin_file == "DLC_25" and not version_info < (2, 6):
                    continue
                if plugin_file == "DLC_26" and not version_info > (2, 6):
                    continue
                plugin_pattern = "(?!http://).*\.dlc"
            else:
                for line in open(file_handler, "r").readlines():
                    if "props['pattern']" in line:
                        plugin_pattern = line.split("r\"")[1].split("\"")[0]
                        break
            if plugin_pattern != "":
                self.plugins_avaible[plugin_file] = plugin_pattern
                self.logger.debug(_("%s added") % plugin_file)
        self.logger.info(_("created index of plugins"))

    def compare_time(self, start, end):
        
        start = map(int, start)
        end = map(int, end)
        
        if start == end: return True

        now  = list(time.localtime()[3:5])
        if start < now and end > now: return True
        elif start > end and (now > start or now < end): return True
        elif start < now and end < now and start > end: return True
        else: return False
    
    def getMaxSpeed(self):
        return self.downloadSpeedLimit
    
    def shutdown(self):
        self.logger.info(_("shutting down..."))
        try:
            if self.config['webinterface']['activated']:
                self.webserver.quit()
                #self.webserver.join()
            for thread in self.thread_list.threads:
                thread.shutdown = True
            self.thread_list.stopAllDownloads()
            for thread in self.thread_list.threads:
                thread.join(10)
            self.file_list.save()
        except:
            self.logger.info(_("error when shutting down"))

    def check_update(self):
        try:
            if self.config['updates']['search_updates']:
                version_check = getURL("http://get.pyload.org/check/%s/" % (CURRENT_VERSION,))
                if version_check == "":
                    self.logger.info(_("No Updates for pyLoad"))
                    return False
                else:
                    self.logger.info(_("New pyLoad Version %s available") % version_check)
                    return True
            else:
                return False
        except:
            pass
        finally:
            self.last_update_check = time.time()

    def install_update(self):
        try:
            if self.config['updates']['search_updates']:
                if self.core.config['updates']['install_updates']:
                    version_check = getURL("http://get.pyload.org/get/update/%s/" % (CURRENT_VERSION,))
                else:
                    version_check = getURL("http://get.pyload.org/check/%s/" % (CURRENT_VERSION,))
                if version_check == "":
                    return False
                else:
                    if self.config['updates']['install_updates']:
                        try:
                            tmp_zip_name = __import__("tempfile").NamedTemporaryFile(suffix=".zip").name
                            tmp_zip = open(tmp_zip_name, 'wb')
                            tmp_zip.write(version_check)
                            tmp_zip.close()
                            __import__("module.Unzip", globals(), locals(), "Unzip", -1).Unzip().extract(tmp_zip_name, "Test/")
                            return True
                        except:
                            self.logger.info(_("Auto install Failed"))
                            return False
                    else:
                        return False
            else:
                return False
        finally:
            return False

    def make_path(self, * args):
        if isabs(args[0]):
            return args[0]
        else:
            return join(self.path, * args)
    
    def freeSpace(self):
        folder = self.make_path(self.config['general']['download_folder'])
        if platform == 'nt':
            free_bytes = ctypes.c_ulonglong(0)
            __import__("ctypes").windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
            return free_bytes.value / 1024 / 1024 #megabyte
        else:
            s = statvfs(folder)
            return s.f_bsize * s.f_bavail / 1024 / 1024 #megabyte
        
    ####################################
    ########## XMLRPC Methods ##########
    ####################################

class ServerMethods():
    def __init__(self, core):
        self.core = core

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
            download['package'] = pyfile.package.data["package_name"]
            downloads.append(download)
        return downloads
    
    def get_conf_val(self, cat, var):
        if var != "username" and var != "password":
            return self.core.config[cat][var]
        else:
            raise Exception("not allowed!")
    
    def get_config(self):
        d = deepcopy(self.core.xmlconfig.getConfigDict())
        del d["remote"]["username"]
        del d["remote"]["password"]
        return d
    
    def get_config_data(self):
        d = deepcopy(self.core.xmlconfig.getDataDict())
        del d["remote"]["options"]["username"]
        del d["remote"]["options"]["password"]
        return d
        
    def pause_server(self):
        self.core.thread_list.pause = True
        
    def unpause_server(self):
        self.core.thread_list.pause = False
    
    def toggle_pause(self):
        if self.core.thread_list.pause:
            self.core.thread_list.pause = False
        else:
            self.core.thread_list.pause = True
        return self.core.thread_list.pause
    
    def status_server(self):
        status = {}
        status['pause'] = self.core.thread_list.pause
        status['activ'] = len(self.core.thread_list.py_downloading)
        status['queue'] = self.core.file_list.countDownloads()
        status['total'] = len(self.core.file_list.data['queue'])
        status['speed'] = 0

        for pyfile in self.core.thread_list.py_downloading:
            status['speed'] += pyfile.status.get_speed()

        status['download'] = not self.core.thread_list.pause and self.is_time_download()
        status['reconnect'] = self.core.config['reconnect']['activated'] and self.is_time_reconnect()

        return status
    
    def file_exists(self, path): #@XXX: security?!
        return exists(path)
    
    def get_server_version(self):
        return CURRENT_VERSION
    
    def add_urls(self, links):
        for link in links:
            link = link.strip()
            if link.startswith("http") or exists(link):
                self.core.file_list.collector.addLink(link)
        self.core.file_list.save()
    
    def add_package(self, name, links, queue=True):
        pid = self.new_package(name)

        fids = map(self.core.file_list.collector.addLink, links)
        map(lambda fid: self.move_file_2_package(fid, pid), fids)
        
        if queue:
            self.core.file_list.packager.pushPackage2Queue(pid)
        
        self.core.file_list.save()
    
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
                self.core.file_list.packager.removeFile(id)
        self.core.file_list.save()
    
    def del_packages(self, ids):
        map(self.core.file_list.packager.removePackage, ids)
        self.core.file_list.save()
        
    def kill(self):
        self.core.do_kill = True
        return True
        
    def restart(self):
        self.core.do_restart = True
    
    def get_queue(self):
        return map(attrgetter("data"), self.core.file_list.data["queue"])

    def get_collector_packages(self):
        return map(attrgetter("data"), self.core.file_list.data["packages"])

    def get_collector_files(self):
        return map(attrgetter("id"), self.core.file_list.data["collector"])
    
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
    
    def restart_package(self, packid):
        map(self.core.file_list.packager.resetFileStatus, self.core.file_list.packager.getPackageFiles(packid))
    
    def restart_file(self, fileid):
        self.core.file_list.packager.resetFileStatus(fileid)
    
    def upload_container(self, filename, type, content):
        th = NamedTemporaryFile(mode="w", suffix="." + type, delete=False)
        th.write(content)
        path = th.name
        th.close()
        pid = self.core.file_list.packager.addNewPackage(filename)
        cid = self.core.file_list.collector.addLink(path)
        self.move_file_2_package(cid, pid)
        self.core.file_list.save()
    
    def get_log(self, offset=0):
        filename = self.core.config['log']['log_folder'] + sep + 'log.txt'
        fh = open(filename, "r")
        content = fh.read()
        fh.close()
        lines = content.splitlines()
        if offset >= len(lines):
            return None
        return lines[offset:]
    
    def stop_downloads(self):
        self.core.thread_list.stopAllDownloads()
    
    def stop_download(self, type, id):
        if type == "pack":
            ids = self.core.file_list.getPackageFiles(id)
            for fid in ids:
                self.core.file_list.packager.abortFile(fid)
        else:
            self.core.file_list.packager.abortFile(id)
    
    def update_available(self):
        return self.core.update_available
    
    def set_package_name(self, pid, name):
        self.core.file_list.packager.setPackageData(pid, package_name=name)
    
    def pull_out_package(self, pid):
        self.core.file_list.packager.pullOutPackage(pid)
    
    def is_captcha_waiting(self):
        self.core.lastGuiConnected = time.time()
        task = self.core.captchaManager.getTask()
        return not task == None
    
    def get_captcha_task(self):
        task = self.core.captchaManager.getTask()
        if task:
            task.setWatingForUser()
            c = task.getCaptcha()
            return str(task.getID()), Binary(c[0]), str(c[1])
        else:
            return None, None, None
    
    def set_captcha_result(self, tid, result):
        task = self.core.captchaManager.getTaskFromID(tid)
        if task:
            task.setResult(result)
            task.setDone()
            return True
        else:
            return False
    
    def get_events(self, uuid):
        return self.core.pullManager.getEvents(uuid)
    
    def get_full_queue(self):
        data = []
        for pack in self.core.file_list.data["queue"]:
            p = {"data":pack.data, "children":[]}
            for child in pack.files:
                info = self.core.file_list.getFileInfo(child.id)
                info["downloading"] = None
                p["children"].append(info)
            data.append(p)
        return data
    
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
        start = self.core.config['reconnect']['startTime'].split(":")
        end = self.core.config['reconnect']['endTime'].split(":")
        return self.core.compare_time(start, end)

# And so it begins...
if __name__ == "__main__":
    pyload_core = Core()
    try:
        pyload_core.start()
    except KeyboardInterrupt:
        pyload_core.shutdown()
        pyload_core.logger.info(_("killed pyLoad from Terminal"))
        _exit(1)
