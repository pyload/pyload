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
CURRENT_VERSION = '0.4.1'

from getopt import GetoptError
from getopt import getopt
import gettext
from imp import find_module
import logging
import logging.handlers
import os
from os import _exit
from os import execv
from os import getcwd
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
import thread
import time
from time import sleep
from traceback import print_exc
from xmlrpclib import Binary

from module import InitHomeDir
from module.AccountManager import AccountManager
from module.CaptchaManager import CaptchaManager
from module.ConfigParser import ConfigParser
from module.FileDatabase import FileHandler
from module.HookManager import HookManager
from module.PluginManager import PluginManager
from module.PullEvents import PullManager
from module.RequestFactory import RequestFactory
from module.ThreadManager import ThreadManager
import module.remote.SecureXMLRPCServer as Server
from module.web.ServerThread import WebServer
from module.FileDatabase import PyFile
from module.Scheduler import Scheduler

from codecs import getwriter
if os.name == "nt":
    enc = "cp850"
else:
    enc = "utf8"

sys.stdout = getwriter(enc)(sys.stdout, errors = "replace")

class Core(object):
    """ pyLoad Core """

    def __init__(self):
        self.doDebug = False
        self.arg_links = []

        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vca:hdus',
                                       ["version", "clear", "add=", "help", "debug", "user", "setup", "configdir"])

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
                    elif option == "--configdir":
                        from module.setup import Setup

                        self.config = ConfigParser()
                        s = Setup(pypath, self.config)
                        s.conf_path(True)
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
        #print "  -a, --add=<link/list>", " " * 2, "Add the specified links"
        print "  -u, --user", " " * 13, "Set new User and password"
        print "  -d, --debug", " " * 12, "Enable debug mode"
        print "  -s, --setup", " " * 12, "Run Setup Assistent"
        print "  --configdir", " " * 12, "Set new config directory"
        print "  -h, --help", " " * 13, "Display this help screen"
        print ""

    def toggle_pause(self):
        if self.threadManager.pause:
            self.threadManager.pause = False
            return False
        elif not self.threadManager.pause:
            self.threadManager.pause = True
            return True

    def quit(self, a, b):
        self.shutdown()
        self.log.info(_("Received Quit signal"))
        _exit(1)

    def start(self, xmlrpc=True, web=True):
        """ starts the fun :D """

        if not exists("pyload.conf"):
            from module.setup import Setup

            print "This is your first start, running configuration assistent now."
            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            try:
                res = s.start()
            except:
                res = False
                print_exc()
                print "Setup failed"
            if not res:
                remove("pyload.conf")

            exit()

        try: signal.signal(signal.SIGQUIT, self.quit)
        except: pass

        self.config = ConfigParser()

        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=["en", self.config['general']['language']])
        translation.install(True)

        self.debug = self.doDebug or self.config['general']['debug_mode']

        self.check_file(self.config['log']['log_folder'], _("folder for logs"), True)

        if self.debug:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level

        self.do_kill = False
        self.do_restart = False
        self.shuttedDown = False

        self.log.info(_("Using home directory: %s") % getcwd())

        #@TODO refractor

        self.check_install("Crypto", _("pycrypto to decode container files"))
        img = self.check_install("Image", _("Python Image Libary (PIL) for captcha reading"))
        self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_install("django", _("Django for webinterface"))
        self.check_file("tmp", _("folder for temporary files"), True)
        #tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False)

        self.captcha = img

        self.check_file(self.config['general']['download_folder'], _("folder for downloads"), True)
        self.check_file("links.txt", _("file for links"))

        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", _("OpenSSL for secure connection"), True)


        self.requestFactory = RequestFactory(self)

        #path.append(self.plugin_folder)

        self.lastClientConnected = 0

        self.server_methods = ServerMethods(self)

        self.scheduler = Scheduler(self)
        
        #hell yeah, so many important managers :D
        self.files = FileHandler(self)
        self.pluginManager = PluginManager(self)
        self.pullManager = PullManager(self)
        self.accountManager = AccountManager(self)
        self.threadManager = ThreadManager(self)
        self.captchaManager = CaptchaManager(self)
        self.hookManager = HookManager(self)

        self.log.info(_("Downloadtime: %s") % self.server_methods.is_time_download())

        if xmlrpc:
            self.init_server()
        if web:
            self.init_webserver()

        #linkFile = self.config['general']['link_file']

        freeSpace = self.freeSpace()
        if freeSpace > 5 * 1024:
            self.log.info(_("Free space: %sGB") % (freeSpace / 1024))
        else:
            self.log.info(_("Free space: %sMB") % freeSpace)

        self.threadManager.pause = False
        #self.threadManager.start()

        self.hookManager.coreReady()

        self.config.save() #save so config files gets filled

        link_file = join(pypath, "links.txt")

        if exists(link_file):
            f = open(link_file, "rb")
            links = [x.strip() for x in f.readlines() if x.strip()]
            if links:
                self.server_methods.add_package("links.txt", links, 1)
                f.close()
                try:
                    f = open(link_file, "wb")
                    f.close()
                except:
                    self.log.warning(_("links.txt could not be cleared"))

        link_file = "links.txt"
        if exists(link_file):
            f = open(link_file, "rb")
            links = [x.strip() for x in f.readlines() if x.strip()]
            if links:
                self.server_methods.add_package("links.txt", links, 1)
                f.close()
                f = open(link_file, "wb")
                f.close()
        
        #self.scheduler.start()
        self.scheduler.addJob(0, self.accountManager.cacheAccountInfos)
        
        while True:
            sleep(2)
            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                self.removeLogger()
                exit()

            self.threadManager.work()
            self.hookManager.periodical()

            try:
                j = self.scheduler.queue.get(False)
                j.start()
            except:
                pass

    def init_server(self):
        try:
            server_addr = (self.config['remote']['listenaddr'], int(self.config['remote']['port']))
            usermap = {self.config.username: self.config.password}
            if self.config['ssl']['activated']:
                if exists(self.config['ssl']['cert']) and exists(self.config['ssl']['key']):
                    self.server = Server.SecureXMLRPCServer(server_addr, self.config['ssl']['cert'],
                                                            self.config['ssl']['key'], usermap)
                    self.log.info(_("Secure XMLRPC Server Started"))
                else:
                    self.log.warning(_("SSL Certificates not found, fallback to auth XMLRPC server"))
                    self.server = Server.AuthXMLRPCServer(server_addr, usermap)
                    self.log.info(_("Auth XMLRPC Server Started"))
            else:
                self.server = Server.AuthXMLRPCServer(server_addr, usermap)
                self.log.info(_("Auth XMLRPC Server Started"))

            self.server.register_instance(self.server_methods)

            thread.start_new_thread(self.server.serve_forever, ())
        except Exception, e:
            self.log.error(_("Failed starting XMLRPC server CLI and GUI will not be available: %s") % str(e))
            if self.debug:
                print_exc()

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
            file_handler = logging.handlers.RotatingFileHandler(join(self.config['log']['log_folder'], 'log.txt'),
                                                                maxBytes=102400,
                                                                backupCount=int(self.config['log']['log_count']),
                                                                encoding="utf8"
                                                                ) #100 kib each
            file_handler.setFormatter(frm)
            self.log.addHandler(file_handler)

        self.log.addHandler(console) #if console logging
        self.log.setLevel(level)

    def removeLogger(self):
        for h in list(self.log.handlers):
            self.log.removeHandler(h)
            h.close()
    
    def check_install(self, check_name, legend, python=True, essential=False):
        """check wether needed tools are installed"""
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)

            return True
        except:
            if essential:
                self.log.info(_("Install %s") % legend)
                exit()

            return False

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
                        self.log.warning(_("could not find %(desc)s: %(name)s") % {"desc": description, "name": tmp_name})
                    else:
                        print _("could not create %(desc)s: %(name)s") % {"desc": description, "name": tmp_name}
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

        now = list(time.localtime()[3:5])
        if start < now and end > now: return True
        elif start > end and (now > start or now < end): return True
        elif start < now and end < now and start > end: return True
        else: return False


    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.config['webinterface']['activated'] and hasattr(self, "webserver"):
                self.webserver.quit()
            #self.webserver.join()
            for thread in self.threadManager.threads:
                thread.put("quit")
            pyfiles = self.files.cache.values()

            for pyfile in pyfiles:
                pyfile.abortDownload()

        except:
            if self.debug:
                print_exc()
            self.log.info(_("error while shutting down"))

        finally:
            self.files.syncSave()
            self.shuttedDown = True


    def path(self, * args):
        return join(pypath, * args)

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
        for pyfile in [x.active for x in self.core.threadManager.threads + self.core.threadManager.localThreads if
                       x.active and x.active != "quit"]:
            if not isinstance(pyfile, PyFile):
                continue
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

    def get_conf_val(self, cat, var, sec="core"):
        """ get config value """
        if sec == "core":
            return self.core.config[cat][var]
        elif sec == "plugin":
            return self.core.config.getPlugin(cat, var)

    def set_conf_val(self, cat, opt, val, sec="core"):
        """ set config value """
        if sec == "core":
            self.core.config[str(cat)][str(opt)] = val
        elif sec == "plugin":
            self.core.config.setPlugin(cat, opt, val)

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
        status['activ'] = len(self.core.threadManager.processingIds())
        status['queue'] = self.core.files.getFileCount()
        status['total'] = self.core.files.getFileCount()
        status['speed'] = 0

        for pyfile in [x.active for x in self.core.threadManager.threads if x.active and x.active != "quit"]:
            status['speed'] += pyfile.getSpeed()

        status['download'] = not self.core.threadManager.pause and self.is_time_download()
        status['reconnect'] = self.core.config['reconnect']['activated'] and self.is_time_reconnect()

        return status
    
    def free_space(self):
        return self.core.freeSpace()

    def get_server_version(self):
        return CURRENT_VERSION

    def add_package(self, name, links, queue=0):
    #0 is collector
        if self.core.config['general']['folder_per_package']:
            folder = name
        else:
            folder = ""

        folder = folder.replace("http://","").replace(":","").replace("/","_").replace("\\","_")

        pid = self.core.files.addPackage(name, folder, queue)

        self.core.files.addLinks(links, pid)

        self.core.log.info(_("Added package %(name)s containing %(count)d links") % {"name": name, "count": len(links)})

        self.core.files.save()

        return pid


    def get_package_data(self, id):
        return self.core.files.getPackageData(int(id))

    def get_file_data(self, id):
        info = self.core.files.getFileData(int(id))
        if not info:
            return None
        info = {str(info.keys()[0]): info[info.keys()[0]]}
        return info

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

    def get_queue_info(self):
        return self.core.files.getInfoData(1)

    def get_collector_info(self):
        return self.core.files.getInfoData(0)

    def add_files_to_package(self, pid, urls):
    #@TODO implement
        pass

    def push_package_to_queue(self, id):
        self.core.files.setPackageLocation(id, 1)

    def restart_package(self, packid):
        self.core.files.restartPackage(int(packid))

    def recheck_package(self, packid):
        self.core.files.reCheckPackage(int(packid))

    def restart_file(self, fileid):
        self.core.files.restartFile(int(fileid))

    def upload_container(self, filename, content):
        th = open(join(self.core.config["general"]["download_folder"], "tmp_" + filename), "wb")
        th.write(str(content))
        th.close()

        self.add_package(th.name, [th.name], 1)

    def get_log(self, offset=0):
        filename = join(self.core.config['log']['log_folder'], 'log.txt')
        try:
            fh = open(filename, "r")
            lines = fh.readlines()
            fh.close()
            if offset >= len(lines):
                return None
            return lines[offset:]
        except:
            return ('No log available', )

    def stop_downloads(self):
        pyfiles = self.core.files.cache.values()

        for pyfile in pyfiles:
            pyfile.abortDownload()

    def abort_files(self, fids):
        pyfiles = self.core.files.cache.values()

        for pyfile in pyfiles:
            if pyfile.id in fids:
                pyfile.abortDownload()

    def stop_download(self, type, id):
        if self.core.files.cache.has_key(id):
            self.core.files.cache[id].abortDownload()


    def set_package_name(self, pid, name):
        pack = self.core.files.getPackage(pid)
        pack.name = name
        pack.sync()

    def pull_out_package(self, pid):
        """put package back to collector"""
        self.core.files.setPackageLocation(pid, 0)

    def move_package(self, dest, pid):
        if dest not in (0,1): return
        self.core.files.setPackageLocation(pid, dest)

    def is_captcha_waiting(self):
        self.core.lastClientConnected = time.time()
        task = self.core.captchaManager.getTask()
        return not task is None

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
        return self.core.pullManager.getEvents(uuid)

    def get_accounts(self, refresh=False):
        return self.core.accountManager.getAccountInfos(force=refresh)

    def update_account(self, plugin, account, password, options=[]):
        """ create and update account """
        self.core.accountManager.updateAccount(plugin, account, password, options)

    def remove_account(self, plugin, account):
        self.core.accountManager.removeAccount(plugin, account)

    def set_priority(self, id, priority):
        p = self.core.files.getPackage(id)
        p.setPriority(priority)

    def order_package(self, id, pos):
        self.core.files.reorderPackage(id, pos)

    def order_file(self, id, pos):
        self.core.files.reorderFile(id, pos)

    def set_package_data(self, id, data):
        p = self.core.files.getPackage(id)
        if not p: return
        
        for key, value in data.iteritems():
            if key == "id": continue
            setattr(p, key, value)

        p.sync()
        self.core.files.save()

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
        pyload_core.removeLogger()
        _exit(1)
