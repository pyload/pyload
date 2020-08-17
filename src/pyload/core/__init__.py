# -*- coding: utf-8 -*-
#      ____________
#   _ /       |    \ ___________ _ _______________ _ ___ _______________
#  /  |    ___/    |   _ __ _  _| |   ___  __ _ __| |   \\    ___  ___ _\
# /   \___/  ______/  | '_ \ || | |__/ _ \/ _` / _` |    \\  / _ \/ _ `/ \
# \       |   o|      | .__/\_, |____\___/\__,_\__,_|    // /_//_/\_, /  /
#  \______\    /______|_|___|__/________________________//______ /___/__/
#          \  /
#           \/

import atexit
import gettext
import locale
import os
import tempfile
import time

from pyload import PKGDIR, APPID, USERHOMEDIR
from .. import __version__ as PYLOAD_VERSION
from .. import __version_info__ as PYLOAD_VERSION_INFO
from .utils import format, fs
from .utils.misc import reversemap
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
class Core:

    LOCALE_DOMAIN = APPID
    DEFAULT_USERNAME = APPID
    DEFAULT_PASSWORD = APPID
    DEFAULT_DATADIR = os.path.join(
        os.getenv("APPDATA") or USERHOMEDIR, "pyLoad" if os.name == "nt" else ".pyload"
    )
    DEFAULT_TMPDIR = os.path.join(tempfile.gettempdir(), "pyLoad")
    DEFAULT_STORAGEDIR = os.path.join(USERHOMEDIR, "Downloads", "pyLoad")
    DEBUG_LEVEL_MAP = {"debug": 1, "trace": 2, "stack": 3}

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

    # NOTE: should `restore` reset config as well?
    def __init__(self, userdir, tempdir, storagedir, debug=None, restore=False):
        self._running = Event()
        self._do_restart = False
        self._do_exit = False
        self._ = lambda x: x
        self._debug = 0

        # if self.tmpdir not in sys.path:
        # sys.path.append(self.tmpdir)

        # if refresh:
        # cleanpy(PACKDIR)

        self._init_config(userdir, tempdir, storagedir, debug)
        self._init_log()

        self._init_database(restore)
        self._init_network()
        self._init_api()
        self._init_managers()
        self._init_webserver()

        atexit.register(self.terminate)

        # TODO: Remove...
        self.last_client_connected = 0

    def _init_config(self, userdir, tempdir, storagedir, debug):
        from .config.parser import ConfigParser

        self.userdir = os.path.realpath(userdir)
        self.tempdir = os.path.realpath(tempdir)
        os.makedirs(self.userdir, exist_ok=True)
        os.makedirs(self.tempdir, exist_ok=True)

        self.config = ConfigParser(self.userdir)

        if debug is None:
            if self.config.get("general", "debug_mode"):
                debug_level = self.config.get("general", "debug_level")
                self._debug = self.DEBUG_LEVEL_MAP[debug_level]
        else:
            self._debug = max(0, int(debug))

        os.makedirs(storagedir, exist_ok=True)
        self.config.set("general", "storage_folder", storagedir)

        self.config.save()  #: save so config files gets filled

    def _init_log(self):
        from .log_factory import LogFactory

        self.logfactory = LogFactory(self)
        self.log = self.logfactory.get_logger(
            "pyload"
        )  # NOTE: forced debug mode from console is not working actually

        self.log.warning(f"*** Welcome to pyLoad {self.version} ***")

    def _init_network(self):
        from .network import request_factory
        from .network.request_factory import RequestFactory

        self.req = self.request_factory = RequestFactory(self)

    def _init_api(self):
        from .api import Api

        self.api = Api(self)

    def _init_webserver(self):
        from pyload.webui.webserver_thread import WebServerThread

        self.webserver = WebServerThread(self)

    def _init_database(self, restore):
        from .database import DatabaseThread

        db_path = os.path.join(self.userdir, DatabaseThread.DB_FILENAME)
        newdb = not os.path.isfile(db_path)

        self.db = DatabaseThread(self)
        self.db.setup()

        userpw = (self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD)
        # nousers = bool(self.db.list_users())
        if restore or newdb:
            self.db.add_user(*userpw)
        if restore:
            self.log.warning(
                self._(
                    "Successfully restored default login credentials `{}|{}`"
                ).format(*userpw)
            )

    def _init_managers(self):
        from .managers.account_manager import AccountManager
        from .managers.addon_manager import AddonManager
        from .managers.captcha_manager import CaptchaManager
        from .managers.event_manager import EventManager
        from .managers.plugin_manager import PluginManager
        from .managers.thread_manager import ThreadManager
        from .managers.file_manager import FileManager

        from .scheduler import Scheduler

        self.files = self.file_manager = FileManager(self)
        self.scheduler = Scheduler(self)

        self.pgm = self.plugin_manager = PluginManager(self)
        self.evm = self.event_manager = EventManager(self)
        self.acm = self.account_manager = AccountManager(self)
        self.thm = self.thread_manager = ThreadManager(self)
        self.cpm = self.captcha_manager = CaptchaManager(self)
        self.adm = self.addon_manager = AddonManager(self)

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
                self.log.warning(
                    self._("Unable to change gid"),
                    exc,
                    exc_info=self.debug > 1,
                    stack_info=self.debug > 2,
                )

        if change_user:
            try:
                user = self.config.get("permission", "user")
                os.setuid(user[2])
            except Exception as exc:
                self.log.warning(
                    self._("Unable to change uid"),
                    exc,
                    exc_info=self.debug > 1,
                    stack_info=self.debug > 2,
                )

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
            self.log.warning(exc, exc_info=self.debug > 1, stack_info=self.debug > 2)
            self._set_language(self.LOCALE_DOMAIN, fallback=True)

    # def _setup_niceness(self):
    # niceness = self.config.get('general', 'niceness')
    # renice(niceness=niceness)
    # ioniceness = int(self.config.get('general', 'ioniceness'))
    # ionice(niceness=ioniceness)

    def _setup_network(self):
        self.log.debug("Setup network...")

        # TODO: Move to accountmanager
        self.log.info(self._("Activating accounts..."))
        self.acm.get_account_infos()
        # self.scheduler.add_job(0, self.acm.get_account_infos)

        self.log.info(self._("Activating Plugins..."))
        self.adm.core_ready()

    def _start_webserver(self):
        if not self.config.get("webui", "enabled"):
            return
        self.webserver.start()

    # def _parse_linkstxt(self):
    #     link_file = os.path.join(self.userdir, "links.txt")
    #     try:
    #         with open(link_file) as fp:
    #             if fp.read().strip():
    #                 self.api.add_package("links.txt", [link_file], 1)
    #     except Exception as exc:
    #         self.log.debug(exc, exc_info=self.debug > 1, stack_info=self.debug > 2)

    def start(self):
        try:
            self.log.debug("Starting core...")

            debug_level = reversemap(self.DEBUG_LEVEL_MAP)[self.debug].upper()
            self.log.debug(f"Debug level: {debug_level}")

            # self.evm.fire('pyload:starting')
            self._running.set()

            self._setup_language()
            self._setup_permissions()

            self.log.info(self._("User directory: {}").format(self.userdir))
            self.log.info(self._("Cache directory: {}").format(self.tempdir))

            storage_folder = self.config.get("general", "storage_folder")
            self.log.info(self._("Storage directory: {}".format(storage_folder)))

            avail_space = format.size(fs.free_space(storage_folder))
            self.log.info(self._("Storage free space: {}").format(avail_space))

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

            self._start_webserver()
            # self._parse_linkstxt()

            self.log.debug("*** pyLoad is up and running ***")
            # self.evm.fire('pyload:started')

            self.thm.pause = False  # NOTE: Recheck...
            while True:
                self._running.wait()
                self.thread_manager.run()
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
            self.log.critical(exc, exc_info=True, stack_info=self.debug > 2)
            self.terminate()

    # TODO: Remove
    def is_client_connected(self):
        return (self.last_client_connected + 30) > time.time()

    def restart(self):
        self.stop()
        self.log.info(self._("Restarting core..."))
        # self.evm.fire('pyload:restarting')
        self.start()

    def terminate(self):
        self.stop()
        self.log.info(self._("Exiting core..."))
        # self.tsm.exit()
        # self.db.exit()  # NOTE: Why here?
        self.logfactory.shutdown()
        # if cleanup:
        # self.log.info(self._("Deleting temp files..."))
        # remove(self.tmpdir)

    def stop(self):
        try:
            self.log.debug("Stopping core...")
            # self.evm.fire('pyload:stopping')

            for thread in self.thread_manager.threads:
                thread.put("quit")

            for pyfile in self.files.cache.values():
                pyfile.abort_download()

            self.addon_manager.core_exiting()

        finally:
            self.files.sync_save()
            self._running.clear()
            # self.evm.fire('pyload:stopped')
