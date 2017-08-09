# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals

import locale
import logging
import logging.handlers
import os
import sched
import signal
import sys
import tempfile
import time
from builtins import TMPDIR, USERDIR, int, str
from contextlib import closing
from multiprocessing import Event, Process

import portalocker
import psutil
from future import standard_library
from pkg_resources import resource_filename

from pyload.config import ConfigParser
from pyload.utils import format
from pyload.utils.check import ismodule
from pyload.utils.fs import availspace, fullpath, makedirs
from pyload.utils.misc import get_translation
from pyload.utils.system import (ionice, renice, set_process_group,
                                 set_process_name, set_process_user)

from pyload.core.network.factory import RequestFactory
from .__about__ import (__namespace__, __package__, __version__,
                        __version_info__)
from .config import config_defaults, session_defaults

standard_library.install_aliases()

try:
    import colorlog
except ImportError:
    colorlog = None


_pmap = {}


class Restart(Exception):

    __slots__ = []


class Shutdown(Exception):

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
class Core(Process):

    __SESSIONFILENAME = 'session.ini'
    __CONFIGFILENAME = 'config.ini'
    DEFAULT_LANGUAGE = 'english'
    DEFAULT_USERNAME = 'admin'
    DEFAULT_PASSWORD = 'pyload'
    DEFAULT_STORAGEDIRNAME = 'downloads'
    DEFAULT_LOGDIRNAME = 'logs'
    DEFAULT_LOGFILENAME = 'log.txt'

    def _init_consolelogger(self):
        if self.config.get('log', 'color_console') and ismodule('colorlog'):
            fmt = "%(label)s %(levelname)-8s %(reset)s %(log_color)s%(asctime)s  %(message)s"
            datefmt = "%Y-%m-%d  %H:%M:%S"
            primary_colors = {
                'DEBUG': "bold,cyan",
                'WARNING': "bold,yellow",
                'ERROR': "bold,red",
                'CRITICAL': "bold,purple",
            }
            secondary_colors = {
                'label': {
                    'DEBUG': "bold,white,bg_cyan",
                    'INFO': "bold,white,bg_green",
                    'WARNING': "bold,white,bg_yellow",
                    'ERROR': "bold,white,bg_red",
                    'CRITICAL': "bold,white,bg_purple",
                }
            }
            consoleform = colorlog.ColoredFormatter(
                fmt, datefmt, primary_colors,
                secondary_log_colors=secondary_colors)
        else:
            fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            consoleform = logging.Formatter(fmt, datefmt)

        consolehdlr = logging.StreamHandler(sys.stdout)
        consolehdlr.setFormatter(consoleform)
        self.log.addHandler(consolehdlr)

    def _init_syslogger(self):
        # try to mimic to normal syslog messages
        fmt = "%(asctime)s %(name)s: %(message)s"
        datefmt = "%b %e %H:%M:%S"
        syslogform = logging.Formatter(fmt, datefmt)
        syslogaddr = None

        syslog = self.config.get('log', 'syslog')
        if syslog == 'remote':
            syslog_host = self.config.get('log', 'syslog_host')
            syslog_port = self.config.get('log', 'syslog_port')
            syslogaddr = (syslog_host, syslog_port)
        else:
            syslog_folder = self.config.get('log', 'syslog_folder')
            if syslogaddr:
                syslogaddr = syslog_folder
            elif sys.platform == 'darwin':
                syslogaddr = '/var/run/syslog'
            elif os.name != 'nt':
                syslogaddr = '/dev/log'

        sysloghdlr = logging.handlers.SysLogHandler(syslogaddr)
        sysloghdlr.setFormatter(syslogform)
        self.log.addHandler(sysloghdlr)

    def _init_filelogger(self):
        fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        fileform = logging.Formatter(fmt, datefmt)

        logfile_folder = self.config.get('log', 'logfile_folder')
        if not logfile_folder:
            logfile_folder = self.DEFAULT_LOGDIRNAME
        makedirs(logfile_folder, exist_ok=True)

        logfile_name = self.config.get('log', 'logfile_name')
        if not logfile_name:
            logfile_name = self.DEFAULT_LOGFILENAME
        logfile = os.path.join(logfile_folder, logfile_name)

        if self.config.get('log', 'rotate'):
            logfile_size = self.config.get('log', 'logfile_size') << 10
            max_logfiles = self.config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(
                logfile, maxBytes=logfile_size, backupCount=max_logfiles,
                encoding=locale.getpreferredencoding(do_setlocale=False))
        else:
            filehdlr = logging.FileHandler(
                logfile, encoding=locale.getpreferredencoding(
                    do_setlocale=False))

        filehdlr.setFormatter(fileform)
        self.log.addHandler(filehdlr)

    # TODO: Extend `logging.Logger` like `..plugin.Log`
    def _init_logger(self):
        level = logging.DEBUG if self.debug else logging.INFO

        # Init logger
        self.log = logging.getLogger()
        self.log.setLevel(level)

        # Set console handler
        self._init_consolelogger()

        # Set syslog handler
        if self.config.get('log', 'syslog') != 'no':
            self._init_syslogger()

        # Set file handler
        if self.config.get('log', 'logfile'):
            self._init_filelogger()

    def _setup_permissions(self):
        if os.name == 'nt':
            return None

        change_group = self.config.get('permission', 'change_group')
        change_user = self.config.get('permission', 'change_user')

        if change_group:
            try:
                group = self.config.get('permission', 'group')
                set_process_group(group)
            except Exception as e:
                self.log.error(self._("Unable to change gid"), str(e))

        if change_user:
            try:
                user = self.config.get('permission', 'user')
                set_process_user(user)
            except Exception as e:
                self.log.error(self._("Unable to change uid"), str(e))

    def set_language(self, lang):
        localedir = resource_filename(__package__, 'locale')
        lc = locale.locale_alias[lang.lower()].split('_', 1)[0]
        trans = get_translation('core', localedir, (lc,))
        try:
            self._ = trans.ugettext
        except AttributeError:
            self._ = trans.gettext

    def _setup_language(self):
        self.log.debug("Loading language ...")
        lang = self.config.get('general', 'language')
        default = self.DEFAULT_LANGUAGE
        if not lang:
            code = locale.getlocale()[0] or locale.getdefaultlocale()[0]
            lang = default if code is None else code.lower().split('_', 1)[0]
        try:
            self.set_language(lang)
        except Exception as e:
            if lang == default:
                raise
            self.log.warning(
                self._("Unable to load `{0}` language, "
                       "use default `{1}`").format(lang, default),
                str(e))
            self.set_language(default)

    def _setup_debug(self):
        if self.__debug is None:
            debug_log = self.config.get('log', 'debug')
            verbose_log = self.config.get('log', 'verbose')
            self.__debug = 0 if not debug_log else 2 if verbose_log else 1

    # def start_interface(self, webui=None, rpc=None):
        # if webui is None:
            # webui = self.__webui
        # if rpc is None:
            # rpc = self.__rpc

        # # TODO: Parse `remote`
        # if rpc or self.config.get('rpc', 'activated'):
            # self.log.debug("Activating RPC interface ...")
            # self.rem.start()
        # elif not webui:
            # webui = True

        # TODO: Parse remote host:port

        # if isinstance(webui, str):
            # host, port = map(str.strip, webui.rsplit(':', 1))
            # webui = True
        # else:
            # host, port = (None, None)
        # kwgs = {
            # 'server': self.config.get('webui', 'server'),
            # 'host': host or self.config.get('webui', 'host'),
            # 'port': port or self.config.get('webui', 'port'),
            # 'key': self.config.get('ssl', 'key'),
            # 'cert': self.config.get('ssl', 'cert'),
            # 'ssl': self.config.get('ssl', 'activated')
        # }
        # if webui or self.config.get('webui', 'activated'):
            # from .thread.webserver import WebServer
            # self.webserver = WebServer(self)
            # self.webserver.start()
            # self.svm.add('webui', **kwgs)
            # self.svm.start()

    def _init_api(self):
        from .api import Api
        self.api = Api(self)

    def _init_database(self):
        from .database import DatabaseBackend
        from .datatype import Permission, Role

        # TODO: Move inside DatabaseBackend
        newdb = not os.path.isfile(DatabaseBackend.DB_FILE)
        self.db = DatabaseBackend(self)
        self.db.setup()

        if self.__restore or newdb:
            self.db.add_user(
                self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD, Role.Admin,
                Permission.All)
        if self.__restore:
            self.log.warning(
                self._("Restored default login credentials `admin|pyload`"))

    def _init_managers(self):
        from .manager import (
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

    def _init_requests(self):
        self.request = self.req = RequestFactory(self)

    def _init_config(self):
        session = ConfigParser(self.__SESSIONFILENAME, session_defaults)

        flags = portalocker.LOCK_EX | portalocker.LOCK_NB
        portalocker.lock(session.fp, flags)

        profiledir = os.path.join(self.configdir, self.profile)
        psp = psutil.Process()
        session.set('current', 'id', time.time())
        session.set('current', 'profile', 'path', profiledir)
        session.set('current', 'profile', 'pid', psp.pid)
        session.set('current', 'profile', 'ctime', psp.create_time())

        self.config = ConfigParser(self.__CONFIGFILENAME, config_defaults)
        self.session = session

    def _init_cache(self):
        # Re-use cache
        tempdir = self.__tempdir
        if tempdir is None:
            tempdir = self.session.get('previous', 'cache', 'path')
            if tempdir is None or not os.path.isdir(tempdir):
                pydir = os.path.join(TMPDIR, __namespace__)
                makedirs(pydir, exist_ok=True)
                tempdir = tempfile.mkdtemp(dir=pydir)
        self.session.set('current', 'cache', 'path', tempdir)
        self.cachedir = tempdir
        # if tempdir not in sys.path:
        # sys.path.append(tempdir)

    def _register_signals(self):
        shutfn = lambda s, f: self.shutdown()
        quitfn = lambda s, f: self.terminate()
        try:
            if os.name == 'nt':
                # signal.signal(signal.CTRL_C_EVENT, shutfn)
                signal.signal(signal.CTRL_BREAK_EVENT, shutfn)
            else:
                signal.signal(signal.SIGTERM, shutfn)
                # signal.signal(signal.SIGINT, shutfn)
                signal.signal(signal.SIGQUIT, quitfn)
                # signal.signal(signal.SIGTSTP, lambda s, f: self.stop())
                # signal.signal(signal.SIGCONT, lambda s, f: self.run())
        except Exception:
            pass

    def __init__(self, profiledir=None, tempdir=None, debug=None,
                 restore=None):
        self.__running = Event()
        self.__do_restart = False
        self.__do_shutdown = False
        self.__debug = debug if debug is None else int(debug)
        self.__restore = bool(restore)
        self.__tempdir = tempdir
        self._ = lambda x: x

        self._init_profile(profiledir)

        # if refresh:
        # cleanpy(PACKDIR)

        Process.__init__(self)

    @property
    def version(self):
        return __version__

    @property
    def version_info(self):
        return __version_info__

    @property
    def running(self):
        return self.__running.is_set()

    @property
    def debug(self):
        return self.__debug

    def _init_profile(self, profiledir):
        profiledir = fullpath(profiledir)
        os.chdir(profiledir)
        self.configdir, self.profile = os.path.split(profiledir)

    def _setup_process(self):
        try:
            set_process_name('pyLoad')
        except AttributeError:
            pass
        niceness = self.config.get('general', 'niceness')
        renice(niceness=niceness)
        ioniceness = int(self.config.get('general', 'ioniceness'))
        ionice(niceness=ioniceness)

    def _setup_storage(self):
        storage_folder = self.config.get('general', 'storage_folder')
        if not storage_folder:
            storage_folder = os.path.join(USERDIR, self.DEFAULT_STORAGEDIRNAME)
        self.log.debug("Storage: {0}".format(storage_folder))
        makedirs(storage_folder, exist_ok=True)
        avail_space = format.size(availspace(storage_folder))
        self.log.info(
            self._("Available storage space: {0}").format(avail_space))

    def _workloop(self):
        self.__running.set()
        self.tsm.pause = False  # NOTE: Recheck...
        while True:
            self.__running.wait()
            self.tsm.work()
            self.iom.work()
            self.exm.work()
            if self.__do_restart:
                raise Restart
            if self.__do_shutdown:
                raise Shutdown
            self.scheduler.run()

    def _start_plugins(self):
        # TODO: Move to accountmanager
        self.log.info(self._("Activating accounts ..."))
        self.acm.load_accounts()
        # self.scheduler.enter(0, 0, self.acm.load_accounts)
        self.adm.activate_addons()

    def _show_info(self):
        self.log.info(self._("Welcome to pyLoad v{0}").format(self.version))

        self.log.info(self._("Profile: {0}").format(self.profile))
        self.log.info(self._("Config directory: {0}").format(self.configdir))

        self.log.debug("Cache directory: {0}".format(self.cachedir))

    def run(self):
        self._init_config()
        self._init_cache()
        self._setup_debug()
        self._init_logger()
        try:
            self.log.debug("Running pyLoad ...")

            self._setup_language()
            self._setup_permissions()
            self._init_database()
            self._init_managers()
            self._init_requests()
            self._init_api()

            self._show_info()
            self._setup_storage()
            self._start_plugins()
            self._setup_process()

            self.log.info(self._("pyLoad is up and running"))
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

            self._workloop()

        except Restart:
            self.restart()
        except Shutdown:
            self.shutdown()
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()
        except Exception as e:
            self.log.critical(str(e))
            self.terminate()
            raise
        else:
            self.shutdown()

    def _remove_loggers(self):
        for handler in self.log.handlers:
            with closing(handler) as hdlr:
                self.log.removeHandler(hdlr)

    def restart(self):
        self.stop()
        self.log.info(self._("Restarting pyLoad ..."))
        self.evm.fire('pyload:restarting')
        self.start()

    def _register_instance(self):
        profiledir = os.path.join(self.configdir, self.profile)
        if profiledir in _pmap:
            raise RuntimeError(
                "A pyLoad instance using profile `{0}` "
                "is already running".format(
                    profiledir))
        _pmap[profiledir] = self

    def _unregister_instance(self):
        profiledir = os.path.join(self.configdir, self.profile)
        _pmap.pop(profiledir, None)

    def _close_session(self):
        id = self.session.get('previous', 'id')
        self.session[id] = self.session['previous']
        self.session['previous'] = self.session['current']
        self.session['current'].reset()
        self.session.close()

    def terminate(self):
        try:
            self.log.debug("Killing pyLoad ...")
            self._unregister_instance()
            self._close_session()
        finally:
            Process.terminate(self)

    def shutdown(self):
        try:
            self.stop()
            self.log.info(self._("Exiting pyLoad ..."))
            self.tsm.shutdown()
            self.db.shutdown()  # NOTE: Why here?
            self.config.close()
            self._remove_loggers()
            # if cleanup:
            # self.log.info(self._("Deleting temp files ..."))
            # remove(self.tempdir, ignore_errors=True)
        finally:
            self.terminate()

    def start(self):
        if not self.is_alive():
            self._register_instance()
            self._register_signals()
            Process.start(self)
        elif not self.running:
            self.log.info(self._("Starting pyLoad ..."))
            self.evm.fire('pyload:starting')
            self.__running.set()

    def stop(self):
        if not self.running:
            return None
        try:
            self.log.info(self._("Stopping pyLoad ..."))
            self.evm.fire('pyload:stopping')
            self.adm.deactivate_addons()
            self.api.stop_all_downloads()
        finally:
            self.files.sync_save()
            self.__running.clear()
            self.evm.fire('pyload:stopped')
