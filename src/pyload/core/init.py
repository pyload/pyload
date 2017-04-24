# -*- coding: utf-8 -*-
# @author: vuolter

from __future__ import absolute_import, unicode_literals
from future import standard_library

import builtins
import errno
import fcntl
import imp
import io
import logging
import logging.handlers
import os
import sched
import signal
import tempfile
import time
from builtins import DATADIR, PACKDIR, REQUEST, TMPDIR, USERDIR, int, map, str
from contextlib import closing
from locale import getpreferredencoding
from multiprocessing import Event, Process

import autoupgrade
import daemonize
import psutil

from .config import make_config
from pyload.config import ConfigParser
from pyload.utils import convert, format, sys
from pyload.utils.check import ismodule
from pyload.utils.misc import install_translation
from pyload.utils.path import availspace, makedirs, pyclean, remove
from pyload.utils.struct.info import Info

standard_library.install_aliases()

try:
    import colorlog
except ImportError:
    pass

    
def _gen_profiledir(profile=None, configdir=None):
    if not profile:
        profile = 'default'
    if configdir:
        configdir = os.path.expanduser(configdir)
    else:
        configdir = os.path.join(
            DATADIR, 'pyLoad' if os.name == 'nt' else '.pyload')
    profiledir = os.path.abspath(os.path.join(configdir, profile))
    makedirs(profiledir)
    return profiledir
    
    
def _get_setup_map():
    """
    Load info dict from `setup.py`.
    """
    fp, fname, desc = imp.find_module('setup', PACKDIR)
    module = imp.load_module('_setup', fp, fname, desc)
    return module.SETUP_MAP

__setup_map = _get_setup_map()
__core_version = convert.to_version(__setup_map['version'])


class Restart(Exception):
    # __slots__ = []
    def __str__(self):
        return """<RestartSignal {0}>""".format(self.message)


class Shutdown(Exception):
    # __slots__ = []
    def __str__(self):
        return """<ShutdownSignal {0}>""".format(self.message)


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

    # __slots__ = [
        # '_cleanup', '_restart', '_shutdown', '_rpc', '_webui', 'accountmanager',
        # 'acm', 'addonmanager', 'adm', 'api', 'configdir', 'configfile', 'db',
        # 'debug', 'debug_level', 'tsm', 'transfermanager', 'eventmanager', 'evm',
        # 'filemanager', 'files', 'exchangemanager', 'exm', 'log', 'pgm',
        # 'pid', 'pidfile', 'pluginmanager', 'profile', 'profiledir', 'rem',
        # 'remotemanager', 'req', 'request', 'running', 'scheduler', 'iom',
        # 'infomanager', 'tmpdir', 'version', 'webserver'
    # ]

    @property
    def version(self):
        return __core_version

    def _set_consolelog_handler(self):
        if self.config.get('log', 'color_console') and ismodule('colorlog'):
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
        else:
            fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
            datefmt = "%Y-%m-%d %H:%M:%S"
            consoleform = logging.Formatter(fmt, datefmt)

        consolehdlr = logging.StreamHandler(sys.stdout)
        consolehdlr.setFormatter(consoleform)
        self.log.addHandler(consolehdlr)

    def _set_syslog_handler(self):
        #: try to mimic to normal syslog messages
        fmt = "%(asctime)s %(name)s: %(message)s"
        datefmt = "%b %e %H:%M:%S"
        syslogform = logging.Formatter(fmt, datefmt)
        syslogaddr = None

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

    def _set_logfile_handler(self):
        fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        fileform = logging.Formatter(fmt, datefmt)

        logfile = os.path.join(logfile_folder, 'log.txt')
        if self.config.get('log', 'rotate'):
            logfile_size = self.config.get('log', 'logfile_size') << 10
            max_logfiles = self.config.get('log', 'max_logfiles')
            filehdlr = logging.handlers.RotatingFileHandler(logfile,
                                                            maxBytes=logfile_size,
                                                            backupCount=max_logfiles,
                                                            encoding=getpreferredencoding())
        else:
            filehdlr = logging.FileHandler(
                logfile, encoding=getpreferredencoding())

        filehdlr.setFormatter(fileform)
        self.log.addHandler(filehdlr)

    def _mklogdir(self):
        logfile_folder = self.config.get('log', 'logfile_folder')
        if not logfile_folder:
            logfile_folder = os.path.abspath("logs")
        makedirs(logfile_folder)

    # TODO: Extend `logging.Logger` like `..plugin.Log`
    def _init_logger(self, level):
        # Init logger
        self.log = logging.getLogger('pyload')
        self.log.setLevel(level)

        # Set console handler
        self._set_consolelog_handler()

        # Set syslog handler
        if self.config.get('log', 'syslog') != 'no':
            self._set_syslog_handler()

        # Create logfile folder
        self._mklogdir()

        # Set file handler
        if self.config.get('log', 'logfile'):
            self._set_logfile_handler()

    def _init_permissions(self):
        if os.name == 'nt':
            return None

        change_group = self.config.get('permission', 'change_group')
        change_user = self.config.get('permission', 'change_user')

        if change_group:
            try:
                group = self.config.get('permission', 'group')
                sys.set_process_group(group)
            except Exception as e:
                self.log.error(_("Unable to change gid"), str(e))

        if change_user:
            try:
                user = self.config.get('permission', 'user')
                sys.set_process_user(user)
            except Exception as e:
                self.log.error(_("Unable to change uid"), str(e))

    def _init_translation(self):
        language = self.config.get('general', 'language')
        localedir = os.path.join(PACKDIR, 'locale')
        try:
            install_translation('core', localedir, [language])
        except (IOError, OSError):
            self.log.warning(
                _("Unable to load `{0}` language, use default").format(language))
            install_translation('core', localedir, fallback=True)

    def _init_debug(self, debug):
        debug_log = self.config.get('log', 'debug')
        verbose_log = self.config.get('log', 'verbose')
        self.debug = 2 if debug_log and verbose_log else int(
            max(debug, debug_log))

    def _start_interface(self, webui, rpc):
        if webui is None:
            webui = self._webui
        if rpc is None:
            rpc = self._rpc

        # TODO: Parse `remote`
        if rpc or self.config.get('rpc', 'activated'):
            self.log.debug("Activating RPC interface ...")
            self.rem.start()
        elif not webui:
            webui = True

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
        if webui or self.config.get('webui', 'activated'):
            from .thread.webserver import WebServer
            self.webserver = WebServer(self)
            self.webserver.start()
            # self.svm.add('webui', **kwgs)
            # self.svm.start()

    def _init_api(self):
        from .api import Api
        self.api = Api(self)

    def _init_database(self, restore):
        from .database import DatabaseBackend
        from .datatype import Permission, Role

        # TODO: Move inside DatabaseBackend
        newdb = not os.path.exists(DatabaseBackend.DB_FILE)
        self.db = DatabaseBackend(self)
        self.db.setup()

        if restore or newdb:
            self.db.add_user("admin", "pyload", Role.Admin, Permission.All)
        if restore:
            self.log.warning(
                "Restored default login credentials `admin|pyload`")

    def _init_managers(self):
        from .manager import (AccountManager, AddonManager, EventManager, 
                              ExchangeManager, FileManager, InfoManager,
                              PluginManager, RemoteManager, TransferManager)

        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.filemanager = self.files = FileManager(self)
        self.pluginmanager = self.pgm = PluginManager(self)
        self.exchangemanager = self.exm = ExchangeManager(self)
        self.eventmanager = self.evm = EventManager(self)
        self.accountmanager = self.acm = AccountManager(self)
        self.infomanager = self.iom = InfoManager(self)
        self.transfermanager = self.tsm = TransferManager(self)
        self.addonmanager = self.adm = AddonManager(self)
        self.remotemanager = self.rem = RemoteManager(self)
        # self.servermanager = self.svm = ServerManager(self)
        self.db.manager = self.files  #: ugly?

    def _init_network(self):
        from .network.factory import RequestFactory
        builtins.REQUEST = self.request = self.req = RequestFactory(self)

    def _init_pid(self):
        self._lockfd = None
        self.pid = os.getpid()
        self.pidfile = os.path.join(self.profiledir, 'pyload.session')
        try:
            with io.open(self.pidfile, mode='w') as fp:
                self._lockfd = fp.fileno()
                fp.write(self.pid)
                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            if e.errno != errno.EAGAIN:
                e = "A pyLoad instance using profile `{0}` is already running".format(
                    self.profiledir)
            raise IOError(e)

    def _init_config(self, profile, configdir):
        self.profiledir = _gen_profiledir(profile, configdir)
        self.configdir, self.profile = os.path.split(self.profiledir)

        tmproot = os.path.join(TMPDIR, os.path.basename(self.configdir))
        makedirs(tmproot)
        self.tmpdir = tempfile.mkdtemp(dir=tmproot)

        self._init_pid()

        if self.profiledir not in sys.path:
            sys.path.append(self.profiledir)

        os.chdir(self.profiledir)
        self.configfile = os.path.join(self.profiledir, 'pyload.conf')
        self.config = self.cfg = ConfigParser(self.configfile, self.version)
        make_config(self.cfg)  # TODO: Rewrite...
        
    def _register_signal(self):
        try:
            if os.name == 'nt':
                signal.signal(
                    signal.CTRL_C_EVENT,
                    lambda s,
                    f: self.shutdown())
                signal.signal(
                    signal.CTRL_BREAK_EVENT,
                    lambda s,
                    f: self.shutdown())
            else:
                signal.signal(signal.SIGTERM, lambda s, f: self.shutdown())
                signal.signal(signal.SIGINT, lambda s, f: self.shutdown())
                signal.signal(signal.SIGQUIT, lambda s, f: self.terminate())
                # signal.signal(signal.SIGTSTP, lambda s, f: self._stop())
                # signal.signal(signal.SIGCONT, lambda s, f: self._start())
        except Exception:
            pass

    def __init__(self, profile=None, configdir=None, debug=None,
                 refresh=None, webui=None, rpc=None, update=None):
        self.running = Event()

        self._cleanup = bool(refresh)
        self._restart = False
        self._shutdown = False
        self._rpc = rpc
        self._webui = webui

        if refresh:
            pyclean(PACKDIR)

        # NOTE: Do not change the init order!
        self._register_signal()
        self._init_config(profile, configdir)
        self._init_debug(debug)
        self._init_logger(logging.DEBUG if self.debug else logging.INFO)
        self._init_translation()

        self.log.debug("Initializing pyLoad ...")
        self._init_permissions()
        self._init_database(refresh > 1)
        self._init_network()
        self._init_api()
        self._init_managers()

        Process.__init__(self, target=self._start)

    def _tune_process(self):
        try:
            sys.set_process_name('pyLoad')
        except NameError:
            pass
        niceness = self.config.get('general', 'niceness')
        sys.renice(niceness)
        ioniceness = int(self.config.get('general', 'ioniceness'))
        sys.ionice(ioniceness)

    def _init_storage(self):
        storage_folder = self.config.get('general', 'storage_folder')
        if not storage_folder:
            storage_folder = os.path.join(USERDIR, 'Downloads')
        self.log.debug("Storage: {0}".format(storage_folder))
        makedirs(storage_folder)
        space_size = format.size(availspace(storage_folder))
        self.log.info(_("Available storage space: {0}").format(space_size))

    def _workloop(self):
        self.tsm.pause = False  # NOTE: Recheck...
        self.running.set()
        try:
            while True:
                self.running.wait()
                self.tsm.work()
                self.iom.work()
                self.exm.work()
                if self._restart:
                    raise Restart
                if self._shutdown:
                    raise Shutdown
                self.scheduler.run()
        except Restart:
            self.restart()
        except Shutdown:
            pass

    def _start_plugins(self):
        # TODO: Move in accountmanager
        self.log.info(_("Activating accounts ..."))
        self.acm.get_account_infos()
        # self.scheduler.enter(0, 0, self.acm.get_account_infos)
        self.adm.activate_plugins()
        self.config.save()  #: save so config files gets filled

    def _start(self, webui=None, rpc=None):
        try:
            self.log.info(_("Starting pyLoad ..."))
            self.log.info(
                _("Version: {0}").format(
                    convert.from_version(
                        self.version)))
            self.log.info(_("Profile: {0}").format(self.profiledir))
            self.log.debug("Tempdir: {0}".format(self.tmpdir))

            self._start_interface(webui, rpc)
            self._init_storage()
            self._tune_process()
            self._start_plugins()

            self.log.info(_("pyLoad is up and running"))
            self.evm.fire('pyload:started')

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

            self._workloop()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log.critical(_("Critical error"), str(e))
            self.terminate()
            raise

        self.shutdown()

    def _remove_logger(self):
        for handler in self.log.handlers:
            with closing(handler) as hdlr:
                self.log.removeHandler(hdlr)

    def update(self):
        autoupgrade.upgrade(__setup_map['name'], dependencies=True, restart=True)

    def restart(self):
        self._stop()
        self.log.info(_("Restarting pyLoad ..."))
        self.evm.fire('pyload:restarting')
        self._start()

    def _remove_pid(self):
        try:
            fcntl.flock(self._lockfd, fcntl.LOCK_UN)
        except IOError:
            pass
        remove(self.pidfile, ignore_errors=True)

    def terminate(self):
        try:
            self.log.debug("Killing pyLoad ...")
            self._remove_pid()
            self._remove_logger()
        finally:
            return Process.terminate(self)

    def shutdown(self, cleanup=None):
        if cleanup is None:
            cleanup = self._cleanup
        try:
            if self.is_alive():
                self._stop()
            self.log.info(_("Exiting pyLoad ..."))
            self.db.shutdown()
            if cleanup:
                self.log.info(_("Deleting temp files ..."))
                remove(self.tmpdir, ignore_errors=True)
        finally:
            return self.terminate(self)

    def _stop(self):
        try:
            self.log.info(_("Stopping pyLoad ..."))
            self.evm.fire('pyload:stopping')
            # TODO: quit webserver
            self.tsm.shutdown()
            self.api.stop_all_downloads()
            self.adm.deactivate_addons()
        finally:
            self.running.clear()
            self.evm.fire('pyload:stopped')
            self.files.sync_save()


def info():
    return Info(__setup_map)


def version():
    return __core_version


def status(profile=None, configdir=None):
    profiledir = _gen_profiledir(profile, configdir)
    pidfile = os.path.join(profiledir, 'pyload.session')
    try:
        with io.open(pidfile, mode='rb') as fp:
            return int(fp.read().strip())
    except (OSError, TypeError):
        return None


def setup(profile=None, configdir=None):
    from pyload.setup import SetupAssistant
    profiledir = _gen_profiledir(profile, configdir)
    configfile = os.path.join(profiledir, 'pyload.conf')
    return SetupAssistant(configfile, version()).start()


def quit(profile=None, configdir=None, wait=300):
    pid = status(profile, configdir)
    try:
        sys.kill_process(pid, wait)
    except Exception:
        pass


def start(profile=None, configdir=None, debug=0,
          refresh=0, webui=None, rpc=None, update=True, daemon=False):
    proc = Core(profile, configdir, debug, refresh, webui, rpc, update)
    proc.start()

    if daemon:
        pidfile = tempfile.mkstemp(
            suffix='.pid',
            prefix='daemon-',
            dir=proc.tmpdir)[1]
        d = daemonize.Daemonize("pyLoad", pidfile, proc.join, logger=proc.log)
        d.start()

    return proc  #: returns process instance


def restart(*args, **kwargs):
    configdir = kwargs.get('configdir', args.pop(1))
    profile = kwargs.get('profile', args.pop(0))
    quit(profile, configdir, wait=None)
    return start(*args, **kwargs)


# def test():
    # raise NotImplementedError
