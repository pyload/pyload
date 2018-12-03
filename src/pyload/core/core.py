# -*- coding: utf-8 -*-
# AUTHOR: vuolter

import atexit
import builtins
import gettext
import locale
import os
import time

from pyload import PKGDIR
from .. import __version__ as PYLOAD_VERSION
from .. import __version_info__ as PYLOAD_VERSION_INFO
from .utils.utils import formatSize, freeSpace
from threading import Event


class Restart(Exception):

    __slots__ = []


class Exit(Exception):

    __slots__ = []


# TODO:
#  configurable auth system ldap/mysql
#  cron job like scheduler
#  plugin stack / multi decrypter
#  content attribute for files / sync status
#  sync with disk content / file manager / nested packages
#  sync between pyload cores
#  new attributes (date|sync status)
#  improve external scripts
class Core(object):

    LOCALE_DOMAIN = "core"
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "pyload"

    @property
    def version(self):
        return PYLOAD_VERSION

    @property
    def version_info(self):
        return PYLOAD_VERSION_INFO

    @property
    def running(self):
        return self._running.is_set()

    @property
    def debug(self):
        return self._debug

    # TODO: `restore` should reset config as well
    def __init__(self, userdir, cachedir, debug=None, restore=False):
        self._running = Event()
        self._do_restart = False
        self._do_exit = False
        self._ = lambda x: x
        self._debug = self.config.get("log", "debug") if debug is None else debug

        self.userdir = os.path.abspath(userdir)
        self.cachedir = os.path.abspath(cachedir)
        os.makedirs(self.userdir, exist_ok=True)
        os.makedirs(self.cachedir, exist_ok=True)

        # if self.tmpdir not in sys.path:
        # sys.path.append(self.tmpdir)

        # if refresh:
        # cleanpy(PACKDIR)

        # TODO: remove here
        self.lastClientConnected = 0

        self._init_config()
        self._init_log()
        self._init_database(restore)
        self._init_managers()
        self._init_network()
        self._init_api()
        self._init_webserver()

        atexit.register(self.terminate)

    def _init_config(self):
        from .config.config_parser import ConfigParser
        self.config = ConfigParser(self.userdir)

    def _init_log(self):
        from .log_factory import LogFactory
        self.logfactory = LogFactory(self)
        self.log = self.logfactory.get_logger('pyload')  # NOTE: forced debug mode from console not working

    def _init_network(self):
        from .network.request_factory import RequestFactory
        self.req = self.requestFactory = RequestFactory(self)
        builtins.REQUESTS = self.requestFactory

    def _init_api(self):
        from .api import Api
        self.api = Api(self)

    def _init_webserver(self):
        from pyload.webui.server_thread import WebServer
        self.webserver = WebServer(self)

    def _init_database(self, restore):
        from .database import DatabaseThread, FileHandler

        db_path = os.path.join(self.userdir, DatabaseThread.DB_FILENAME)
        newdb = not os.path.isfile(db_path)

        self.db = DatabaseThread(self)
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files  #: ugly?

        userpw = (self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD)
        # nousers = bool(self.db.listUsers())
        if restore or newdb:
            self.db.addUser(*userpw)
        if restore:
            self.log.warning(
                self._("Restored default login credentials `{}|{}`").format(*userpw)
            )

    def _init_managers(self):
        from .manager.account_manager import AccountManager
        from .manager.addon_manager import AddonManager
        from .manager.captcha_manager import CaptchaManager
        from .manager.event_manager import EventManager
        from .manager.plugin_manager import PluginManager
        from .remote.remote_manager import RemoteManager
        from .manager.thread_manager import ThreadManager
        from .scheduler import Scheduler

        self.scheduler = Scheduler(self)
        self.pgm = self.pluginManager = PluginManager(self)
        self.evm = self.eventManager = EventManager(self)
        self.acm = self.accountManager = AccountManager(self)
        self.thm = self.threadManager = ThreadManager(self)
        self.cpm = self.captchaManager = CaptchaManager(self)
        # TODO: Remove builtins.ADDONMANAGER
        builtins.ADDONMANAGER = self.adm = self.addonManager = AddonManager(self)
        self.rem = self.remoteManager = RemoteManager(self)

    def _setup_permissions(self):
        self.log.debug("Setup permissions...")

        if os.name == "nt":
            return

        change_group = self.config.get("permission", "change_group")
        change_user = self.config.get("permission", "change_user")

        if change_group:
            try:
                group = self.config.get("permission", "group")
                os.setgid(group[2])
            except Exception as exc:
                self.log.error(self._("Unable to change gid"))
                self.log.error(exc, exc_info=self.debug)

        if change_user:
            try:
                user = self.config.get("permission", "user")
                os.setuid(user[2])
            except Exception as exc:
                self.log.error(self._("Unable to change uid"))
                self.log.error(exc, exc_info=self.debug)

    def set_language(self, lang):
        localedir = os.path.join(PKGDIR, "locale")
        languages = (locale.locale_alias[lang.lower()].split("_", 1)[0],)
        self._set_language(self.LOCALE_DOMAIN, localedir, languages)

    def _set_language(self, *args, **kwargs):
        trans = gettext.translation(*args, **kwargs)
        try:
            self._ = trans.ugettext
        except AttributeError:
            self._ = trans.gettext

    def _setup_language(self):
        self.log.debug("Setup language...")

        lang = self.config.get("general", "language")
        if not lang:
            lc = locale.getlocale()[0] or locale.getdefaultlocale()[0]
            lang = lc.split("_", 1)[0] if lc else "en"

        try:
            self.set_language(lang)
        except IOError as exc:
            self.log.error(exc, exc_info=self.debug)
            self._set_language(self.LOCALE_DOMAIN, fallback=True)

    # def _setup_niceness(self):
    # niceness = self.config.get('general', 'niceness')
    # renice(niceness=niceness)
    # ioniceness = int(self.config.get('general', 'ioniceness'))
    # ionice(niceness=ioniceness)

    def _setup_storage(self):
        self.log.debug("Setup storage...")

        storage_folder = self.config.get("general", "storage_folder")
        # if storage_folder is None:
        # storage_folder = os.path.join(
        # builtins.USERDIR, self.DEFAULT_STORAGENAME)
        
        # NOTE: Remove in 0.6
        storage_folder = os.path.abspath(storage_folder)
        
        self.log.info(self._("Storage folder: {0}".format(storage_folder)))
        os.makedirs(storage_folder, exist_ok=True)
        
        avail_space = formatSize(freeSpace(storage_folder))
        self.log.info(self._("Available storage space: {0}").format(avail_space))

        self.config.save()  #: save so config files gets filled

    def _setup_network(self):
        self.log.debug("Setup network...")

        # TODO: Move to accountmanager
        self.log.info(self._("Activating accounts..."))
        self.acm.getAccountInfos()
        # self.scheduler.addJob(0, self.acm.getAccountInfos)

        self.log.info(self._("Activating Plugins..."))
        self.adm.coreReady()

    def _start_servers(self):
        if self.config.get("webui", "enabled"):
            self.webserver.start()
        if self.config.get("remote", "enabled"):
            self.remoteManager.startBackends()

    def _parse_linkstxt(self):
        link_file = os.path.join(self.userdir, "links.txt")
        try:
            with open(link_file) as f:
                if f.read().strip():
                    self.api.addPackage("links.txt", [link_file], 1)
        except Exception as exc:
            self.log.debug(exc)

    def start(self):
        self.log.info("Welcome to pyLoad v{0}".format(self.version))
        if self.debug:
            self.log.warning("*** DEBUG MODE ***")
        try:
            self.log.debug("Starting pyLoad...")
            # self.evm.fire('pyload:starting')
            self._running.set()

            self._setup_language()
            self._setup_permissions()

            self.log.info(self._("User directory: {0}").format(self.userdir))
            self.log.info(self._("Cache directory: {0}").format(self.cachedir))

            self._setup_storage()
            self._setup_network()
            # self._setup_niceness()

            # # some memory stats
            # from guppy import hpy
            # hp=hpy()
            # print(hp.heap())
            # import objgraph
            # objgraph.show_most_common_types(limit=30)
            # import memdebug
            # memdebug.start(8002)
            # from meliae import scanner
            # scanner.dump_all_objects(os.path.join(PACKDIR, 'objs.json'))

            self._start_servers()
            self._parse_linkstxt()
                        
            self.log.debug("pyLoad is up and running")
            # self.evm.fire('pyload:started')
            
            self.thm.pause = False  # NOTE: Recheck...
            while True:
                self._running.wait()
                self.threadManager.run()
                if self._do_restart:
                    raise Restart
                if self._do_exit:
                    raise Exit
                self.scheduler.run()
                time.sleep(1)

        except Restart:
            self.restart()

        except (Exit, KeyboardInterrupt, SystemExit):
            self.terminate()

        except Exception as exc:
            self.log.critical(exc, exc_info=True)
            self.terminate()

    # TODO: remove here
    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time.time()

    def restart(self):
        self.stop()
        self.log.info(self._("Restarting pyLoad..."))
        # self.evm.fire('pyload:restarting')
        self.start()

    def terminate(self):
        self.stop()
        self.log.info(self._("Exiting pyLoad..."))
        # self.tsm.exit()
        # self.db.exit()  # NOTE: Why here?
        self.logfactory.shutdown()
        # if cleanup:
        # self.log.info(self._("Deleting temp files..."))
        # remove(self.tmpdir, ignore_errors=True)

    def stop(self):
        try:
            self.log.debug("Stopping pyLoad...")
            # self.evm.fire('pyload:stopping')

            if self.webserver.is_alive():
                self.webserver.stop()

            for thread in self.threadManager.threads:
                thread.put("quit")

            for pyfile in self.files.cache.values():
                pyfile.abortDownload()

            self.addonManager.coreExiting()

        finally:
            self.files.syncSave()
            self.logfactory.shutdown()
            self._running.clear()
            # self.evm.fire('pyload:stopped')
