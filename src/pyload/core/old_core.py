#!/usr/bin/env python
# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import builtins
import os
import signal
import subprocess
import sys
import time
from builtins import HOMEDIR, PKGDIR, _, object, range, str
from getopt import GetoptError, getopt
from imp import find_module
from sys import argv, executable, exit

import pyload.core.utils.pylgettext as gettext
from pyload import __version__ as PYLOAD_VERSION
from pyload import __version_info__ as PYLOAD_VERSION_INFO
from pyload import exc_logger
from pyload.core.config.config_parser import ConfigParser
from pyload.core.database import DatabaseThread
from pyload.core.database.file_database import FileHandler
from pyload.core.log_factory import LogFactory
from pyload.core.manager.account_manager import AccountManager
from pyload.core.manager.captcha_manager import CaptchaManager
from pyload.core.manager.event_manager import EventManager
from pyload.core.manager.plugin_manager import PluginManager
from pyload.core.network.request_factory import RequestFactory
from pyload.core.remote.remote_manager import RemoteManager
from pyload.core.scheduler import Scheduler
from pyload.core.utils.utils import formatSize, freeSpace
from pyload.webui.server_thread import WebServer

# TODO: List
# - configurable auth system ldap/mysql
# - cron job like sheduler


class Core(object):
    """
    pyLoad Core, one tool to rule them all...

    (the filehosters) :D
    """

    def __init__(self):
        self.doDebug = False
        self.daemon = False
        self.remote = True
        self.arg_links = []
        self.pidfile = "pyload.pid"
        self.deleteLinks = False  #: will delete links on startup

        if len(argv) > 1:
            try:
                options, args = getopt(
                    argv[1:],
                    "vchdusqp:",
                    [
                        "version",
                        "clear",
                        "clean",
                        "help",
                        "debug",
                        "configdir=",
                        "daemon",
                        "quit",
                        "status",
                        "no-remote",
                        "pidfile=",
                    ],
                )

                for option, argument in options:
                    if option in ("-v", "--version"):
                        print("pyLoad", PYLOAD_VERSION)
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
                    elif option in ("-q", "--quit"):
                        self.quitInstance()
                        exit()
                    elif option == "--status":
                        pid = self.isAlreadyRunning()
                        if self.isAlreadyRunning():
                            print(pid)
                            exit(0)
                        else:
                            print("false")
                            exit(1)
                    elif option == "--clean":
                        self.cleanTree()
                        exit()
                    elif option == "--no-remote":
                        self.remote = False

            except GetoptError:
                print('Unknown Argument(s) "{}"'.format(" ".join(argv[1:])))
                self.print_help()
                exit()

    def print_help(self):
        print("")
        print("pyLoad v{}     2018 pyLoad team".format(PYLOAD_VERSION))
        print("")
        print("Usage: pyLoad [options]")
        print("")
        print("<Options>")
        print("  -v, --version", " " * 10, "Print version to terminal")
        print("  -c, --clear", " " * 12, "Delete all saved packages/links")
        # print("  -a, --add=<link/list>", " " * 2, "Add the specified links")
        print("  -d, --debug", " " * 12, "Enable debug mode")
        print("  --configdir=<dir>", " " * 6, "Run with <dir> as config directory")
        print("  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>")
        print("  --daemon", " " * 15, "Daemonmize after start")
        print("  --no-remote", " " * 12, "Disable remote access (saves RAM)")
        print("  --status", " " * 15, "Display pid if running or False")
        print("  --clean", " " * 16, "Remove .pyc/.pyo files")
        print("  -q, --quit", " " * 13, "Quit running pyLoad instance")
        print("  -h, --help", " " * 13, "Display this help screen")
        print("")

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
        with open(self.pidfile, mode="w") as f:
            f.write(str(pid))

    def deletePidFile(self):
        if self.checkPidFile():
            self.log.debug("Deleting old pidfile {}".format(self.pidfile))
            os.remove(self.pidfile)

    def checkPidFile(self):
        """
        return pid as int or 0.
        """
        if os.path.isfile(self.pidfile):
            with open(self.pidfile) as f:
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
            print("Not supported on windows.")
            return

        pid = self.isAlreadyRunning()
        if not pid:
            print("No pyLoad running.")
            return

        try:
            os.kill(pid, 3)  #: SIGUIT

            t = time.time()
            print("waiting for pyLoad to quit")

            while os.path.exists(self.pidfile) and t + 10 > time.time():
                time.sleep(0.25)

            if not os.path.exists(self.pidfile):
                print("pyLoad successfully stopped")
            else:
                os.kill(pid, 9)  #: SIGKILL
                print("pyLoad did not respond")
                print("Kill signal was send to process with id {}".format(pid))

        except Exception:
            print("Error quitting pyLoad")

    def cleanTree(self):
        for path, dirs, files in os.walk(PKGDIR):
            for f in files:
                if not f.endswith(".pyo") and not f.endswith(".pyc"):
                    continue
                print(os.path.join(path, f))
                os.remove(os.path.join(path, f))

    def start(self, rpc=True, web=True):
        """
        starts the fun :D.
        """

        self.version = PYLOAD_VERSION
        self.version_info = PYLOAD_VERSION_INFO

        try:
            signal.signal(signal.SIGQUIT, self.quit)
        except Exception:
            pass

        self.config = ConfigParser()

        gettext.setpaths(
            [os.path.join(os.sep, "usr", "share", "pyload", "locale"), None]
        )
        translation = gettext.translation(
            "pyload",
            os.path.join(PKGDIR, "locale"),
            languages=[self.config.get("general", "language"), "en"],
            fallback=True,
        )
        translation.install(True)

        self.debug = self.doDebug or self.config.get("general", "debug_mode")
        self.remote &= self.config.get("remote", "activated")

        pid = self.isAlreadyRunning()
        if pid:
            print(_("pyLoad already running with pid {}").format(pid))
            exit()

        if os.name != "nt" and self.config.get("general", "renice"):
            os.system(
                "renice {} {}".format(self.config.get("general", "renice"), os.getpid())
            )

        if self.config.get("permission", "change_group"):
            if os.name != "nt":
                try:
                    from grp import getgrnam

                    group = getgrnam(self.config.get("permission", "group"))
                    os.setgid(group[2])
                except Exception as e:
                    print(_("Failed changing group: {}").format(e))

        if self.config.get("permission", "change_user"):
            if os.name != "nt":
                try:
                    from pwd import getpwnam

                    user = getpwnam(self.config.get("permission", "user"))
                    os.setuid(user[2])
                except Exception as e:
                    print(_("Failed changing user: {}").format(e))

        self.do_kill = False
        self.do_restart = False
        self.shuttedDown = False

        self.logfactory = LogFactory(self)
        self.logfactory.init_logger(exc_logger.name)
        self.log = self.logfactory.get_logger("pyload")

        self.log.info(_("Starting pyLoad {}").format(self.version))
        self.log.info(_("Using home directory: {}").format(os.getcwd()))

        self.writePidFile()

        # TODO: refractor
        self.log.debug("Remote activated: {}".format(self.remote))

        self.check_install("cryptography", _("pycrypto to decode container files"))
        # img = self.check_install("Image", _("Python Image Libary (Pillow) for captcha reading"))
        # self.check_install("pycurl", _("pycurl to download any files"), True, True)
        self.check_file(
            os.path.join(HOMEDIR, "pyLoad", ".tmp"),
            _("folder for temporary files"),
            True,
        )
        # tesser = self.check_install("tesseract", _("tesseract for captcha reading"), False) if os.name != "nt" else True

        self.captcha = True  #: checks seems to fail, althoug tesseract is available

        self.check_file(
            self.config.get("general", "download_folder"),
            _("folder for downloads"),
            True,
        )

        if self.config.get("ssl", "activated"):
            self.check_install("OpenSSL", _("OpenSSL for secure connection"))

        self.setupDB()
        
        if self.config.oldRemoteData:
            self.log.info(_("Moving old user config to DB"))
            self.db.addUser(
                self.config.oldRemoteData["username"],
                self.config.oldRemoteData["password"],
            )

            self.log.info(_("Please check your logindata with pyLoad -u"))

        if self.deleteLinks:
            self.log.info(_("All links os.removed"))
            self.db.purgeLinks()

        self.requestFactory = RequestFactory(self)
        builtins.REQUESTS = self.requestFactory

        self.lastClientConnected = 0

        # later imported because they would trigger api import, and remote value
        # not set correctly
        from pyload.core.api import Api
        from pyload.core.manager.addon_manager import AddonManager
        from pyload.core.manager.thread_manager import ThreadManager

        self.api = Api(self)

        self.scheduler = Scheduler(self)

        # hell yeah, so many important managers :D
        self.pluginManager = PluginManager(self)
        self.pullManager = EventManager(self)
        self.accountManager = AccountManager(self)
        self.threadManager = ThreadManager(self)
        self.captchaManager = CaptchaManager(self)
        self.addonManager = AddonManager(self)
        self.remoteManager = RemoteManager(self)

        self.log.info(_("Download time: {}").format(self.api.isTimeDownload()))

        if rpc:
            self.remoteManager.startBackends()

        if web:
            self.init_webserver()

        spaceLeft = freeSpace(self.config.get("general", "download_folder"))

        self.log.info(_("Free space: {}").format(formatSize(spaceLeft)))

        self.config.save()  #: save so config files gets filled

        link_file = os.path.join(HOMEDIR, "pyLoad", "links.txt")

        if os.path.exists(link_file):
            with open(link_file) as f:
                if f.read().strip():
                    self.api.addPackage("links.txt", [link_file], 1)

        link_file = "links.txt"
        if os.path.exists(link_file):
            with open(link_file) as f:
                if f.read().strip():
                    self.api.addPackage("links.txt", [link_file], 1)

        # self.scheduler.addJob(0, self.accountManager.getAccountInfos)
        self.log.info(_("Activating Accounts..."))
        self.accountManager.getAccountInfos()

        self.threadManager.pause = False

        self.log.info(_("Activating Plugins..."))
        self.addonManager.coreReady()

        self.log.info(_("pyLoad is up and running"))

        # test api
        #        from tests.api_exerciser import startApiExerciser
        #        startApiExerciser(self, 3)

        # some memory os.stats
        #        from guppy import hpy
        #        hp=hpy()
        #        import objgraph
        #        objgraph.show_most_common_types(limit=20)
        #        import memdebug
        #        memdebug.start(8002)

        locals().clear()

        while True:
            try:
                time.sleep(2)
            except IOError as e:
                if e.errno != 4:  #: errno.EINTR
                    raise

            if self.do_restart:
                self.log.info(_("Restarting pyLoad"))
                self.restart()

            if self.do_kill:
                self.log.info(_("pyLoad quits"))
                self.shutdown()
                os._exit(0)  # TODO: thrift blocks shutdown

            self.threadManager.work()
            self.scheduler.work()

    def setupDB(self):
        self.db = DatabaseThread(self)  #: the backend
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files  #: ugly?

    def init_webserver(self):
        if self.config.get("webui", "activated"):
            self.webserver = WebServer(self)
            self.webserver.start()

    def check_install(self, check_name, legend, python=True, essential=False):
        """
        check wether needed tools are installed.
        """
        try:
            if python:
                find_module(check_name)
            else:
                pipe = subprocess.PIPE
                subprocess.Popen(check_name, stdout=pipe, stderr=pipe)

            return True
        except Exception:
            if essential:
                self.log.info(_("Install {}").format(legend))
                exit()

            return False

    def check_file(
        self,
        check_names,
        description="",
        folder=False,
        empty=True,
        essential=False,
        quiet=False,
    ):
        """
        check wether needed files exists.
        """
        tmp_names = []
        if not isinstance(check_names, list):
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
                            tmp_name = tmp_name.replace("/", os.sep)
                            os.makedirs(tmp_name, exist_ok=True)
                        else:
                            open(tmp_name, mode="w")  #: where is closed?
                    except Exception:
                        file_created = False
                else:
                    file_created = False

            if not file_exists and not quiet:
                if file_created:
                    # self.log.info( _("{} created").format(description))
                    pass
                else:
                    if not empty:
                        self.log.warning(
                            _("could not find {desc}: {name}").format(
                                desc=description, name=tmp_name
                            )
                        )
                    else:
                        print(
                            _("could not create {desc}: {name}").format(
                                desc=description, name=tmp_name
                            )
                        )
                    if essential:
                        exit()

    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time.time()

    def restart(self):
        self.shutdown()
        # close some open fds
        for i in range(3, 50):
            try:
                os.close(i)
            except BaseException:
                pass

        os.execl(executable, executable, *sys.argv)
        os._exit(0)

    def shutdown(self):
        self.log.info(_("shutting down..."))
        try:
            if self.webserver.is_alive():
                self.webserver.stop()

            for thread in self.threadManager.threads:
                thread.put("quit")
            pyfiles = list(self.files.cache.values())

            for pyfile in pyfiles:
                pyfile.abortDownload()

            self.addonManager.coreExiting()

        finally:
            self.files.syncSave()
            self.logfactory.shutdown()
            self.shuttedDown = True

        self.deletePidFile()


def daemon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #1 failed: {} ({})\n".format(e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # exit from second parent, print(eventual PID before)
            print("Daemon PID {}".format(pid))
            sys.exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: {} ({})\n".format(e.errno, e.strerror))
        sys.exit(1)

    # Iterate through and close some file descriptors.
    for fd in range(0, 3):
        try:
            os.close(fd)
        except OSError:  #: ERROR as fd wasn't open to begin with (ignored)
            pass

    os.open(os.devnull, os.O_RDWR)  #: standard input (0)
    os.dup2(0, 1)  #: standard output (1)
    os.dup2(0, 2)

    pyload_core = Core()
    pyload_core.start()


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    # change name to 'pyLoad'
    # from pyload.lib.rename_process import renameProcess
    # renameProcess('pyLoad')
    if "--daemon" in sys.argv:
        daemon()
    else:
        pyload_core = Core()
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.log.info(_("killed pyLoad from Terminal"))
            pyload_core.shutdown()
            os._exit(1)


def run():
    """
    Entry point for console_scripts
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    run()
