# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay, sebnapi, spoob
# @version: v0.4.10

CURRENT_VERSION = '0.4.10'

import __builtin__

from getopt import getopt, GetoptError
import pyload.utils.pylgettext as gettext
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

from pyload.manager.Account import AccountManager
from pyload.manager.Captcha import CaptchaManager
from pyload.config.Parser import ConfigParser
from pyload.manager.Plugin import PluginManager
from pyload.manager.Event import PullManager
from pyload.network.RequestFactory import RequestFactory
from pyload.manager.thread.Server import WebServer
from pyload.manager.event.Scheduler import Scheduler
from pyload.network.JsEngine import JsEngine
from pyload import remote
from pyload.manager.Remote import RemoteManager
from pyload.database import DatabaseBackend, FileHandler

from pyload.utils import freeSpace, formatSize, get_console_encoding

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
        self.running = False
        self.daemon = False
        self.remote = True
        self.arg_links = []
        self.pidfile = "pyload.pid"
        self.deleteLinks = False  #: will delete links on startup

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
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
                        s.set_user()
                        exit()
                    elif option in ("-s", "--setup"):
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
                        s.start()
                        exit()
                    elif option == "--changedir":
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
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
        print
        print "pyLoad v%s     2008-2015 the pyLoad Team" % CURRENT_VERSION
        print
        if sys.argv[0].endswith(".py"):
            print "Usage: python pyload.py [options]"
        else:
            print "Usage: pyload [options]"
        print
        print "<Options>"
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -c, --clear", " " * 12, "Delete all saved packages/links"
        #print "  -a, --add=<link/list>", " " * 2, "Add the specified links"
        print "  -u, --user", " " * 13, "Manages users"
        print "  -d, --debug", " " * 12, "Enable debug mode"
        print "  -s, --setup", " " * 12, "Run Setup Assistant"
        print "  --configdir=<dir>", " " * 6, "Run with <dir> as config directory"
        print "  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>"
        print "  --changedir", " " * 12, "Change config dir permanently"
        print "  --daemon", " " * 15, "Daemonmize after start"
        print "  --no-remote", " " * 12, "Disable remote access (saves RAM)"
        print "  --status", " " * 15, "Display pid if running or False"
        print "  --clean", " " * 16, "Remove .pyc/.pyo files"
        print "  -q, --quit", " " * 13, "Quit running pyLoad instance"
        print "  -h, --help", " " * 13, "Display this help screen"
        print


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
        except Exception:
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
            os.kill(pid, 3)  #: SIGUIT

            t = time()
            print "waiting for pyLoad to quit"

            while exists(self.pidfile) and t + 10 > time():
                sleep(0.25)

            if not exists(self.pidfile):
                print "pyLoad successfully stopped"
            else:
                os.kill(pid, 9)  #: SIGKILL
                print "pyLoad did not respond"
                print "Kill signal was send to process with id %s" % pid

        except Exception:
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
            from pyload.config.Setup import SetupAssistant as Setup

            print "This is your first start, running configuration assistent now."
            self.config = ConfigParser()
            s = Setup(self.config)
            res = False
            try:
                res = s.start()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print "\nSetup interrupted"
            except Exception:
                res = False
                print_exc()
                print "Setup failed"
            if not res:
                remove("pyload.conf")

            exit()

        try: signal.signal(signal.SIGQUIT, self.quit)
        except Exception: pass

        self.config = ConfigParser()

        gettext.setpaths([join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=[self.config.get("general", "language"), "en"], fallback=True)
        translation.install(True)

        self.debug = self.doDebug or self.config.get("general", "debug_mode")
        self.remote &= self.config.get("remote", "activated")

        pid = self.isAlreadyRunning()
        if pid:
            print _("pyLoad already running with pid %s") % pid
            exit()

        if os.name != "nt" and self.config.get("general", "renice"):
            os.system("renice %d %d" % (self.config.get("general", "renice"), os.getpid()))

        if self.config.get("permission", "change_group"):
            if os.name != "nt":
                try:
                    from grp import getgrnam

                    group = getgrnam(self.config.get("permission", "group"))
                    os.setgid(group[2])
                except Exception, e:
                    print _("Failed changing group: %s") % e

        if self.config.get("permission", "change_user"):
            if os.name != "nt":
                try:
                    from pwd import getpwnam

                    user = getpwnam(self.config.get("permission", "user"))
                    os.setuid(user[2])
                except Exception, e:
                    print _("Failed changing user: %s") % e

        self.check_file(self.config.get("log", "log_folder"), _("folder for logs"), True)

        if self.debug:
            self.init_logger(logging.DEBUG)  #: logging level
        else:
            self.init_logger(logging.INFO)  #: logging level

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
        #img = self.check_install("Image", _("Python Image Library (PIL) for captcha reading"))
        #self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_file("tmp", _("folder for temporary files"), True)
        #tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False) if os.name != "nt" else True

        self.captcha = True  #: checks seems to fail, although tesseract is available

        self.check_file(self.config.get("general", "download_folder"), _("folder for downloads"), True)

        if self.config.get("ssl", "activated"):
            self.check_install("OpenSSL", _("OpenSSL for secure connection"))

        self.setupDB()
        if self.config.oldRemoteData:
            self.log.info(_("Moving old user config to DB"))
            self.db.addUser(self.config.oldRemoteData['username'], self.config.oldRemoteData['password'])

            self.log.info(_("Please check your logindata with ./pyload.py -u"))

        if self.deleteLinks:
            self.log.info(_("All links removed"))
            self.db.purgeLinks()

        self.requestFactory = RequestFactory(self)
        __builtin__.pyreq = self.requestFactory

        self.lastClientConnected = 0

        # later imported because they would trigger api import, and remote value not set correctly
        from pyload import api
        from pyload.manager.Addon import AddonManager
        from pyload.manager.Thread import ThreadManager

        if api.activated != self.remote:
            self.log.warning("Import error: API remote status not correct.")

        self.api = api.Api(self)

        self.scheduler = Scheduler(self)

        #hell yeah, so many important managers :D
        self.pluginManager = PluginManager(self)
        self.pullManager = PullManager(self)
        self.accountManager = AccountManager(self)
        self.threadManager = ThreadManager(self)
        self.captchaManager = CaptchaManager(self)
        self.addonManager = AddonManager(self)
        self.remoteManager = RemoteManager(self)

        self.js = JsEngine(self)

        self.log.info(_("Downloadtime: %s") % self.api.isTimeDownload())

        if rpc:
            self.remoteManager.startBackends()

        if web:
            self.init_webserver()

        spaceLeft = freeSpace(self.config.get("general", "download_folder"))

        self.log.info(_("Free space: %s") % formatSize(spaceLeft))

        self.config.save()  #: save so config files gets filled

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
        self.addonManager.coreReady()

        self.log.info(_("pyLoad is up and running"))

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
                _exit(0)  #@TODO thrift blocks shutdown

            self.threadManager.work()
            self.scheduler.work()


    def setupDB(self):
        self.db = DatabaseBackend(self)  #: the backend
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files  #: ugly?


    def init_webserver(self):
        if self.config.get("webui", "activated"):
            self.webserver = WebServer(self)
            self.webserver.start()


    def init_logger(self, level):
        self.log = logging.getLogger("log")
        self.log.setLevel(level)

        date_fmt = "%Y-%m-%d %H:%M:%S"
        fh_fmt   = "%(asctime)s %(levelname)-8s  %(message)s"

        fh_frm      = logging.Formatter(fh_fmt, date_fmt)  #: file handler formatter
        console_frm = fh_frm  #: console formatter did not use colors as default

        # Console formatter with colors
        if self.config.get("log", "color_console"):
            import colorlog

            color_template = self.config.get("log", "color_template")
            extra_clr = {}

            if color_template is "mixed":
                c_fmt = "%(log_color)s%(asctime)s %(label_log_color)s%(bold)s%(white)s %(levelname)-8s%(reset)s  %(log_color)s%(message)s"
                clr = {
                    'DEBUG'   : "cyan"  ,
                    'WARNING' : "yellow",
                    'ERROR'   : "red"   ,
                    'CRITICAL': "purple",
                }
                extra_clr = {
                    'label': {
                        'DEBUG'   : "bg_cyan"  ,
                        'INFO'    : "bg_green" ,
                        'WARNING' : "bg_yellow",
                        'ERROR'   : "bg_red"   ,
                        'CRITICAL': "bg_purple",
                    }
                }

            elif color_template is "label":
                c_fmt = "%(asctime)s %(log_color)s%(bold)s%(white)s %(levelname)-8s%(reset)s  %(message)s"
                clr = {
                    'DEBUG'   : "bg_cyan"  ,
                    'INFO'    : "bg_green" ,
                    'WARNING' : "bg_yellow",
                    'ERROR'   : "bg_red"   ,
                    'CRITICAL': "bg_purple",
                }

            else:
                c_fmt = "%(log_color)s%(asctime)s  %(levelname)-8s  %(message)s"
                clr = {
                    'DEBUG'   : "cyan"  ,
                    'WARNING' : "yellow",
                    'ERROR'   : "red"   ,
                    'CRITICAL': "purple"
                }

            console_frm = colorlog.ColoredFormatter(format=c_fmt,
                                                    datefmt=date_fmt,
                                                    log_colors=clr,
                                                    secondary_log_colors=extra_clr)

        # Set console formatter
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(console_frm)
        self.log.addHandler(console)

        log_folder = self.config.get("log", "log_folder")
        if not exists(log_folder):
            makedirs(log_folder, 0700)

        # Set file handler formatter
        if self.config.get("log", "file_log"):
            if self.config.get("log", "log_rotate"):
                file_handler = logging.handlers.RotatingFileHandler(join(log_folder, 'log.txt'),
                                                                    maxBytes=self.config.get("log", "log_size") * 1024,
                                                                    backupCount=int(self.config.get("log", "log_count")),
                                                                    encoding="utf8")
            else:
                file_handler = logging.FileHandler(join(log_folder, 'log.txt'), encoding="utf8")

            file_handler.setFormatter(fh_frm)
            self.log.addHandler(file_handler)


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
        except Exception:
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
                    except Exception:
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
        for i in range(3, 50):
            try:
                close(i)
            except Exception:
                pass

        execl(executable, executable, *sys.argv)
        _exit(0)


    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.config.get("webui", "activated") and hasattr(self, "webserver"):
                self.webserver.quit()

            for thread in list(self.threadManager.threads):
                thread.put("quit")
            pyfiles = self.files.cache.values()

            for pyfile in pyfiles:
                pyfile.abortDownload()

            self.addonManager.coreExiting()

        except Exception:
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
