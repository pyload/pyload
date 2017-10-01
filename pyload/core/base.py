# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import atexit
import locale
import os
import sched
import time
from builtins import USERDIR
from contextlib import closing

from future import standard_library
from pkg_resources import resource_filename

from pyload.__about__ import __package__, __version__, __version_info__
from pyload.config import ConfigParser, config_defaults
from pyload.core.log import Logger
from pyload.core.network.factory import RequestFactory
from pyload.utils import format
from pyload.utils.fs import availspace, fullpath, makedirs
from pyload.utils.layer.safethreading import Event
from pyload.utils.misc import get_translation
from pyload.utils.system import (ionice, renice, set_process_group,
                                 set_process_user)

standard_library.install_aliases()


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

    DEFAULT_CONFIGFILENAME = 'config.ini'
    DEFAULT_LANGUAGE = 'english'
    DEFAULT_USERNAME = 'admin'
    DEFAULT_PASSWORD = 'pyload'
    DEFAULT_STORAGEDIRNAME = 'downloads'

    @property
    def version(self):
        return __version__

    @property
    def version_info(self):
        return __version_info__

    @property
    def running(self):
        return self.__running.is_set()

    def __init__(self, cfgdir, tmpdir, debug=None,
                 verbose=None, restore=False):
        self.__running = Event()
        self.__do_restart = False
        self.__do_exit = False
        self._ = lambda x: x

        self.cfgdir = fullpath(cfgdir)
        self.tmpdir = fullpath(tmpdir)

        os.chdir(self.cfgdir)

        # if self.tmpdir not in sys.path:
        # sys.path.append(self.tmpdir)

        # if refresh:
        # cleanpy(PACKDIR)

        self.config = ConfigParser(
            self.DEFAULT_CONFIGFILENAME, config_defaults)
        self.log = Logger(self, debug, verbose)
        self._init_database(restore)
        self._init_managers()
        self.request = self.req = RequestFactory(self)
        self._init_api()

    def _init_api(self):
        from pyload.api import Api
        self.api = Api(self)

    def _init_database(self, restore):
        from pyload.core.database import DatabaseBackend
        from pyload.core.datatype import Permission, Role

        # TODO: Move inside DatabaseBackend
        newdb = not os.path.isfile(DatabaseBackend.DB_FILE)
        self.db = DatabaseBackend(self)
        self.db.setup()

        if restore or newdb:
            self.db.add_user(
                self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD, Role.Admin,
                Permission.All)
        if restore:
            self.log.warning(
                self._('Restored default login credentials `admin|pyload`'))

    def _init_managers(self):
        from pyload.core.manager import (
            AccountManager, AddonManager, EventManager, ExchangeManager,
            FileManager, InfoManager, PluginManager, TransferManager)

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.filemanager = self.files = FileManager(self)
        self.pluginmanager = self.pgm = PluginManager(self)
        self.exchangemanager = self.exm = ExchangeManager(self)
        self.eventmanager = self.evm = EventManager(self)
        self.accountmanager = self.acm = AccountManager(self)
        self.infomanager = self.iom = InfoManager(self)
        self.transfermanager = self.tsm = TransferManager(self)
        self.addonmanager = self.adm = AddonManager(self)
        # self.remotemanager = self.rem = RemoteManager(self)
        # self.servermanager = self.svm = ServerManager(self)
        self.db.manager = self.files  # ugly?

    def _setup_permissions(self):
        if os.name == 'nt':
            return

        change_group = self.config.get('permission', 'change_group')
        change_user = self.config.get('permission', 'change_user')

        if change_group:
            try:
                group = self.config.get('permission', 'group')
                set_process_group(group)
            except Exception as exc:
                self.log.error(self._('Unable to change gid'), exc)

        if change_user:
            try:
                user = self.config.get('permission', 'user')
                set_process_user(user)
            except Exception as exc:
                self.log.error(self._('Unable to change uid'), exc)

    def set_language(self, lang):
        localedir = resource_filename(__package__, 'locale')
        lc = locale.locale_alias[lang.lower()].split('_', 1)[0]
        trans = get_translation('core', localedir, (lc,))
        try:
            self._ = trans.ugettext
        except AttributeError:
            self._ = trans.gettext

    def _setup_language(self):
        self.log.debug('Loading language ...')
        lang = self.config.get('general', 'language')
        default = self.DEFAULT_LANGUAGE
        if not lang:
            code = locale.getlocale()[0] or locale.getdefaultlocale()[0]
            lang = default if code is None else code.lower().split('_', 1)[0]
        try:
            self.set_language(lang)
        except Exception as exc:
            if lang == default:
                raise

            self.log.warning(
                self._('Unable to load `{0}` language, using default `{1}`').format(
                    lang, default),
                exc)
            self.set_language(default)

    # def _setup_niceness(self):
        # niceness = self.config.get('general', 'niceness')
        # renice(niceness=niceness)
        # ioniceness = int(self.config.get('general', 'ioniceness'))
        # ionice(niceness=ioniceness)

    def _setup_storage(self):
        storage_folder = self.config.get('general', 'storage_folder')
        if not storage_folder:
            storage_folder = os.path.join(USERDIR, self.DEFAULT_STORAGEDIRNAME)
        self.log.debug('Storage: {0}'.format(storage_folder))
        makedirs(storage_folder, exist_ok=True)
        avail_space = format.size(availspace(storage_folder))
        self.log.info(
            self._('Available storage space: {0}').format(avail_space))

    def _setup_network(self):
        # TODO: Move to accountmanager
        self.log.info(self._('Activating accounts ...'))
        self.acm.load_accounts()
        # self.scheduler.enter(0, 0, self.acm.load_accounts)
        self.adm.activate_addons()

    def run(self):
        try:
            self.log.info(self._('Running pyLoad ...'))
            self.evm.fire('pyload:starting')
            self.__running.set()

            self._setup_language()
            self._setup_permissions()
            self._setup_storage()
            self._setup_network()
            # self._setup_niceness()

            self.log.info(
                self._('Welcome to pyLoad v{0}').format(self.version))
            self.log.info(self._('Config directory: {0}').format(self.cfgdir))
            self.log.info(self._('Temp directory: {0}').format(self.tmpdir))
            self.evm.fire('pyload:started')

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

            self.tsm.pause = False  # NOTE: Recheck...
            while True:
                self.__running.wait()
                self.tsm.work()
                self.iom.work()
                self.exm.work()
                if self.__do_restart:
                    raise Restart
                if self.__do_exit:
                    raise Exit
                self.scheduler.run()

        except Restart:
            self.restart()
            return

        except (Exit, KeyboardInterrupt, SystemExit):
            pass

        except Exception as exc:
            self.log.critical(exc)
            self.exit()
            raise

        else:
            self.exit()

    def _remove_loggers(self):
        for handler in self.log.handlers:
            with closing(handler) as hdlr:
                self.log.removeHandler(hdlr)

    def restart(self):
        self.stop()
        self.log.info(self._('Restarting pyLoad ...'))
        self.evm.fire('pyload:restarting')
        self.run()

    @atexit.register
    def exit(self):
        self.stop()
        self.log.info(self._('Exiting pyLoad ...'))
        self.tsm.exit()
        self.db.exit()  # NOTE: Why here?
        self.config.close()
        self._remove_loggers()
        # if cleanup:
        # self.log.info(self._("Deleting temp files ..."))
        # remove(self.tmpdir, ignore_errors=True)

    def stop(self):
        try:
            self.log.info(self._('Stopping pyLoad ...'))
            self.evm.fire('pyload:stopping')
            self.adm.deactivate_addons()
            self.api.stop_all_downloads()
        finally:
            self.files.sync_save()
            self.__running.clear()
            self.evm.fire('pyload:stopped')
