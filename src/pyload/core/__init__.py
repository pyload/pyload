# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/

import atexit
import gettext
import locale
import os
import signal
import subprocess
import sys
import tempfile
import time
from threading import Event

from pyload import APPID, PKGDIR, USERHOMEDIR

from .. import __version__ as PYLOAD_VERSION
from .. import __version_info__ as PYLOAD_VERSION_INFO
from .utils import format, fs
from .utils.misc import reversemap


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

    #: addons can check this property when deactivated to tell the reason for deactivation (unload or exit)
    @property
    def exiting(self):
        return self._exiting

    @property
    def debug(self):
        return self._debug

    # NOTE: should `reset` restore the user config as well?
    def __init__(self, userdir, tempdir, storagedir, debug=None, reset=False, dry=False):
        self._running = Event()
        self._exiting = False
        self._do_restart = False
        self._do_exit = False
        self._ = lambda x: x
        self._debug = 0
        self._dry_run = dry

        # if self.tmpdir not in sys.path:
        # sys.path.append(self.tmpdir)

        # if refresh:
        # cleanpy(PACKDIR)

        datadir = os.path.join(os.path.realpath(userdir), "data")
        os.makedirs(datadir, exist_ok=True)
        os.chdir(datadir)

        self._init_config(userdir, tempdir, storagedir, debug)
        self._init_log()
        if storagedir is not None:
            self.log.warning("Download folder was specified from the commandline")
        self._init_database(reset and not dry)
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

        # If no argument set, read storage dir from config file,
        # otherwise save setting to config dir
        if storagedir is None:
            storagedir = self.config.get("general", "storage_folder")

        else:
            self.config.set("general", "storage_folder", storagedir)

        # Make sure storage_folder is not empty
        # and also not inside dangerous locations
        correct_case = lambda x: x.lower() if os.name == "nt" else x
        directories = [
            correct_case(os.path.join(os.path.realpath(d), "") )
            for d in [storagedir or PKGDIR, PKGDIR, userdir]
        ]
        is_bad_dir = any(directories[0].startswith(d) for d in directories[1:])

        if not storagedir or is_bad_dir:
            self.config.set("general", "storage_folder", "~/Downloads/pyLoad")
            storagedir = self.config.get("general", "storage_folder")

        os.makedirs(storagedir, exist_ok=True)

        if not self._dry_run:
            self.config.save()  #: save so config files gets filled

    def _init_log(self):
        from .log_factory import LogFactory

        self.logfactory = LogFactory(self)
        self.log = self.logfactory.get_logger(
            "pyload"
        )  # NOTE: forced debug mode from console is not working actually

        self.log.info(f"*** Welcome to pyLoad {self.version} ***")
        if self._dry_run:
            self.log.info("*** TEST RUN ***")

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

    def _init_database(self, reset):
        from .threads.database_thread import DatabaseThread

        db_path = os.path.join(self.userdir, "data", DatabaseThread.DB_FILENAME)
        newdb = not os.path.isfile(db_path)

        self.db = DatabaseThread(self)
        self.db.setup()

        userpw = (self.DEFAULT_USERNAME, self.DEFAULT_PASSWORD)
        # nousers = bool(self.db.list_users())
        if reset or newdb:
            self.db.add_user(*userpw, reset=True)

        if reset:
            self.log.info(
                self._(
                    "Successfully reset default login credentials `{}|{}`"
                ).format(*userpw)
            )

    def _init_managers(self):
        from .managers.account_manager import AccountManager
        from .managers.addon_manager import AddonManager
        from .managers.captcha_manager import CaptchaManager
        from .managers.event_manager import EventManager
        from .managers.file_manager import FileManager
        from .managers.plugin_manager import PluginManager
        from .managers.thread_manager import ThreadManager
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
                from grp import getgrnam

                group = getgrnam(self.config.get("permission", "group"))
                os.setgid(group[2])
            except Exception:
                self.log.warning(
                    self._("Unable to change gid"),
                    exc_info=self.debug > 1,
                    stack_info=self.debug > 2,
                )

        if change_user:
            try:
                from pwd import getpwnam

                user = getpwnam(self.config.get("permission", "user"))
                os.setuid(user[2])
            except Exception:
                self.log.warning(
                    self._("Unable to change uid"),
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
            if lang != "en":
                self.log.warning(exc, exc_info=self.debug > 1, stack_info=self.debug > 2)
            self._set_language(self.LOCALE_DOMAIN, fallback=True)

    # def _setup_niceness(self):
    # niceness = self.config.get('general', 'niceness')
    # renice(niceness=niceness)
    # ioniceness = int(self.config.get('general', 'ioniceness'))
    # ionice(niceness=ioniceness)

    def _setup_network(self):
        self.log.debug("Setup network...")

        # TODO: Move to AccountManager
        self.log.info(self._("Activating accounts..."))
        self.acm.get_account_infos()
        # self.scheduler.add_job(0, self.acm.get_account_infos)

        self.log.info(self._("Activating plugins..."))
        self.adm.core_ready()

    def _start_webserver(self):
        if not self.config.get("webui", "enabled"):
            return
        self.webserver.start()

    def _stop_webserver(self):
        if not self.config.get("webui", "enabled"):
            return
        self.webserver.stop()

    def _get_args_for_reloading(self):
        """Determine how the script was executed, and return the args needed
        to execute it again in a new process.
        """
        rv = [sys.executable]
        py_script = sys.argv[0]
        args = sys.argv[1:]
        # Need to look at main module to determine how it was executed.
        __main__ = sys.modules["__main__"]

        # The value of __package__ indicates how Python was called. It may
        # not exist if a setuptools script is installed as an egg. It may be
        # set incorrectly for entry points created with pip on Windows.
        if getattr(__main__, "__package__", None) is None or (
            os.name == "nt"
            and __main__.__package__ == ""
            and not os.path.exists(py_script)
            and os.path.exists(f"{py_script}.exe")
        ):
            # Executed a file, like "python app.py".
            py_script = os.path.abspath(py_script)

            if os.name == "nt":
                # Windows entry points have ".exe" extension and should be
                # called directly.
                if not os.path.exists(py_script) and os.path.exists(f"{py_script}.exe"):
                    py_script += ".exe"

                if (
                    os.path.splitext(sys.executable)[1] == ".exe"
                    and os.path.splitext(py_script)[1] == ".exe"
                ):
                    rv.pop(0)

            rv.append(py_script)
        else:
            # Executed a module, like "python -m module".
            if sys.argv[0] == "-m":
                args = sys.argv
            else:
                if os.path.isfile(py_script):
                    # Rewritten by Python from "-m script" to "/path/to/script.py".
                    py_module = __main__.__package__
                    name = os.path.splitext(os.path.basename(py_script))[0]

                    if name != "__main__":
                        py_module += f".{name}"
                else:
                    # Incorrectly rewritten by pydevd debugger from "-m script" to "script".
                    py_module = py_script

                rv.extend(("-m", py_module.lstrip(".")))

        rv.extend(args)
        return rv

    def start(self):
        try:
            try:
                signal.signal(signal.SIGQUIT, self.sigquit)
                signal.signal(signal.SIGTERM, self.sigterm)
            except Exception:
                pass

            self.log.debug("Starting core...")

            if self.debug:
                debug_level = reversemap(self.DEBUG_LEVEL_MAP)[self.debug].upper()
                self.log.debug(f"Debug level: {debug_level}")

            # self.evm.fire('pyload:starting')
            self._running.set()

            self._setup_language()
            self._setup_permissions()

            self.log.info(self._("User directory: {}").format(self.userdir))
            self.log.info(self._("Cache directory: {}").format(self.tempdir))

            storage_folder = self.config.get("general", "storage_folder")
            self.log.info(self._("Storage directory: {}").format(storage_folder))

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

            self.log.debug("*** pyLoad is up and running ***")
            # self.evm.fire('pyload:started')

            self.thm.pause = False  # NOTE: Recheck...

            if self._dry_run:
                raise Exit

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
            if os.name == "nt":
                sys.exit(70)
            else:
                sys.exit(os.EX_SOFTWARE)  #: this kind of stuff should not be here!

    def is_client_connected(self):
        return (self.last_client_connected + 30) > time.time()

    def restart(self):
        self.log.info(self._("pyLoad is restarting..."))
        # self.evm.fire('pyload:restarting')
        self.terminate()

        if sys.path[0]:
            os.chdir(sys.path[0])

        args = self._get_args_for_reloading()
        subprocess.Popen(args, close_fds=True)

        sys.exit()

    def sigquit(self, a, b):
        self.log.info(self._("Received Quit signal"))
        self.terminate()
        sys.exit()

    def sigterm(self, a, b):
        self.log.info(self._("Received Terminate signal"))
        self.terminate()
        sys.exit()

    def terminate(self):
        if self.running:
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

            for pyfile in list(self.files.cache.values()):
                pyfile.abort_download()

            self._exiting = True
            self.addon_manager.core_exiting()

        finally:
            self.files.sync_save()
            self._running.clear()
            # self.evm.fire('pyload:stopped')
