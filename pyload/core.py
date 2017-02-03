# -*- coding: utf-8 -*-
#@author: vuolter
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import map

import logging
import logging.handlers
import os
import sched
import signal
import tempfile
import time

import colorlog
import setproctitle

from contextlib import closing
from multiprocessing import Process

from pyload.utils.new import format, sys, misc
from pyload.utils.new.path import makedirs, open, remove
from pyload.utils.new.check import lookup


class Restart(Exception):
    
    def __str__(self):
        return """<RestartSignal {}>""".format(self.message)
        
        
class Shutdown(Exception):
    
    def __str__(self):
        return """<ShutdownSignal {}>""".format(self.message)
        
        
# TODO:
#  configurable auth system ldap/mysql
#  cron job like scheduler
#  plugin stack / multi decrypter
#  content attribute for files / sync status
#  sync with disk content / file manager / nested packages
#  sync between pyload cores
#  new attributes (date|sync status)
#  improve external scripts
class Core(Process):

    __title__ = "pyLoad"
    __version__ = "0.5.0"
    __status__ = "3 - Alpha"

    __description__ = """Free and Open Source download manager written in Python
                         and designed to be extremely lightweight, easily extensible
                         and fully manageable via web"""
    __license__ = "AGPLv3"
    __authors__ = (("Walter Purcaro", "vuolter@gmail.com     "),
                   ("Christian Rakow", "Mast3rRaNaN@hotmail.de"))

    def _clean(self):
        join = os.path.join
        remove = os.remove
        for dir, dirnames, filenames in os.walk(COREDIR):
            for dirname in dirnames:
                if dirname != '__pycache__':
                    continue
                dir = join(dir, dirname)
                remove(dir, trash=False, ignore_errors=True)
                break
            for filename in filenames:
                if not filename[-4:] in ('.pyc', '.pyo'):
                    continue
                file = join(dir, filename)
                try:
                    remove(file)
                except Exception:
                    continue
        remove('tmp', trash=False, ignore_errors=True)

    # TODO: Extend `logging.Logger` like `pyload.plugin.Log`
    def _init_logger(self, level):
        # Init logger
        self.log = logging.getLogger("log")
        self.log.setLevel(level)

        # Set console handler
        if not self.config.get('log', 'color_console'):
            fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            consoleform = logging.Formatter(fmt, datefmt)
        else:
            fmt = "%(label)s %(levelname)-8s %(reset)s %(log_color)s%(asctime)s  %(message)s"
            datefmt = "%Y-%m-%d  %H:%M:%S"
            log_colors = {
                'DEBUG': "bold,cyan",
                'WARNING': "bold,yellow",
                'ERROR': "bold,red",
                'CRITICAL': "bold,purple",
            }
            log_colors_2 = {
                'label': {
                    'DEBUG': "bold,white,bg_cyan",
                    'INFO': "bold,white,bg_green",
                    'WARNING': "bold,white,bg_yellow",
                    'ERROR': "bold,white,bg_red",
                    'CRITICAL': "bold,white,bg_purple",
                }
            }
            consoleform = colorlog.ColoredFormatter(fmt, datefmt, log_colors,
                                                    secondary_log_colors=log_colors_2)
        consolehdlr = logging.StreamHandler(sys.stdout)
        consolehdlr.setFormatter(consoleform)
        self.log.add_handler(consolehdlr)

        # Create logfile folder
        logfile_folder = self.config.get('log', 'logfile_folder') or "logs"
        makedirs(logfile_folder)

        # Set file handler
        if not self.config.get('log', 'logfile'):
            return

        fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        fileform = logging.Formatter(fmt, datefmt)

        logfile = os.path.join(logfile_folder, 'log.txt')
        if self.config.get('log', 'rotate'):
            logfile_size = self.config.get('log', 'logfile_size') * 1024
            max_logfiles = self.config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(logfile,
                                                            maxBytes=logfile_size,
                                                            backupCount=max_logfiles,
                                                            encoding=lookup)
        else:
            filehdlr = logging.FileHandler(logfile, encoding='utf-8')

        filehdlr.setFormatter(fileform)
        self.log.add_handler(filehdlr)

    def _init_permissions(self):
        change_group = self.config.get('permission', 'change_group')
        change_user = self.config.get('permission', 'change_user')

        if change_group:
            try:
                group = self.config.get('permission', 'group')
                gid = grp.getgrnam(group)[2]
                os.setgid(gid)
            except Exception as e:
                self.log.error(_("Unable to change gid"), e.message)

        if change_user:
            try:
                user = self.config.get('permission', 'user')
                uid = pwd.getpwnam(user).pw_uid
            except KeyError:
                self.log.error(_("User `{}` not found").format(user))
                return
            try:
                os.setuid(uid)
            except Exception as e:
                self.log.error(_("Unable to change uid"), e.message)

    def _init_config(self, configdir):
        from pyload.config import Config

        if configdir:
            self.configdir = os.path.expanduser(configdir)
            self.log.debug("Use custom configdir `{}`".format(configdir))
        else:
            dirname = 'pyLoad' if os.name == 'nt' else '.pyload'
            self.configdir = os.path.join(USERDIR, dirname)

        profiledir = os.path.join(self.configdir, self.profile)
        tmpdir = os.path.join(profiledir, 'tmp')

        makedirs(profiledir)
        makedirs(tmpdir)
        # NOTE: pyLoad runs over configdir/profile for its entire process-life
        os.chdir(profiledir)

        configfile = self.profile + '.conf'
        self.config = self.cfg = Config(configfile, self.__version__)

    def _init_translation(self):
        language = self.config.get('general', 'language')
        try:
            translation = misc.get_translation('pyload', language)
        except Exception:
            self.log.debug("Unable to load `{}` language".format(language))
        else:
            translation.install(True)

    def _init_debug(self, debug, webdebug):
        debug_log = self.config.get('log', 'debug')
        verbose_log = self.config.get('log', 'verbose')
        debug_webui = config.get('webui', 'debug')

        self.debug = bool(debug) or debug_log
        self.debug_level = 2 if debug > 1 or verbose_log else 1
        self.webdebug = bool(webdebug) or debug_webui

    def _start_interfaces(self, webui, remote):
        # TODO: Parse `remote`
        if remote is not None or self.config.get('remote', 'activated'):
            self.log.debug("Activating remote interface ...")
            # self.rem.start_backends()
        elif not webui:
            webui = True

        if isinstance(webui, str):
            webui = True
            host, port = map(str.strip, webui.rsplit(':', 1))
        else:
            host, port = (None, None)

        kwgs = {
            'server': self.pyload.config.get('webui', 'server'),
            'host': host or self.pyload.config.get('webui', 'host'),
            'port': port or self.pyload.config.get('webui', 'port'),
            'key': self.pyload.config.get('ssl', 'key'),
            'cert': self.pyload.config.get('ssl', 'cert'),
            'ssl': self.pyload.config.get('ssl', 'activated')
        }
        if webui or self.config.get('webui', 'activated'):
            from pyload.thread.webui import WebServer
            self.webserver = WebServer(self)
            self.webserver.start()
            # self.svm.add('webui', **kwgs)
            # self.svm.start()

        Api.init_components()
        self.api = Api(self)

    def _init_database(self, restore):
        from pyload.database import DatabaseBackend
        from pyload.manager.file import FileManager

        self.db = DatabaseBackend(self)  #: the backend
        self.db.setup()

        self.files = FileManager(self)
        self.db.manager = self.files  #: ugly?

        if restore or not os.path.isfile("pyload.conf"):
            self.db.add_user("admin", "pyload")

    def _init_managers(self):
        from pyload.manager import (AccountManager, AddonManager, DownloadManager, EventManager,
                                    InteractionManager, PluginManager, RemoteManager,
                                    ThreadManager)

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.pluginmanager = self.pgm = PluginManager(self)
        self.interactionmanager = self.itm = InteractionManager(self)
        self.eventmanager = self.evm = EventManager(self)
        self.accountmanager = self.acm = AccountManager(self)
        self.threadmanager = self.thm = ThreadManager(self)
        self.downloadmanager = self.dlm = DownloadManager(self)
        self.addonmanager = self.adm = AddonManager(self)
        self.remotemanager = self.rem = RemoteManager(self)
        # self.servermanager      = self.svm = ServerManager(self)

    # TODO: Remove?
    def _init_requests(self):
        from pyload.network.factory import RequestFactory
        self.request = self.req = RequestFactory(self)

    def _init_process(self, profile):
        if not profile:
            profile = "default"

        pidname = "pyLoad-{}.pid".format(profile)
        tmpdir = tempfile.gettempdir()
        if pidname in os.listdir(tmpdir):
            msg = 'A pyLoad instance with profile `{}` is already running'.format(
                profile)
            raise Exception(msg)

        self.pidfile = os.path.join(tmpdir, pidname)
        self.profile = profile

        with open(self.pidfile, 'wb') as f:
            f.write(os.getpid())

        #: register exit signal
        signal.signal(signal.SIGTERM, lambda s, f: self.terminate())
        Process.__init__(self)

    def __init__(self, profile=None, configdir=None, refresh=0, remote=None,
                 webui=None, debug=0, webdebug=0):
        # NOTE: Don't change the init order!
        self._init_process(profile)
        self._init_debug(debug, webdebug)
        # NOTE: Logging level
        self._init_logger(logging.DEBUG if self.debug else logging.INFO)
        self._init_translation()
        self._init_config(configdir)

        self.log.debug("Initializing pyLoad ...")
        self._shutdown = False
        self._restart  = False
        if refresh:
            self._clean()
        self._init_permissions()
        self._init_database(refresh > 1)
        self._init_managers()
        self._init_requests()
        self._start_interfaces(webui, remote)

    def _set_process(self):
        profile = os.path.basename(os.getcwd())
        setproctitle.setproctitle('pyLoad-{}'.format(profile))

        niceness = self.config.get('general', 'niceness')
        sys.renice(niceness)

    def _set_storage(self):
        storage_folder = self.config.get(
            'general', 'storage_folder') or "downloads"
        makedirs(storage_folder)
        space_size = format.size(availspace(storage_folder))
        self.log.info(_("Available storage space: {}").format(space_size))

    def run(self):
        self.log.info(_("Starting pyLoad ..."))
        self.log.info(_("Version: {}").format(self.__version__))
        self.log.info(_("Profile: {}").format(os.path.abspath(os.getcwd())))

        self._set_storage()
        self._set_process()

        # TODO: Move in accountmanager
        self.log.info(_("Activating accounts ..."))
        self.acm.get_account_infos()
        # self.scheduler.enter(0, 0, self.acm.get_account_infos)

        self.adm.activate_plugins()

        self.config.save()  #: save so config files gets filled

        self.log.info(_("pyLoad is up and running"))
        self.evm.fire('pyload:started')

        # #: test api
        # from pyload.common.APIExerciser import start_api_exerciser
        # start_api_exerciser(self, 3)

        # #: some memory stats
        # from guppy import hpy
        # hp=hpy()
        # print(hp.heap())
        # import objgraph
        # objgraph.show_most_common_types(limit=30)
        # import memdebug
        # memdebug.start(8002)
        # from meliae import scanner
        # scanner.dump_all_objects(os.path.join(COREDIR, 'objs.json'))

        self.thm.pause = False
        try:
            while True:
                self.dlm.work()
                self.thm.work()
                self.itm.work()
                if self._restart:
                    raise Restart
                elif self._shutdown:
                    raise Shutdown
                self.scheduler.run()
        except Restart:
            self.restart()
        except Shutdown:
            self.shutdown()
        except Exception as e:
            self.log.critical(_("Critical error"), e.message)
            raise

    def _exit_logger(self):
        for handler in self.log.handlers:
            with closing(handler) as hdlr:
                self.log.remove_handler(hdlr)

    def restart(self):        
        self._stop()
        self.log.info(_("Restarting pyLoad ..."))
        self.evm.fire('pyload:restarting')
        self.start()

    def shutdown(self):
        try:
            if self.is_alive():
                self._stop()
        finally:
            self.log.info(_("Exiting pyLoad ..."))
            return Process.shutdown(self)

    def terminate(self):
        try:
            self._stop()
        except Exception:
            pass
        self.log.info(_("Exiting pyLoad ..."))
        return Process.terminate(self)

    def _stop(self):
        self.log.info(_("Stopping pyLoad ..."))
        self.evm.fire('pyload:stopping')
        try:
            # TODO: quit webserver
            self.dlm.shutdown()
            self.api.stop_all_downloads()
            self.adm.deactivate_addons()

        finally:
            self.evm.fire('pyload:stopped')
            remove(self.pidfile, trash=False)
            self.files.sync_save()
            self.db.shutdown()
            self._exit_logger()
