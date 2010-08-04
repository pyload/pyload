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
    @version: v0.4.0
"""
CURRENT_VERSION = '0.4.0b'

from getopt import GetoptError
from getopt import getopt
import gettext
from imp import find_module
import logging
import logging.handlers
from os import _exit
from os import getcwd
from os import execv
from os import makedirs
from os import name as platform
from os import remove
from os import sep
from os.path import exists
from os.path import join
import signal
import subprocess
import sys
from sys import argv
from sys import executable
from sys import exit
from sys import stdout
from tempfile import NamedTemporaryFile
import thread
import time
from time import sleep
from xmlrpclib import Binary
from traceback import print_exc


from module import InitHomeDir

from module.ConfigParser import ConfigParser
import module.remote.SecureXMLRPCServer as Server
from module.web.ServerThread import WebServer

from module.ThreadManager import ThreadManager
from module.CaptchaManager import CaptchaManager
from module.HookManager import HookManager
from module.PullEvents import PullManager
from module.PluginManager import PluginManager
from module.FileDatabase import FileHandler
from module.RequestFactory import RequestFactory
from module.AccountManager import AccountManager

class Core(object):
    """ pyLoad Core """

    def __init__(self):
        self.doDebug = False
        self.arg_links = []


        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vca:hdusC:', ["version", "clear", "add=", "help", "debug", "user", "setup", "configdir="])

                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad", CURRENT_VERSION
                        exit()
                    elif option in ("-c", "--clear"):
                        try: 
                            remove("files.db")
                            print "Removed Linklist"
                        except:
                            print "No Linklist found"
                    elif option in ("-a", "--add"):
                        #self.arg_links.append(argument)
                        #@TODO
                        print "Added %s" % argument
                    elif option in ("-h", "--help"):
                        self.print_help()
                        exit()
                    elif option in ("-d", "--debug"):
                        self.doDebug = True
                    elif option in ("-u", "--user"):
                        from module.setup import Setup
                        self.config = ConfigParser()
                        s = Setup(pypath, self.config)
                        s.set_user()
                        exit()
                    elif option in ("-s", "--setup"):
                        from module.setup import Setup
                        self.config = ConfigParser()
                        s = Setup(pypath, self.config)
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
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -c, --clear", " " * 12, "Delete the saved linklist"
        print "  -a, --add=<link/list>", " " * 2, "Add the specified links"
        print "  -u, --user", " " * 13, "Set new User and password"
        print "  -d, --debug", " " * 12, "Enable debug mode"
        print "  -s, --setup", " " * 12, "Run Setup Assistent"
        print "  --configdir=<path>", " " * 5, "Custom config dir, (see config folder for permanent change)"
        print "  -h, --help", " " * 13, "Display this help screen"
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
        self.log.info(_("Received Quit signal"))
        _exit(1)

    def start(self):
        """ starts the fun :D """

        try: signal.signal(signal.SIGQUIT, self.quit)
        except: pass

        if not exists("pyload.conf"):
            from module.setup import Setup
            print "This is your first start, running configuration assistent now."
            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            s.start()
            exit()
        
        
        self.config = ConfigParser()
        
        translation = gettext.translation("pyLoad", self.path("locale"), languages=["en", self.config['general']['language']])
        translation.install(unicode=(True if sys.getfilesystemencoding().lower().startswith("utf") else False))
        
        self.debug = self.doDebug or self.config['general']['debug_mode']

        self.check_file(self.config['log']['log_folder'], _("folder for logs"), True)
        
        if self.debug:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level
        
        self.do_kill = False
        self.do_restart = False
        
        self.log.info(_("Using home directory: %s") % getcwd() )
        
        #@TODO refractor
        
        self.check_install("Crypto", _("pycrypto to decode container files"))
        self.check_install("Image", _("Python Image Libary (PIL) for captha reading"))
        self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_install("django", _("Django for webinterface"))
        self.check_install("tesseract", _("tesseract for captcha reading"), False)
        self.check_install("gocr", _("gocr for captcha reading"), False)

        self.check_file(self.config['general']['download_folder'], _("folder for downloads"), True)

        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", _("OpenSSL for secure connection"), True)


        self.downloadSpeedLimit = int(self.config.get("general", "download_speed_limit"))

        self.requestFactory = RequestFactory(self)

        #path.append(self.plugin_folder)

        self.lastClientConnected = 0

        self.server_methods = ServerMethods(self)

        #hell yeah, so many important managers :D
        self.files = FileHandler(self)
        self.pluginManager = PluginManager(self)
        self.pullManager = PullManager(self)
        self.accountManager = AccountManager(self)
        self.threadManager = ThreadManager(self)
        self.captchaManager = CaptchaManager(self)
        self.hookManager = HookManager(self)

        self.log.info(_("Downloadtime: %s") % self.server_methods.is_time_download())

        self.init_server()
        self.init_webserver()

        linkFile = self.config['general']['link_file']

        freeSpace = self.freeSpace()
        if freeSpace > 5 * 1024:
            self.log.info(_("Free space: %sGB") % (freeSpace / 1024))
        else:
            self.log.info(_("Free space: %sMB") % freeSpace)

        self.threadManager.pause = False
        #self.threadManager.start()

        self.hookManager.coreReady()
        
        while True:
                        
            sleep(2)
            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                exit()
                
            self.threadManager.work()
            self.hookManager.periodical()

    def init_server(self):
        try:
            server_addr = (self.config['remote']['listenaddr'], int(self.config['remote']['port']))
            usermap = {self.config.username: self.config.password}
            if self.config['ssl']['activated']:
                self.server = Server.SecureXMLRPCServer(server_addr, self.config['ssl']['cert'], self.config['ssl']['key'], usermap)
                self.log.info(_("Secure XMLRPC Server Started"))
            else:
                self.server = Server.AuthXMLRPCServer(server_addr, usermap)
                self.log.info(_("Auth XMLRPC Server Started"))

            self.server.register_instance(self.server_methods)

            thread.start_new_thread(self.server.serve_forever, ())
        except Exception, e:
            self.log.error(_("Failed starting XMLRPC server CLI and GUI will not be available: %s") % str(e))
            if self.debug:
                import traceback
                traceback.print_exc()

    def init_webserver(self):
        if self.config['webinterface']['activated']:
            self.webserver = WebServer(self)
            self.webserver.start()

    def init_logger(self, level):
        console = logging.StreamHandler(stdout)
        frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        console.setFormatter(frm)
        self.log = logging.getLogger("log") # settable in config

        if self.config['log']['file_log']:
            file_handler = logging.handlers.RotatingFileHandler(join(self.config['log']['log_folder'], 'log.txt'), maxBytes=102400, backupCount=int(self.config['log']['log_count'])) #100 kib each
            file_handler.setFormatter(frm)
            self.log.addHandler(file_handler)

        self.log.addHandler(console) #if console logging
        self.log.setLevel(level)

    def check_install(self, check_name, legend, python=True, essential=False):
        """check wether needed tools are installed"""
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)
        except:
            self.log.info( _("Install %s") % legend )
            if essential: exit()

    def check_file(self, check_names, description="", folder=False, empty=True, essential=False, quiet=False):
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
        if not file_exists and not quiet:
            if file_created:
                #self.log.info( _("%s created") % description )
                pass
            else:
                if not empty:
                    self.log.warning( _("could not find %s: %s") % (description, tmp_name) )
                else:
                    print _("could not create %s: %s") % (description, tmp_name)
                if essential:
                    exit()

    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time.time()

    def restart(self):
        self.shutdown()
        execv(executable, [executable, "pyLoadCore.py"])

    def compare_time(self, start, end):

        start = map(int, start)
        end = map(int, end)

        if start == end: return True

        now  = list(time.localtime()[3:5])
        if start < now and end > now: return True
        elif start > end and (now > start or now < end): return True
        elif start < now and end < now and start > end: return True
        else: return False


    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.config['webinterface']['activated']:
                self.webserver.quit()
                #self.webserver.join()
            for thread in self.threadManager.threads:
                thread.put("quit")
            pyfiles = self.files.cache.values()
            
            for pyfile in pyfiles:
                pyfile.abortDownload()
            
            
#            self.requestFactory.clean()
        except:
            if self.debug:
                print_exc()
            self.log.info(_("error while shutting down"))
        finally:
            self.files.syncSave()

    def path(self, *args):
        return join(pypath, *args)

    def freeSpace(self):
        folder = self.config['general']['download_folder']
        if platform == 'nt':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
            return free_bytes.value / 1024 / 1024 #megabyte
        else:
            from os import statvfs
            s = statvfs(folder)
            return s.f_bsize * s.f_bavail / 1024 / 1024 #megabyte


    ####################################
    ########## XMLRPC Methods ##########
    ####################################

class ServerMethods():
    """ methods that can be used by clients with xmlrpc connection"""
    def __init__(self, core):
        self.core = core

    def status_downloads(self):
        """ gives status about all files currently processed """
        downloads = []
        for pyfile in [x.active for x in self.core.threadManager.threads + self.core.threadManager.localThreads if x.active]:
            download = {}
            download['id'] = pyfile.id
            download['name'] = pyfile.name
            download['speed'] = pyfile.getSpeed()
            download['eta'] = pyfile.getETA()
            download['format_eta'] = pyfile.formatETA()
            download['kbleft'] = pyfile.getBytesLeft() #holded for backward comp.
            download['bleft'] = pyfile.getBytesLeft()
            download['size'] = pyfile.getSize()
            download['format_size'] = pyfile.formatSize()
            download['percent'] = pyfile.getPercent()
            download['status'] = pyfile.status
            download['statusmsg'] = pyfile.m.statusMsg[pyfile.status] 
            download['format_wait'] = pyfile.formatWait()
            download['wait_until'] = pyfile.waitUntil
            download['package'] = pyfile.package().name
            downloads.append(download)
        return downloads

    def get_conf_val(self, cat, var):
        """ get config value """
        return self.core.config[cat][var]

    def set_conf_val(self, cat, opt, val):
        """ set config value """
        self.core.config[str(cat)][str(opt)] = val
        
    def get_config(self):
        """ gets complete config """
        return self.core.config.config 

    def get_plugin_config(self):
        """ gets complete plugin config """
        return self.core.config.plugin

    def pause_server(self):
        self.core.threadManager.pause = True

    def unpause_server(self):
        self.core.threadManager.pause = False

    def toggle_pause(self):
        if self.core.threadManager.pause:
            self.core.threadManager.pause = False
        else:
            self.core.threadManager.pause = True
        return self.core.threadManager.pause

    def status_server(self):
        """ dict with current server status """
        status = {}
        status['pause'] = self.core.threadManager.pause
        status['activ'] = len([x.active for x in self.core.threadManager.threads if x.active])
        status['queue'] = self.core.files.getFileCount()
        status['total'] = self.core.files.getFileCount()
        status['speed'] = 0

        for pyfile in [x.active for x in self.core.threadManager.threads if x.active]:
            status['speed'] += pyfile.getSpeed()

        status['download'] = not self.core.threadManager.pause and self.is_time_download()
        status['reconnect'] = self.core.config['reconnect']['activated'] and self.is_time_reconnect()

        return status

    def get_server_version(self):
        return CURRENT_VERSION

    def add_package(self, name, links, queue=0):
        #0 is collector
        pid = self.core.files.addPackage(name, name, queue)

        self.core.files.addLinks(links, pid)
        
        self.core.log.info(_("Added package %s containing %s links") % (name, len(links) ) )
        
        self.core.files.save()


    def get_package_data(self, id):
        return self.core.files.getPackageData(int(id))

    def get_file_info(self, id):
        return self.core.file_list.getFileInfo(id)

    def del_links(self, ids):
        for id in ids:
            self.core.files.deleteLink(int(id))
        
        self.core.files.save()

    def del_packages(self, ids):
        
        for id in ids:
            self.core.files.deletePackage(int(id))
        
        self.core.files.save()

    def kill(self):
        self.core.do_kill = True
        return True

    def restart(self):
        self.core.do_restart = True

    def get_queue(self):
        return self.core.files.getCompleteData(1)

    def get_collector(self):
        return self.core.files.getCompleteData(0)

    def add_files_to_package(self, pid, urls):
        #@TODO implement
        pass

    def push_package_to_queue(self, id):
        #@TODO implement
        pass

    def restart_package(self, packid):
        self.core.files.restartPackage(int(packid))

    def restart_file(self, fileid):
        self.core.files.restartFile(int(fileid))

    def upload_container(self, filename, type, content):
        #@TODO py2.5 unproofed
        th = NamedTemporaryFile(mode="w", suffix="." + type, delete=False)
        th.write(str(content))
        path = th.name
        th.close()
        pid = self.core.file_list.packager.addNewPackage(filename)
        cid = self.core.file_list.collector.addLink(path)
        self.move_file_2_package(cid, pid)
        self.core.file_list.save()

    def get_log(self, offset=0):
        filename = join(self.core.config['log']['log_folder'], 'log.txt')
        fh = open(filename, "r")
        lines = fh.readlines()
        fh.close()
        lines.reverse()
        if offset >= len(lines):
            return None

        return lines[offset:]

    def stop_downloads(self):
        pyfiles = self.files.cache.values()
            
        for pyfile in pyfiles:
            pyfile.abortDownload()

    def stop_download(self, type, id):
        if self.core.files.cache.has_key(id):
            self.core.files.cache[id].abortDownload()


    def set_package_name(self, pid, name):
        #@TODO
        self.core.file_list.packager.setPackageData(pid, package_name=name)

    def pull_out_package(self, pid):
        """put package back to collector"""
        #@TODO implement
        pass

    def is_captcha_waiting(self):
        self.core.lastClientConnected = time.time()
        task = self.core.captchaManager.getTask()
        return not task == None

    def get_captcha_task(self, exclusive=False):
        self.core.lastClientConnected = time.time()
        task = self.core.captchaManager.getTask()
        if task:
            task.setWatingForUser(exclusive=exclusive)
            c = task.getCaptcha()
            return str(task.getID()), Binary(c[0]), str(c[1])
        else:
            return None, None, None

    def get_task_status(self, tid):
        self.core.lastClientConnected = time.time()
        return self.core.captchaManager.getTaskFromID(tid).getStatus()

    def set_captcha_result(self, tid, result):
        self.core.lastClientConnected = time.time()
        task = self.core.captchaManager.getTaskFromID(tid)
        if task:
            task.setResult(result)
            task.setDone()
            return True
        else:
            return False

    def get_events(self, uuid):
        #@TODO
        return self.core.pullManager.getEvents(uuid)

    def get_premium_accounts(self):
        #@TODO implement
        plugins = self.core.pluginManager.getAccountPlugins()
        data = []
        for p in plugins:
            data.extend(p.getAllAccounts())
        return data

    
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
        pyload_core.log.info(_("killed pyLoad from Terminal"))
        _exit(1)
