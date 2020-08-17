# -*- coding: utf-8 -*-
import inspect
import re
import time
import urllib.parse

from pyload.core.network.exceptions import Abort, Fail, Reconnect, Retry, Skip
from pyload.core.utils import format, parse
from pyload.core.utils.old import decode, fixurl

from ..helpers import parse_html_form, replace_patterns
from .captcha import BaseCaptcha
from .plugin import BasePlugin


# TODO: Recheck in 0.6.x
def get_info(urls):
    #: result = [ .. (name, size, status, url) .. ]
    pass


# TODO: Remove in 0.6.x
def parse_file_info(klass, url="", html=""):
    info = klass.get_info(url, html)
    return info["name"], info["size"], info["status"], info["url"]


class BaseHoster(BasePlugin):
    __name__ = "BaseHoster"
    __type__ = "base"
    __version__ = "0.34"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
    ]

    __description__ = """Base hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = []

    @classmethod
    def get_info(cls, url="", html=""):
        url = fixurl(url, unquote=True)
        info = {
            "name": parse.name(url),
            "hash": {},
            "pattern": {},
            "size": 0,
            "status": 7 if url else 8,
            "url": replace_patterns(url, cls.URL_REPLACEMENTS),
        }

        try:
            info["pattern"] = re.match(cls.__pattern__, url).groupdict()

        except Exception:
            pass

        return info

    def __init__(self, pyfile):
        self._init(pyfile.m.pyload)

        #: Engage wan reconnection
        self.want_reconnect = False  # TODO: Change to `want_reconnect` in 0.6.x

        #: Enable simultaneous processing of multiple downloads
        self.multi_dl = True  # TODO: Change to `multi_dl` in 0.6.x

        #: time.time() + wait in seconds
        self.waiting = False

        #: Account handler instance, see :py:class:`Account`
        self.account = None
        self.user = None  # TODO: Remove in 0.6.x
        self.premium = None

        #: Associated pyfile instance, see `PyFile`
        self.pyfile = pyfile

        #: Holds thread in future
        self.thread = None

        #: Captcha stuff
        # TODO: Replace in 0.6.x:
        # _Captcha = self.pyload.plugin_manager.load_class("anticaptcha", self.classname) or BaseCaptcha
        # self.captcha = _Captcha(pyfile)
        self.captcha = BaseCaptcha(pyfile)

        #: Some plugins store html code here
        self.data = ""

        #: Dict of the amount of retries already made
        self.retries = {}

        self.init_base()
        self.init()

    def _log(self, level, plugintype, pluginname, args, kwargs):
        log = getattr(self.pyload.log, level)

        #: Hide any user/password
        try:
            user = self.account.user
            pw = self.account.info["login"]["password"]
        except AttributeError:
            pass
        else:
            hidden_user = "{:*<{}}".format(self.account.user[:3], 7)
            hidden_pw = "*" * 10
            args = (
                a.replace(user, hidden_user).replace(pw, hidden_pw) for a in args if a
            )

        log(
            "{plugintype} {pluginname}[{id}]: {msg}".format(
                plugintype=plugintype.upper(),
                pluginname=pluginname,
                id=self.pyfile.id,
                msg="%s" * len(args),
            ),
            *args,
            **kwargs,
        )

    def init_base(self):
        pass

    def setup_base(self):
        pass

    def setup(self):
        """
        Setup for enviroment and other things, called before downloading (possibly more
        than one time)
        """
        pass

    def _setup(self):
        # TODO: Remove in 0.6.x
        self.pyfile.error = ""
        self.data = ""
        self.last_html = ""
        self.last_header = {}

        if self.config.get("use_premium", True):
            self.load_account()  # TODO: Move to PluginThread in 0.6.x
        else:
            self.account = False
            self.user = None  # TODO: Remove in 0.6.x

        try:
            self.req.close()
        except Exception:
            pass

        if self.account:
            self.req = self.pyload.request_factory.get_request(
                self.classname, self.account.user
            )
            # NOTE: Avoid one unnecessary get_info call by `self.account.premium` here
            self.premium = self.account.info["data"]["premium"]
        else:
            self.req = self.pyload.request_factory.get_request(self.classname)
            self.premium = False

        self.req.set_option("timeout", 60)  # TODO: Remove in 0.6.x

        self.setup_base()
        self.grab_info()
        self.setup()
        self.check_status()

    def load_account(self):
        if not self.account:
            self.account = self.pyload.account_manager.get_account_plugin(
                self.classname
            )

        if not self.account:
            self.account = False
            self.user = None  # TODO: Remove in 0.6.x

        else:
            self.account.choose()
            self.user = self.account.user  # TODO: Remove in 0.6.x
            if self.account.user is None:
                self.account = False

    def _update_name(self):
        name = decode(self.info.get("name"))

        if name and name != decode(self.info.get("url")):
            self.pyfile.name = name
        else:
            name = decode(self.pyfile.name)

        self.log_info(self._("Link name: {}").format(name))

    def _update_size(self):
        size = self.info.get("size")

        if size > 0:
            # TODO: Fix int conversion in 0.6.x
            self.pyfile.size = int(self.info.get("size"))
        else:
            size = self.pyfile.size

        if size:
            self.log_info(
                self._("Link size: {} ({} bytes)").format(format.size(size), size)
            )
        else:
            self.log_info(self._("Link size: N/D"))

    def _update_status(self):
        self.pyfile.status = self.info.get("status", 14)
        self.pyfile.sync()

        self.log_info(self._("Link status: ") + self.pyfile.get_status_name())

    def sync_info(self):
        self._update_name()
        self._update_size()
        self._update_status()

    def grab_info(self):
        self.log_info(self._("Grabbing link info..."))

        old_info = dict(self.info)
        new_info = self.get_info(self.pyfile.url, self.data)

        self.info.update(new_info)

        self.log_debug(f"Link info: {self.info}")
        self.log_debug(f"Previous link info: {old_info}")

        self.sync_info()

    def check_status(self):
        status = self.pyfile.status

        if status == 1:
            self.offline()

        elif status == 4:
            self.skip(self.pyfile.statusname)

        elif status == 6:
            self.temp_offline()

        elif status == 8:
            self.fail()

        elif status == 9 or self.pyfile.abort:
            self.abort()

    def _initialize(self):
        self.log_debug("Plugin version: " + self.__version__)
        self.log_debug("Plugin status: " + self.__status__)

        if self.__status__ == "broken":
            self.abort(self._("Plugin is temporarily unavailable"))

        elif self.__status__ == "testing":
            self.log_warning(self._("Plugin may be unstable"))

    def _process(self, thread):
        """
        Handles important things to do before starting.
        """
        self.thread = thread

        self._initialize()
        self._setup()

        # TODO: Enable in 0.6.x
        # self.pyload.addon_manager.download_preparing(self.pyfile)
        # self.check_status()

        # TODO: Remove in 0.6.x
        if self.__type__ == "decrypter":
            self.pyload.addon_manager.download_preparing(self.pyfile)
            self.check_status()

        self.pyfile.set_status("starting")

        self.log_info(self._("Processing url: ") + self.pyfile.url)
        self.process(self.pyfile)
        self.check_status()

    #: Deprecated method, use `_process` instead (Remove in 0.6.x)
    def preprocessing(self, *args, **kwargs):
        # NOTE: Set pyfile status from `queued` to `starting` as soon as possible to avoid race condition in ThreadManager's assign_job function
        # NOTE: Move to ThreadManager in 0.6.x
        self.pyfile.set_status("starting")

        # NOTE: Recheck info thread synchronization in 0.6.x
        return self._process(*args, **kwargs)

    def process(self, pyfile):
        """
        The "main" method of every downloader plugin, you **have to** overwrite it.
        """
        raise NotImplementedError

    def set_reconnect(self, reconnect):
        if self.pyload.config.get("reconnect", "enabled"):
            reconnect = reconnect and self.pyload.api.is_time_reconnect()
            self.log_debug(
                "RECONNECT{} required".format("" if reconnect else " not"),
                "Previous want_reconnect: {}".format(self.want_reconnect),
            )
            self.want_reconnect = bool(reconnect)

    def set_wait(self, seconds, strict=False):
        """
        Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        wait_time = float(seconds)

        if wait_time < 0:
            return False

        old_wait_until = self.pyfile.wait_until
        new_wait_until = time.time() + wait_time + float(not strict)

        self.log_debug(
            "WAIT set to timestamp {}".format(new_wait_until),
            "Previous wait_until: {}".format(old_wait_until),
        )

        self.pyfile.wait_until = new_wait_until
        return True

    def wait(self, seconds=None, reconnect=None):
        """
        Waits the time previously set.
        """
        if seconds is not None:
            self.set_wait(seconds)

        if reconnect is None:
            reconnect = seconds > self.config.get("max_wait", 10) * 60

        self.set_reconnect(reconnect)

        wait_time = self.pyfile.wait_until - time.time()

        if wait_time < 1:
            self.log_warning(self._("Invalid wait time interval"))
            return

        self.waiting = True

        status = self.pyfile.status  # NOTE: Recheck in 0.6.x
        self.pyfile.set_status("waiting")

        self.log_info(self._("Waiting {}...").format(format.time(wait_time)))

        if self.want_reconnect:
            self.log_info(self._("Requiring reconnection..."))
            if self.account:
                self.log_warning(self._("Reconnection ignored due logged account"))

        if not self.want_reconnect or self.account:
            while self.pyfile.wait_until > time.time():
                self.check_status()
                time.sleep(2)

        else:
            while self.pyfile.wait_until > time.time():
                self.check_status()
                self.thread.m.reconnecting.wait(1)

                if self.thread.m.reconnecting.is_set():
                    self.waiting = False
                    self.want_reconnect = False

                    self.req.clear_cookies()
                    raise Reconnect

                time.sleep(2)

        self.waiting = False
        self.pyfile.status = status  # NOTE: Recheck in 0.6.x

    def skip(self, msg=""):
        """
        Skip and give msg.
        """
        raise Skip(msg or self.pyfile.error or self.pyfile.pluginname)

    # TODO: Remove in 0.6.x
    def fail(self, msg=""):
        """
        Fail and give msg.
        """
        msg = msg.strip()

        if msg:
            self.pyfile.error = msg
        else:
            msg = (
                self.pyfile.error
                or self.info.get("error")
                or self.pyfile.get_status_name()
            )

        raise Fail(msg)

    def error(self, msg="", type="Parse"):
        type = self._("{} error").format(
            type.strip().capitalize() if type else self._("Unknown")
        )
        msg = self._("{type}: {msg} | Plugin may be out of date").format(
            type=type, msg=msg or self.pyfile.error
        )

        self.fail(msg)

    def abort(self, msg=""):
        """
        Abort and give msg.
        """
        if msg:  # TODO: Remove in 0.6.x
            self.pyfile.error = msg

        raise Abort

    # TODO: Recheck in 0.6.x
    def offline(self, msg=""):
        """
        Fail and indicate file is offline.
        """
        self.fail("offline")

    # TODO: Recheck in 0.6.x
    def temp_offline(self, msg=""):
        """
        Fail and indicates file ist temporary offline, the core may take consequences.
        """
        self.fail("temp. offline")

    def restart(self, msg="", premium=True):
        if not msg:
            msg = (
                self._("Restart plugin")
                if premium
                else self._("Fallback to free processing")
            )

        if not premium:
            if self.premium:
                self.restart_free = True
            else:
                self.fail(
                    "{} | {}".format(msg, self._("Url was already processed as free"))
                )

        self.req.clear_cookies()

        raise Retry(msg)

    def retry(self, attemps=5, wait=1, msg="", msgfail="Max retries reached"):
        """
        Retries and begin again from the beginning.

        :param attemps: number of maximum retries
        :param wait: time to wait in seconds before retry
        :param msg: message passed to fail if attemps value was reached
        """
        frame = inspect.currentframe()

        try:
            id = frame.f_back.f_lineno
        finally:
            del frame  #: Delete the frame or it wont be cleaned

        if id not in self.retries:
            self.retries[id] = 0

        if 0 < attemps <= self.retries[id]:
            self.fail(msgfail)

        self.retries[id] += 1

        self.wait(wait)

        raise Retry(msg)

    def retry_captcha(
        self, attemps=10, wait=1, msg="", msgfail="Max captcha retries reached"
    ):
        self.captcha.invalid(msg)
        self.retry(attemps, wait, msg=self._("Retry Captcha"), msgfail=msgfail)

    def fixurl(self, url, baseurl=None, unquote=True):
        url = fixurl(url, unquote=True)
        baseurl = fixurl(baseurl or self.pyfile.url, unquote=True)

        if not urllib.parse.urlparse(url).scheme:
            url_p = urllib.parse.urlparse(baseurl)
            baseurl = "{}://{}".format(url_p.scheme, url_p.netloc)
            url = urllib.parse.urljoin(baseurl, url)

        return fixurl(url, unquote)

    def load(self, *args, **kwargs):
        self.check_status()
        return super().load(*args, **kwargs)

    def parse_html_form(self, attr_str="", input_names={}):
        return parse_html_form(attr_str, self.data, input_names)

    def get_password(self):
        """
        Get the password the user provided in the package.
        """
        return self.pyfile.package().password or ""

    def clean(self):
        """
        Clean everything and remove references.
        """
        super().clean()
        for attr in ("account", "html", "pyfile", "thread"):
            if hasattr(self, attr):
                setattr(self, attr, None)
