# -*- coding: utf-8 -*-
# @author: RaNaN, mkaay, sebnapi, spoob, vuolter
# @version: v0.4.10

from __future__ import with_statement

import __builtin__
import codecs
import getopt
import imp
import logging
import logging.handlers
import os
import signal
import subprocess
import sys
import time
import traceback

import pyload
from pyload.utils import pylgettext as gettext

from pyload import remote
from pyload.Database import DatabaseBackend, FileHandler
from pyload.config.Parser import ConfigParser
from pyload.manager.Account import AccountManager
from pyload.manager.Captcha import CaptchaManager
from pyload.manager.Event import PullManager
from pyload.manager.Plugin import PluginManager
from pyload.manager.Remote import RemoteManager
from pyload.manager.Scheduler import Scheduler
from pyload.Thread.Server import WebServer
from pyload.network.JsEngine import JsEngine
from pyload.network.RequestFactory import RequestFactory
from pyload.utils import freeSpace, formatSize


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

        if len(sys.argv) > 1:
            try:
                options, args = getopt.getopt(sys.argv[1:], 'vchdusqp:',
                    ["version", "clear", "clean", "help", "debug", "user",
                     "setup", "configdir=", "changedir", "daemon",
                     "quit", "status", "no-remote","pidfile="])

                for option, argument in options:
                    if option in ("-v", "--version"):
                        print "pyLoad", pyload.__version__
                        sys.exit()
                    elif option in ("-p", "--pidfile"):
                        self.pidfile = argument
                    elif option == "--daemon":
                        self.daemon = True
                    elif option in ("-c", "--clear"):
                        self.deleteLinks = True
                    elif option in ("-h", "--help"):
                        self.print_help()
                        sys.exit()
                    elif option in ("-d", "--debug"):
                        self.doDebug = True
                    elif option in ("-u", "--user"):
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
                        s.set_user()
                        sys.exit()
                    elif option in ("-s", "--setup"):
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
                        s.start()
                        sys.exit()
                    elif option == "--changedir":
                        from pyload.config.Setup import SetupAssistant as Setup

                        self.config = ConfigParser()
                        s = Setup(self.config)
                        s.conf_path(True)
                        sys.exit()
                    elif option in ("-q", "--quit"):
                        self.quitInstance()
                        sys.exit()
                    elif option == "--status":
                        pid = self.isAlreadyRunning()
                        if self.isAlreadyRunning():
                            print pid
                            sys.exit(0)
                        else:
                            print "false"
                            sys.exit(1)
                    elif option == "--clean":
                        self.cleanTree()
                        sys.exit()
                    elif option == "--no-remote":
                        self.remote = False

            except getopt.GetoptError:
                print 'Unknown Argument(s) "%s"' % " ".join(sys.argv[1:])
                self.print_help()
                sys.exit()


    def print_help(self):
        print
        print "pyLoad v%s     2008-2015 the pyLoad Team" % pyload.__version__
        print
        if sys.argv[0].endswith(".py"):
            print "Usage: python pyload.py [options]"
        else:
            print "Usage: pyload [options]"
        print
        print "<Options>"
        print "  -v, --version", " " * 10, "Print version to terminal"
        print "  -c, --clear", " " * 12, "Delete all saved packages/links"
        # print "  -a, --add=<link/list>", " " * 2, "Add the specified links"
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
        os._exit(1)


    def writePidFile(self):
        self.deletePidFile()
        pid = os.getpid()
        with open(self.pidfile, "wb") as f:
            f.write(str(pid))


    def deletePidFile(self):
        if self.checkPidFile():
            self.log.debug("Deleting old pidfile %s" % self.pidfile)
            os.remove(self.pidfile)


    def checkPidFile(self):
        """ return pid as int or 0"""
        if os.path.isfile(self.pidfile):
            with open(self.pidfile, "rb") as f:
                pid = f.read().strip()
            if pid:
                pid = int(pid)
                return pid

        return 0


    def isAlreadyRunning(self):
        pid = self.checkPidFile()
        if not pid or os.name == "nt":
            return False
        try:
            os.kill(pid, 0)  #: 0 - default signal (does nothing)
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

            t = time.time()
            print "waiting for pyLoad to quit"

            while os.path.exists(self.pidfile) and t + 10 > time.time():
                time.sleep(0.25)

            if not os.path.exists(self.pidfile):
                print "pyLoad successfully stopped"
            else:
                os.kill(pid, 9)  #: SIGKILL
                print "pyLoad did not respond"
                print "Kill signal was send to process with id %s" % pid

        except Exception:
            print "Error quitting pyLoad"


    def cleanTree(self):
        for path, dirs, files in os.walk(self.path("")):
            for f in files:
                if not f.endswith(".pyo") and not f.endswith(".pyc"):
                    continue

                if "_25" in f or "_26" in f or "_27" in f:
                    continue

                print os.path.join(path, f)
                reshutil.move(os.path.join(path, f))


    def start(self, rpc=True, web=True):
        """ starts the fun :D """

        self.version = pyload.__version__

        if not os.path.exists("pyload.conf"):
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
                traceback.print_exc()
                print "Setup failed"
            if not res:
                reshutil.move("pyload.conf")

            sys.exit()

        try: signal.signal(signal.SIGQUIT, self.quit)
        except Exception:
            pass

        self.config = ConfigParser()

        gettext.setpaths([os.path.join(os.sep, "usr", "share", "pyload", "locale"), None])
        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=[self.config.get("general", "language"), "en"], fallback=True)
        translation.install(True)

        self.debug = self.doDebug or self.config.get("general", "debug_mode")
        self.remote &= self.config.get("remote", "activated")

        pid = self.isAlreadyRunning()
        if pid:
            print _("pyLoad already running with pid %s") % pid
            sys.exit()

        if os.name != "nt" and self.config.get("general", "renice"):
            os.system("renice %d %d" % (self.config.get("general", "renice"), os.getpid()))

        if self.config.get("permission", "change_group"):
            if os.name != "nt":
                try:
                    import grp

                    group = grp.getgrnam(self.config.get("permission", "group"))
                    os.setgid(group[2])

                except Exception, e:
                    print _("Failed changing group: %s") % e

        if self.config.get("permission", "change_user"):
            if os.name != "nt":
                try:
                    import pwd

                    user = pwd.getpwnam(self.config.get("permission", "user"))
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

        self.log.info(_("Starting") + " pyLoad %s" % pyload.__version__)
        self.log.info(_("Using home directory: %s") % os.getcwd())

        self.writePidFile()

        #@TODO refractor

        remote.activated = self.remote
        self.log.debug("Remote activated: %s" % self.remote)

        self.check_install("Crypto", _("pycrypto to decode container files"))
        # img = self.check_install("Image", _("Python Image Library (PIL) for captcha reading"))
        # self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_file("tmp", _("folder for temporary files"), True)
        # tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False) if os.name != "nt" else True

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
        from pyload.Api import Api
        from pyload.manager.Addon import AddonManager
        from pyload.manager.Thread import ThreadManager

        if pyload.Api.activated != self.remote:
            self.log.warning("Import error: API remote status not correct.")

        self.api = Api(self)

        self.scheduler = Scheduler(self)

        # hell yeah, so many important managers :D
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

        link_file = os.path.join(pypath, "links.txt")

        if os.path.exists(link_file):
            with open(link_file, "rb") as f:
                if f.read().strip():
                    self.api.addPackage("links.txt", [link_file], 1)

        link_file = "links.txt"
        if os.path.exists(link_file):
            with open(link_file, "rb") as f:
                if f.read().strip():
                    self.api.addPackage("links.txt", [link_file], 1)

        # self.scheduler.addJob(0, self.accountManager.getAccountInfos)
        self.log.info(_("Activating Accounts..."))
        self.accountManager.getAccountInfos()

        self.threadManager.pause = False
        self.running = True

        self.log.info(_("Activating Plugins..."))
        self.addonManager.coreReady()

        self.log.info(_("pyLoad is up and running"))

        locals().clear()

        while True:
            time.sleep(2)
            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                self.removeLogger()
                os._exit(0)  #@TODO thrift blocks shutdown

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

            if self.config.get("log", "console_mode") == "label":
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
                    'CRITICAL': "purple",
                }

            console_frm = colorlog.ColoredFormatter(c_fmt, date_fmt, clr)

        # Set console formatter
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(console_frm)
        self.log.addHandler(console)

        log_folder = self.config.get("log", "log_folder")
        if not os.path.exists(log_folder):
            os.makedirs(log_folder, 0700)

        # Set file handler formatter
        if self.config.get("log", "file_log"):
            if self.config.get("log", "log_rotate"):
                file_handler = logging.handlers.RotatingFileHandler(os.path.join(log_folder, 'log.txt'),
                                                                    maxBytes=self.config.get("log", "log_size") * 1024,
                                                                    backupCount=int(self.config.get("log", "log_count")),
                                                                    encoding="utf8")
            else:
                file_handler = logging.FileHandler(os.path.join(log_folder, 'log.txt'), encoding="utf8")

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
                imp.find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)

            return True
        except Exception:
            if essential:
                self.log.info(_("Install %s") % legend)
                sys.exit()

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
            if not os.path.exists(tmp_name):
                file_exists = False
                if empty:
                    try:
                        if folder:
                            tmp_name = tmp_name.replace("/", sep)
                            os.makedirs(tmp_name)
                        else:
                            open(tmp_name, "w")
                    except Exception:
                        file_created = False
                else:
                    file_created = False

            if not file_exists and not quiet:
                if file_created:
                    # self.log.info( _("%s created") % description )
                    pass
                else:
                    if not empty:
                        self.log.warning(
                            _("could not find %(desc)s: %(name)s") % {"desc": description, "name": tmp_name})
                    else:
                        print _("could not create %(desc)s: %(name)s") % {"desc": description, "name": tmp_name}
                    if essential:
                        sys.exit()


    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time.time()


    def restart(self):
        self.shutdown()
        os.chdir(owd)
        # close some open fds
        for i in xrange(3, 50):
            try:
                os.close(i)
            except Exception:
                pass

        os.execl(executable, executable, *sys.argv)
        os._exit(0)


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
                traceback.print_exc()
            self.log.info(_("error while shutting down"))

        finally:
            self.files.syncSave()
            self.shuttedDown = True

        self.deletePidFile()


    def path(self, *args):
        return os.path.join(pypath, *args)


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
    for fd in xrange(0, 3):
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
            os._exit(1)

# And so it begins...
if __name__ == "__main__":
    main()
