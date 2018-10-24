# -*- coding: utf-8 -*-
# @author: vuolter

import atexit
import builtins
import gettext
import locale
import os
import sched
import time
from contextlib import closing

from future import standard_library
from pkg_resources import resource_filename

from .. import __version__ as PYLOAD_VERSION
from .. import __version_info__ as PYLOAD_VERSION_INFO
from builtins import PKGDIR

from .config.config_parser import ConfigParser
from .log_factory import LoggerFactory
from ..network.request_factory import RequestFactory
from .utils.utils import format
from .utils.utils.fs import availspace, fullpath, makedirs
from .utils.utils.layer.safethreading import Event
from .utils.utils.system import (ionice, renice, set_process_group,
                                 set_process_user)


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

    DEFAULT_LANGUAGE = 'english'
    DEFAULT_USERNAME = 'admin'
    DEFAULT_PASSWORD = 'pyload'

    @property
    def version(self):
        return PYLOAD_VERSION

    @property
    def version_info(self):
        return PYLOAD_VERSION_INFO

    @property
    def running(self):
        return self._running.is_set()

    # TODO: `restore` should reset config as well
    def __init__(self, userdir, cachedir, debug=False, restore=False):
        self._running = Event()
        self.__do_restart = False
        self.__do_exit = False
        self._ = lambda x: x

        self.userdir = os.path.abspath(userdir)
        self.cachedir = os.path.abspath(cachedir)
        os.makedirs(self.userdir, exist_ok=True)
        os.makedirs(self.cachedir, exist_ok=True)

        # if self.tmpdir not in sys.path:
        # sys.path.append(self.tmpdir)

        # if refresh:
        # cleanpy(PACKDIR)

        self.config = ConfigParser(self.userdir)
        self.debug = self.config.get(
            'log', 'debug') if debug is None else debug
        self.log = LoggerFactory(self, self.debug)

        self._init_database(restore)
        self._init_managers()

        self.request = self.req = RequestFactory(self)

        self._init_api()

        atexit.register(self.terminate)

    def _init_api(self):
        from .api import Api
        self.api = Api(self)

    def _init_webserver(self):
        if not self.config.get("webui", "enabled"):
            return
        self.webserver = WebServer(self)
        self.webserver.start()
            
    def _init_database(self, restore):
        db_path = os.path.join(self.userdir, DatabaseThread.DB_FILENAME)
        newdb = not os.path.isfile(db_path)
        
        self.db = DatabaseThread(self)
        self.db.setup()

        self.files = FileHandler(self)
        self.db.manager = self.files  #: ugly?
        
        userpw = (self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD)
        # nousers = bool(self.db.listUsers())
        if restore or newdb:
            self.db.add_user(*userpw)
        if restore:
            self.log.warning(
                self._('Restored default login credentials `{}|{}`').format(*userpw))

    def _init_managers(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.pluginmanager = self.pgm = PluginManager(self)
        self.exchangemanager = self.exm = ExchangeManager(self)
        self.eventmanager = self.evm = EventManager(self)
        self.accountmanager = self.acm = AccountManager(self)
        self.infomanager = self.iom = InfoManager(self)
        self.transfermanager = self.tsm = TransferManager(self)
        # TODO: Remove builtins.ADDONMANAGER
        builtins.ADDONMANAGER = self.addonmanager = self.adm = AddonManager(
            self)
        # self.remotemanager = self.rem = RemoteManager(self)
        # self.servermanager = self.svm = ServerManager(self)
        self.db.manager = self.files  # ugly?

    def _setup_permissions(self):
        self.log.debug('Setup permissions...')

        if os.name == 'nt':
            return

        change_group = self.config.get('permission', 'change_group')
        change_user = self.config.get('permission', 'change_user')

        if change_group:
            try:
                group = self.config.get('permission', 'group')
                set_process_group(group)
            except Exception as exc:
                self.log.error(self._('Unable to change gid'))
                self.log.error(exc, exc_info=self.debug)

        if change_user:
            try:
                user = self.config.get('permission', 'user')
                set_process_user(user)
            except Exception as exc:
                self.log.error(self._('Unable to change uid'))
                self.log.error(exc, exc_info=self.debug)

    def set_language(self, lang):
        domain = 'core'
        localedir = os.path.join(PKGDIR, 'locale')
        languages = (locale.locale_alias[lang.lower()].split('_', 1)[0],)
        self._set_language(domain, localedir, languages)

    def _set_language(self, *args, **kwargs):
        trans = gettext.translation(*args, **kwargs)
        try:
            self._ = trans.ugettext
        except AttributeError:
            self._ = trans.gettext

    def _setup_language(self):
        self.log.debug('Setup language...')

        lang = self.config.get('general', 'language')
        if not lang:
            lc = locale.getlocale()[0] or locale.getdefaultlocale()[0]
            lang = lc.split('_', 1)[0] if lc else 'en'

        try:
            self.set_language(lang)
        except IOError as exc:
            self.log.error(exc, exc_info=self.debug)
            self._set_language('core', fallback=True)

    # def _setup_niceness(self):
        # niceness = self.config.get('general', 'niceness')
        # renice(niceness=niceness)
        # ioniceness = int(self.config.get('general', 'ioniceness'))
        # ionice(niceness=ioniceness)

    def _setup_storage(self):
        self.log.debug('Setup storage...')

        storage_folder = self.config.get('general', 'storage_folder')
        # if storage_folder is None:
            # storage_folder = os.path.join(
                # builtins.USERDIR, self.DEFAULT_STORAGENAME)
        self.log.info(self._('Storage: {0}'.format(storage_folder)))
        makedirs(storage_folder, exist_ok=True)
        avail_space = format.size(availspace(storage_folder))
        self.log.info(
            self._('Available storage space: {0}').format(avail_space))

    def _setup_network(self):
        self.log.debug('Setup network...')

        # TODO: Move to accountmanager
        self.log.info(self._('Activating accounts...'))
        self.acm.load_accounts()
        # self.scheduler.enter(0, 0, self.acm.load_accounts)
        self.adm.activate_addons()

    def start(self):
        self.log.info('Welcome to pyLoad v{0}'.format(self.version))
        if self.debug:
            self.log.warning('*** DEBUG MODE ***')
        try:
            self.log.debug('Starting pyLoad...')
            self.evm.fire('pyload:starting')
            self._running.set()

            self._setup_language()
            self._setup_permissions()

            self.log.info(self._('User directory: {0}').format(self.userdir))
            self.log.info(self._('Cache directory: {0}').format(self.cachedir))

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

            self.log.debug('pyLoad is up and running')
            self.evm.fire('pyload:started')

            self.tsm.pause = False  # NOTE: Recheck...
            while True:
                self._running.wait()
                # self.tsm.work()
                # self.iom.work()
                # self.exm.work()
                if self.__do_restart:
                    raise Restart
                if self.__do_exit:
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

    def isClientConnected(self):
        return (self.lastClientConnected + 30) > time.time()
        
    def restart(self):
        self.stop()
        self.log.info(self._('Restarting pyLoad...'))
        # self.evm.fire('pyload:restarting')
        self.start()

    def terminate(self):
        self.stop()
        self.log.info(self._('Exiting pyLoad...'))
        # self.tsm.exit()
        # self.db.exit()  # NOTE: Why here?
        self.logfactory.shutdown()
        # if cleanup:
        # self.log.info(self._("Deleting temp files..."))
        # remove(self.tmpdir, ignore_errors=True)

    def stop(self):
        try:
            self.log.debug('Stopping pyLoad...')
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
            