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
    @version: v0.4.9
"""
CURRENT_VERSION = '0.4.9'

import __builtin__

from getopt import getopt, GetoptError
import module.common.pylgettext as gettext
from imp import find_module
import logging
import logging.handlers
import os
from os import _exit, execl, getcwd, makedirs, remove, sep, walk, chdir, close
from os.path import exists, join
import signal
import subprocess
import sys
from sys import argv, executable, exit
from time import time, sleep
from traceback import print_exc

from module import InitHomeDir
from module.plugins.AccountManager import AccountManager
from module.CaptchaManager import CaptchaManager
from module.ConfigParser import ConfigParser
from module.plugins.PluginManager import PluginManager
from module.PullEvents import PullManager
from module.network.RequestFactory import RequestFactory
from module.web.ServerThread import WebServer
from module.Scheduler import Scheduler
from module.common.JsEngine import JsEngine
from module import remote
from module.remote.RemoteManager import RemoteManager
from module.database import DatabaseBackend, FileHandler

from module.utils import freeSpace, formatSize, get_console_encoding

from codecs import getwriter

enc = get_console_encoding(sys.stdout.encoding)
sys.stdout = getwriter(enc)(sys.stdout, errors="replace")

# TODO List
# - configurable auth system ldap/mysql
# - cron job like sheduler

class Core(object):
    """pyLoad Core, one tool to rule them all... (the filehosters) :D"""

    def __init__(self):
        self.doDebug = False
        self.startedInGui = False
        self.running = False
        self.daemon = False
        self.remote = True
        self.arg_links = []
        self.pidfile = "pyload.pid"
        self.deleteLinks = False # will delete links on startup

        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vchdusqp:',
                    ["version", "clear", "clean", "help", "debug", "user",
                     "setup", "configdir=", "changedir", "daemon",
                     "quit", "status", "no-remote","pidfile="])

                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad", CURRENT_VERSION
                        exit()
                    elif option in ("-p", "--pidfile"):
                        self.pidfile = argument
                    elif option == "--daemon":
                        self.daemon = True
                    elif option in ("-c", "--clear"):
                        self.deleteLinks = True
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
                    elif option == "--changedir":
                        from module.setup import Setup

                        self.config = ConfigParser()
                        s = Setup(pypath, self.config)
                        s.conf_path(True)
                        exit()
                    elif option in ("-q", "--quit"):
                        self.quitInstance()
                        exit()
                    elif option == "--status":
                        pid = self.isAlreadyRunning()
                        if self.isAlreadyRunning():
                            print pid
                            exit(0)
                        else:
			    print "false"
                            exit(1)
                    elif option == "--clean":
                        self.cleanTree()
                        exit()
                    elif option == "--no-remote":
                        self.remote = False

            except GetoptError:
                print 'Unknown Argument(s) "%s"' % " ".join(argv[1:])
                self.print_help()
                exit()

    def print_help(self):
        print ""
        print "pyLoad v%s     2008-2011 the pyLoad Team" % CURRENT_VERSION
        print ""
        if sys.argv[0].endswith(".py"):
            print "Usage: python pyLoadCore.py [options]"
        else:
            print "Usage: pyLoadCore [options]"
        print ""
        print "<Options>"
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -c, --clear", " " * 12, "Delete all saved packages/links"
        #print "  -a, --add=<link/list>", " " * 2, "Add the specified links"
        print "  -u, --user", " " * 13, "Manages users"
        print "  -d, --debug", " " * 12, "Enable debug mode"
        print "  -s, --setup", " " * 12, "Run Setup Assistent"
        print "  --configdir=<dir>", " " * 6, "Run with <dir> as config directory"
        print "  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>"
        print "  --changedir", " " * 12, "Change config dir permanently"
        print "  --daemon", " " * 15, "Daemonmize after start"
        print "  --no-remote", " " * 12, "Disable remote access (saves RAM)"
        print "  --status", " " * 15, "Display pid if running or False"
        print "  --clean", " " * 16, "Remove .pyc/.pyo files"
        print "  -q, --quit", " " * 13, "Quit running pyLoad instance"
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

    def writePidFile(self):
        self.deletePidFile()
        pid = os.getpid()
        f = open(self.pidfile, "wb")
        f.write(str(pid))
        f.close()

    def deletePidFile(self):
        if self.checkPidFile():
            self.log.debug("Deleting old pidfile %s" % self.pidfile)
            os.remove(self.pidfile)

    def checkPidFile(self):
        """ return pid as int or 0"""
        if os.path.isfile(self.pidfile):
            f = open(self.pidfile, "rb")
            pid = f.read().strip()
            f.close()
            if pid:
                pid = int(pid)
                return pid

        return 0

    def isAlreadyRunning(self):
        pid = self.checkPidFile()
        if not pid or os.name == "nt": return False
        try:
            os.kill(pid, 0)  # 0 - default signal (does nothing)
        except:
            return 0

        return pid

    def quitInstance(self):
        if os.name == "nt":
            print "Not supported on windows."
            return

        pid = self.isAlreadyRunning()
        if not pid:
            print "No pyLoad running."
            return

        try:
            os.kill(pid, 3) #SIGUIT

            t = time()
            print "waiting for pyLoad to quit"

            while exists(self.pidfile) and t + 10 > time():
                sleep(0.25)

            if not exists(self.pidfile):
                print "pyLoad successfully stopped"
            else:
                os.kill(pid, 9) #SIGKILL
                print "pyLoad did not respond"
                print "Kill signal was send to process with id %s" % pid

        except:
            print "Error quitting pyLoad"


    def cleanTree(self):
        for path, dirs, files in walk(self.path("")):
            for f in files:
                if not f.endswith(".pyo") and not f.endswith(".pyc"):
                    continue

                if "_25" in f or "_26" in f or "_27" in f:
                    continue

                print join(path, f)
                remove(join(path, f))

    def start(self, rpc=True, web=True):
        """ starts the fun :D """

        self.version = CURRENT_VERSION

        if not exists("pyload.conf"):
            from module.setup import Setup

            print "This is your first start, running configuration assistent now."
            self.config = ConfigParser()
            s = Setup(pypath, self.config)
            res = False
            try:
                res = s.start()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print "\nSetup interrupted"
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

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=[self.config['general']['language'],"en"],fallback=True)
        translation.install(True)

        self.debug = self.doDebug or self.config['general']['debug_mode']
        self.remote &= self.config['remote']['activated']

        pid = self.isAlreadyRunning()
        if pid:
            print _("pyLoad already running with pid %s") % pid
            exit()

        if os.name != "nt" and self.config["general"]["renice"]:
            os.system("renice %d %d" % (self.config["general"]["renice"], os.getpid()))

        if self.config["permission"]["change_group"]:
            if os.name != "nt":
                try:
                    from grp import getgrnam

                    group = getgrnam(self.config["permission"]["group"])
                    os.setgid(group[2])
                except Exception, e:
                    print _("Failed changing group: %s") % e

        if self.config["permission"]["change_user"]:
            if os.name != "nt":
                try:
                    from pwd import getpwnam

                    user = getpwnam(self.config["permission"]["user"])
                    os.setuid(user[2])
                except Exception, e:
                    print _("Failed changing user: %s") % e

        self.check_file(self.config['log']['log_folder'], _("folder for logs"), True)

        if self.debug:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level

        self.do_kill = False
        self.do_restart = False
        self.shuttedDown = False

        self.log.info(_("Starting") + " pyLoad %s" % CURRENT_VERSION)
        self.log.info(_("Using home directory: %s") % getcwd())

        self.writePidFile()

        #@TODO refractor

        remote.activated = self.remote
        self.log.debug("Remote activated: %s" % self.remote)

        self.check_install("Crypto", _("pycrypto to decode container files"))
        #img = self.check_install("Image", _("Python Image Libary (PIL) for captcha reading"))
        #self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_file("tmp", _("folder for temporary files"), True)
        #tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False) if os.name != "nt" else True

        self.captcha = True # checks seems to fail, althoug tesseract is available

        self.check_file(self.config['general']['download_folder'], _("folder for downloads"), True)

        if self.config['ssl']['activated']:
            self.check_install("OpenSSL", _("OpenSSL for secure connection"))

        self.setupDB()
        if self.config.oldRemoteData:
            self.log.info(_("Moving old user config to DB"))
            self.db.addUser(self.config.oldRemoteData["username"], self.config.oldRemoteData["password"])

            self.log.info(_("Please check your logindata with ./pyLoadCore.py -u"))

        if self.deleteLinks:
            self.log.info(_("All links removed"))
            self.db.purgeLinks()

        self.requestFactory = RequestFactory(self)
        __builtin__.pyreq = self.requestFactory

        self.lastClientConnected = 0

        # later imported because they would trigger api import, and remote value not set correctly
        from module import Api
        from module.HookManager import HookManager
        from module.ThreadManager import ThreadManager

        if Api.activated != self.remote:
            self.log.warning("Import error: API remote status not correct.")

        self.api = Api.Api(self)

        self.scheduler = Scheduler(self)

        #hell yeah, so many important managers :D
        self.pluginManager = PluginManager(self)
        self.pullManager = PullManager(self)
        self.accountManager = AccountManager(self)
        self.threadManager = ThreadManager(self)
        self.captchaManager = CaptchaManager(self)
        self.hookManager = HookManager(self)
        self.remoteManager = RemoteManager(self)

        self.js = JsEngine()

        self.log.info(_("Downloadtime: %s") % self.api.isTimeDownload())

        if rpc:
            self.remoteManager.startBackends()

        if web:
            self.init_webserver()

        spaceLeft = freeSpace(self.config["general"]["download_folder"])

        self.log.info(_("Free space: %s") % formatSize(spaceLeft))

        self.config.save() #save so config files gets filled

        link_file = join(pypath, "links.txt")

        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.addPackage("links.txt", [link_file], 1)
            f.close()

        link_file = "links.txt"
        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.addPackage("links.txt", [link_file], 1)
            f.close()

        #self.scheduler.addJob(0, self.accountManager.getAccountInfos)
        self.log.info(_("Activating Accounts..."))
        self.accountManager.getAccountInfos()

        self.threadManager.pause = False
        self.running = True

        self.log.info(_("Activating Plugins..."))
        self.hookManager.coreReady()

        self.log.info(_("pyLoad is up and running"))

        #test api
#        from module.common.APIExerciser import startApiExerciser
#        startApiExerciser(self, 3)

        #some memory stats
#        from guppy import hpy
#        hp=hpy()
#        import objgraph
#        objgraph.show_most_common_types(limit=20)
#        import memdebug
#        memdebug.start(8002)

        locals().clear()

        while True:
            sleep(2)
            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                self.removeLogger()
                _exit(0) #@TODO thrift blocks shutdown

            self.threadManager.work()
            self.scheduler.work()

    def setupDB(self):
        self.db = DatabaseBackend(self) # the backend
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files #ugly?

    def init_webserver(self):
        if self.config['webinterface']['activated']:
            self.webserver = WebServer(self)
            self.webserver.start()

    def init_logger(self, level):
        console = logging.StreamHandler(sys.stdout)
        frm = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s", "%d.%m.%Y %H:%M:%S")
        console.setFormatter(frm)
        self.log = logging.getLogger("log") # settable in config

        if self.config['log']['file_log']:
            if self.config['log']['log_rotate']:
                file_handler = logging.handlers.RotatingFileHandler(join(self.config['log']['log_folder'], 'log.txt'),
                                                                    maxBytes=self.config['log']['log_size'] * 1024,
                                                                    backupCount=int(self.config['log']['log_count']),
                                                                    encoding="utf8")
            else:
                file_handler = logging.FileHandler(join(self.config['log']['log_folder'], 'log.txt'), encoding="utf8")

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
                        self.log.warning(
                            _("could not find %(desc)s: %(name)s") % {"desc": description, "name": tmp_name})
                    else:
                        print _("could not create %(desc)s: %(name)s") % {"desc": description, "name": tmp_name}
                    if essential:
                        exit()

    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time()

    def restart(self):
        self.shutdown()
        chdir(owd)
        # close some open fds
        for i in range(3,50):
            try:
                close(i)
            except :
                pass

        execl(executable, executable, *sys.argv)
        _exit(0)

    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.config['webinterface']['activated'] and hasattr(self, "webserver"):
                self.webserver.quit()

            for thread in self.threadManager.threads:
                thread.put("quit")
            pyfiles = self.files.cache.values()

            for pyfile in pyfiles:
                pyfile.abortDownload()

            self.hookManager.coreExiting()

        except:
            if self.debug:
                print_exc()
            self.log.info(_("error while shutting down"))

        finally:
            self.files.syncSave()
            self.shuttedDown = True

        self.deletePidFile()


    def path(self, *args):
        return join(pypath, *args)


def deamon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # decouple from parent environment 
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
        # exit from second parent, print eventual PID before
            print "Daemon PID %d" % pid
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
        sys.exit(1)

    # Iterate through and close some file descriptors.
    for fd in range(0, 3):
        try:
            os.close(fd)
        except OSError:    # ERROR, fd wasn't open to begin with (ignored)
            pass

    os.open(os.devnull, os.O_RDWR)    # standard input (0)
    os.dup2(0, 1)            # standard output (1)
    os.dup2(0, 2)

    pyload_core = Core()
    pyload_core.start()


def main():
    #change name to 'pyLoadCore'
    #from module.lib.rename_process import renameProcess
    #renameProcess('pyLoadCore')
    if "--daemon" in sys.argv:
            deamon()
    else:
        pyload_core = Core()
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.shutdown()
            pyload_core.log.info(_("killed pyLoad from Terminal"))
            pyload_core.removeLogger()
            _exit(1)

# And so it begins... 
if __name__ == "__main__":
    main()

