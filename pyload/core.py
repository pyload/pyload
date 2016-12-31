# -*- coding: utf-8 -*-
#@author: sebnapi, RaNaN, mkaay

from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
from pyload import __version__ as CURRENT_VERSION

import builtins

from getopt import getopt, GetoptError
import logging
import logging.handlers
import os
from os import _exit, execl, getcwd, remove, walk, chdir, close
import signal
import sys
import gettext
from sys import argv, executable, exit
from time import time, sleep
from traceback import print_exc

import locale

locale.locale_alias = locale.windows_locale = {} #save ~100kb ram, no known sideeffects for now

import subprocess

subprocess.__doc__ = None # the module with the largest doc we are using

from pyload.inithomedir import init_dir

from builtins import PACKDIR
from builtins import COREDIR

init_dir()

from pyload.manager.account import AccountManager
from pyload.config.parser import ConfigParser
from pyload.manager.config import ConfigManager
from pyload.manager.plugin import PluginManager
from pyload.manager.event import EventManager
from pyload.network.request import RequestFactory
from pyload.thread.webui import WebServer
from pyload.manager.scheduler import Scheduler
from pyload.manager.remote import RemoteManager
from pyload.utils.jsengine import JsEngine

from pyload.utils import format_size, get_console_encoding
from pyload.utils.fs import free_space, exists, makedirs, join, chmod

from codecs import getwriter

# test runner overwrites sys.stdout
if hasattr(sys.stdout, "encoding"):
    enc = get_console_encoding(sys.stdout.encoding)
else:
    enc = "utf8"

sys._stdout = sys.stdout
sys.stdout = getwriter(enc)(sys.stdout, errors="replace")


# TODO List
# - configurable auth system ldap/mysql
# - cron job like sheduler
# - plugin stack / multi decrypter
# - content attribute for files / sync status
# - sync with disk content / file manager / nested packages
# - sync between pyload cores
# - new attributes (date|sync status)
# - improve external scripts
class Core(object):
    """pyLoad Core, one tool to rule them all... (the filehosters) :D"""

    def __init__(self):
        self.doDebug = False
        self.running = False
        self.daemon = False
        self.remote = True
        self.pdb = None
        self.arg_links = []
        self.pidfile = "pyload.pid"
        self.deleteLinks = False # will delete links on startup

        if len(argv) > 1:
            try:
                options, args = getopt(argv[1:], 'vchdusqp:',
                                       ["version", "clear", "clean", "help", "debug", "user",
                                        "setup", "configdir=", "changedir", "daemon",
                                        "quit", "status", "no-remote", "pidfile="])

                for option, argument in options:
                    if option in ("-v", "--version"):
                        print("pyLoad", CURRENT_VERSION)
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
                        from pyload.setup.setup import Setup

                        self.config = ConfigParser()
                        s = Setup(COREDIR, self.config)
                        s.set_user()
                        exit()
                    elif option in ("-s", "--setup"):
                        from pyload.setup.setup import Setup

                        self.config = ConfigParser()
                        s = Setup(COREDIR, self.config)
                        s.start()
                        exit()
                    elif option == "--changedir":
                        from pyload.setup.setup import Setup

                        self.config = ConfigParser()
                        s = Setup(COREDIR, self.config)
                        s.conf_path(True)
                        exit()
                    elif option in ("-q", "--quit"):
                        self.quit_instance()
                        exit()
                    elif option == "--status":
                        pid = self.is_already_running()
                        if self.is_already_running():
                            print(pid)
                            exit(0)
                        else:
                            print("false")
                            exit(1)
                    elif option == "--clean":
                        self.clean_tree()
                        exit()
                    elif option == "--no-remote":
                        self.remote = False

            except GetoptError:
                print('Unknown Argument(s) "{}"'.format(" ".join(argv[1:])))
                self.print_help()
                exit()

    def print_help(self):
        print("")
        print("pyLoad v{}     2009-2017 The pyLoad Team".format(CURRENT_VERSION))
        print("")
        if sys.argv[0].endswith(".py"):
            print("Usage: python pyload.py [options]")
        else:
            print("Usage: pyload [options]")
        print("")
        print("<Options>")
        print("  -v, --version", " " * 10, "Print version to terminal")
        print("  -c, --clear", " " * 12, "Delete all saved packages/links")
        #print("  -a, --add=<link/list>", " " * 2, "Add the specified links")
        print("  -u, --user", " " * 13, "Manages users")
        print("  -d, --debug", " " * 12, "Enable debug mode")
        print("  -s, --setup", " " * 12, "Run setup assistant")
        print("  --configdir=<dir>", " " * 6, "Run with <dir> as configuration directory")
        print("  -p, --pidfile=<file>", " " * 3, "Set pidfile to <file>")
        print("  --changedir", " " * 12, "Change configuration directory permanently")
        print("  --daemon", " " * 15, "Daemonize after startup")
        print("  --no-remote", " " * 12, "Disable remote access")
        print("  --status", " " * 15, "Display pid if running or False")
        print("  --clean", " " * 16, "Remove .pyc/.pyo files")
        print("  -q, --quit", " " * 13, "Quit a running pyLoad instance")
        print("  -h, --help", " " * 13, "Display this help screen")
        print("")


    def quit(self, a, b):
        self.shutdown()
        self.log.info(_("Received Quit signal"))
        _exit(1)

    def write_pid_file(self):
        self.delete_pid_file()
        pid = os.getpid()
        f = open(self.pidfile, "wb")
        f.write(str(pid))
        f.close()
        chmod(self.pidfile, 0o660)

    def delete_pid_file(self):
        if self.check_pid_file():
            self.log.debug("Deleting old pidfile {}".format(self.pidfile))
            os.remove(self.pidfile)

    def check_pid_file(self):
        """ return pid as int or 0"""
        if os.path.isfile(self.pidfile):
            f = open(self.pidfile, "rb")
            pid = f.read().strip()
            f.close()
            if pid:
                pid = int(pid)
                return pid

        return 0

    def is_already_running(self):
        pid = self.check_pid_file()
        if not pid or os.name == "nt": return False
        try:
            os.kill(pid, 0)  # 0 - default signal (does nothing)
        except Exception:
            return 0

        return pid

    def quit_instance(self):
        if os.name == "nt":
            print("Not supported on windows.")
            return

        pid = self.is_already_running()
        if not pid:
            print("No pyLoad running.")
            return

        try:
            os.kill(pid, 3) #SIGUIT

            t = time()
            print("waiting for pyLoad to quit")

            while exists(self.pidfile) and t + 10 > time():
                sleep(0.25)

            if not exists(self.pidfile):
                print("pyLoad successfully stopped")
            else:
                os.kill(pid, 9) #SIGKILL
                print("pyLoad did not respond")
                print("Kill signal was send to process with id {}".format(pid))

        except:
            print("Error quitting pyLoad")


    def clean_tree(self):
        for path, dirs, files in walk(self.path("pyload")):
            for f in files:
                if not f.endswith(".pyo") and not f.endswith(".pyc"):
                    continue

                if "_25" in f or "_26" in f or "_27" in f:
                    continue

                print(join(path, f))
                remove(join(path, f))

    def start(self, rpc=True, web=True, tests=False):
        """ starts the fun :D """

        self.version = CURRENT_VERSION

        if not exists("pyload.conf") and not tests:
            from pyload.setup.setup import Setup

            print("This is your first start, running configuration assistant now.")
            self.config = ConfigParser()
            s = Setup(COREDIR, self.config)
            res = False
            try:
                res = s.start()
            except SystemExit:
                pass
            except KeyboardInterrupt:
                print("\nSetup interrupted")
            except:
                res = False
                print_exc()
                print("Setup failed")
            if not res:
                remove("pyload.conf")

            exit()

        try:
            signal.signal(signal.SIGQUIT, self.quit)
        except:
            pass

        self.config = ConfigParser()

        translation = gettext.translation("pyLoad", self.path("locale"),
                                          languages=[self.config['general']['language'], "en"], fallback=True)
        translation.install(True)

        # load again so translations are propagated
        self.config.load_default()

        self.debug = self.doDebug or self.config['general']['debug_mode']

        pid = self.is_already_running()
        # don't exit when in test runner
        if pid and not tests:
            print(_("pyLoad already running with pid {}").format(pid))
            exit()

        if os.name != "nt" and self.config["general"]["renice"]:
            os.system("renice {:d} {:d}".format(self.config["general"]["renice"], os.getpid()))

        if self.config["permission"]["change_group"]:
            if os.name != "nt":
                try:
                    from grp import getgrnam

                    group = getgrnam(self.config["permission"]["group"])
                    os.setgid(group[2])
                except Exception as e:
                    print(_("Failed changing group: {}").format(e.message))

        if self.config["permission"]["change_user"]:
            if os.name != "nt":
                try:
                    from pwd import getpwnam

                    user = getpwnam(self.config["permission"]["user"])
                    os.setuid(user[2])
                except Exception as e:
                    print(_("Failed changing user: {}").format(e.message))

        if self.debug:
            self.init_logger(logging.DEBUG) # logging level
        else:
            self.init_logger(logging.INFO) # logging level

        self.do_kill = False
        self.do_restart = False
        self.shuttedDown = False

        self.log.info(_("Starting") + " pyLoad {}".format(CURRENT_VERSION))
        self.log.info(_("Using home directory: {}").format(getcwd()))

        if not tests:
            self.write_pid_file()

        self.captcha = True # checks seems to fail, although tesseract is available

        self.eventmanager = self.evm = EventManager(self)
        self.setup_db()

        # Upgrade to configManager
        self.config = ConfigManager(self, self.config)

        if self.deleteLinks:
            self.log.info(_("All links removed"))
            self.db.purge_links()

        self.request = RequestFactory(self)
        builtins.pyreq = self.request

        # deferred import, could improve start-up time
        from pyload.api import Api
        from pyload.manager.addon import AddonManager
        from pyload.manager.interaction import InteractionManager
        from pyload.manager.thread import ThreadManager
        from pyload.manager.download import DownloadManager

        Api.init_components()
        self.api = Api(self)

        self.scheduler = Scheduler(self)
        self.js = JsEngine()

        #hell yeah, so many important managers :D
        self.pluginmanager = PluginManager(self)
        self.interactionmanager = self.im = InteractionManager(self)
        self.accountmanager = AccountManager(self)
        self.threadmanager = ThreadManager(self)
        self.downloadmanager = self.dlm = DownloadManager(self)
        self.addonmanager = AddonManager(self)
        self.remotemanager = RemoteManager(self)

        # enough initialization for test cases
        if tests: return

        self.log.info(_("Download time: {}").format(self.api.is_time_download()))

        if rpc:
            self.remotemanager.start_backends()

        if web:
            self.init_webserver()

        dl_folder = self.config["general"]["download_folder"]

        if not exists(dl_folder):
            makedirs(dl_folder)

        spaceLeft = free_space(dl_folder)

        self.log.info(_("Free space: {}").format(format_size(spaceLeft)))

        self.config.save() #save so config files gets filled

        link_file = join(COREDIR, "links.txt")

        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.add_package("links.txt", [link_file], 1)
            f.close()

        link_file = "links.txt"
        if exists(link_file):
            f = open(link_file, "rb")
            if f.read().strip():
                self.api.add_package("links.txt", [link_file], 1)
            f.close()

        #self.scheduler.add_job(0, self.accountmanager.getAccountInfos)
        self.log.info(_("Activating Accounts..."))
        self.accountmanager.refresh_all_accounts()

        #restart failed
        if self.config["download"]["restart_failed"]:
            self.log.info(_("Restarting failed downloads..."))
            self.api.restart_failed()

        # start downloads
        self.dlm.paused = False
        self.running = True

        self.addonmanager.activate_addons()

        self.log.info(_("pyLoad is up and running"))
        self.eventmanager.dispatch_event("pyload:ready")

        #test api
        #        from pyload.common.APIExerciser import start_api_exerciser
        #        start_api_exerciser(self, 3)

        #some memory stats
        #        from guppy import hpy
        #        hp=hpy()
        #        print(hp.heap())
        #        import objgraph
        #        objgraph.show_most_common_types(limit=30)
        #        import memdebug
        #        memdebug.start(8002)
        #        from meliae import scanner
        #        scanner.dump_all_objects(self.path('objs.json'))

        locals().clear()

        while True:
            sleep(1.5)
            if self.do_restart:
                self.log.info(_("restarting pyLoad"))
                self.restart()
            if self.do_kill:
                self.shutdown()
                self.log.info(_("pyLoad quits"))
                self.remove_logger()
                _exit(0)
                # TODO check exits codes, clean exit is still blocked
            try:
                self.downloadmanager.work()
                self.threadmanager.work()
                self.interactionmanager.work()
                self.scheduler.work()
            except Exception as e:
                self.log.critical(_("Critical error: {}").format(e.message))
                self.print_exc()


    def setup_db(self):
        from pyload.database import DatabaseBackend
        from pyload.manager.file import FileManager

        self.db = DatabaseBackend(self) # the backend
        self.db.setup()

        self.files = FileManager(self)
        self.db.manager = self.files #ugly?

    def init_webserver(self):
        self.webserver = WebServer(self)
        self.webserver.start()

    def init_logger(self, level):
        datefmt = "%Y-%m-%d %H:%M:%S"

        # file handler formatter
        fhfmt = "%(asctime)s %(levelname)-8s  %(message)s"
        fh_frm = logging.Formatter(fhfmt, datefmt)
        console_frm = fh_frm

        # console formatter
        if self.config['log']['console_color']:
            from colorlog import ColoredFormatter

            if self.config['log']['color_theme'] == "full":
                cfmt = "%(asctime)s %(log_color)s%(bold)s%(white)s %(levelname)-8s %(reset)s %(message)s"
                clr = {
                    'DEBUG': 'bg_cyan',
                    'INFO': 'bg_green',
                    'WARNING': 'bg_yellow',
                    'ERROR': 'bg_red',
                    'CRITICAL': 'bg_purple',
                }
            else: #light theme
                cfmt = "%(log_color)s%(asctime)s %(levelname)-8s  %(message)s"
                clr = {
                    'DEBUG': 'cyan',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'purple',
                }

            color = True
            if os.name == "nt":
                try:
                    import colorama

                    colorama.init()
                except Exception:
                    color = False
                    print("Install 'colorama' to use the colored log on windows")

            if color: console_frm = ColoredFormatter(cfmt, datefmt, clr)

        # set console formatter
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(console_frm)

        self.log = logging.getLogger("log") # setable in config

        if not exists(self.config['log']['log_folder']):
            makedirs(self.config['log']['log_folder'], 0o700)

        if self.config['log']['file_log']:
            if self.config['log']['log_rotate']:
                file_handler = logging.handlers.RotatingFileHandler(join(self.config['log']['log_folder'], 'log.txt'),
                                                                    maxBytes=self.config['log']['log_size'] * 1024,
                                                                    backupCount=int(self.config['log']['log_count']),
                                                                    encoding="utf8")
            else:
                file_handler = logging.FileHandler(join(self.config['log']['log_folder'], 'log.txt'), encoding="utf8")

            #: set file handler formatter
            file_handler.setFormatter(fh_frm)
            self.log.addHandler(file_handler)

        self.log.addHandler(console) #if console logging
        self.log.setLevel(level)

    def remove_logger(self):
        for h in self.log.handlers:
            self.log.removeHandler(h)
            h.close()

    def restart(self):
        self.shutdown()
        chdir(PACKDIR)
        # close some open fds
        for i in range(3, 50):
            try:
                close(i)
            except:
                pass

        execl(executable, executable, *sys.argv)
        _exit(0)

    def shutdown(self):
        self.log.info(_("shutting down..."))
        self.eventmanager.dispatch_event("coreShutdown")
        try:
            if hasattr(self, "webserver"):
                pass # TODO: quit webserver?
                #                self.webserver.quit()

            self.dlm.shutdown()
            self.api.stop_all_downloads()
            self.addonmanager.deactivate_addons()

        except:
            self.print_exc()
            self.log.info(_("error while shutting down"))

        finally:
            self.files.sync_save()
            self.db.shutdown()
            self.shuttedDown = True

        self.delete_pid_file()

    def shell(self):
        """ stop and open an ipython shell inplace"""
        if self.debug:
            from IPython import embed

            sys.stdout = sys._stdout
            embed()

    def breakpoint(self):
        if self.debug:
            from IPython.core.debugger import Pdb

            sys.stdout = sys._stdout
            if not self.pdb: self.pdb = Pdb()
            self.pdb.set_trace()

    def print_exc(self, force=False):
        if self.debug or force:
            print_exc()

    def path(self, *args):
        return join(COREDIR, *args)


def deamon():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        # print("fork #1 failed: {:d} ({})".format(e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)

    # decouple from parent environment
    os.setsid()
    os.umask(0)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
        # exit from second parent, print(eventual PID before)
            print("Daemon PID {:d}".format(pid))
            sys.exit(0)
    except OSError as e:
        # print("fork #2 failed: {:d} ({})".format(e.errno, e.strerror), file=sys.stderr)
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

# And so it begins...
def main():
    # change name to 'pyLoadCore'
    # from rename_process import rename_process
    # rename_process('pyLoadCore')
    if "--daemon" in sys.argv:
        deamon()
    else:
        pyload_core = Core()
        try:
            pyload_core.start()
        except KeyboardInterrupt:
            pyload_core.shutdown()
            pyload_core.log.info(_("killed pyLoad from terminal"))
            pyload_core.remove_logger()
            _exit(1)
