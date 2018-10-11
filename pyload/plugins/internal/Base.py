# -*- coding: utf-8 -*-
import inspect
import re
import time
import urllib.parse
from builtins import _

from pyload.plugins.internal.Captcha import Captcha
from pyload.plugins.internal.Plugin import Abort, Fail, Plugin, Reconnect, Retry, Skip
from pyload.plugins.utils import (decode, encode, fixurl, format_size, format_time,
                                  parse_html_form, parse_name, replace_patterns)


# TODO: Recheck in 0.6.x
def getInfo(urls):
    #: result = [ .. (name, size, status, url) .. ]
    pass


# TODO: Remove in 0.6.x
def parse_fileInfo(klass, url="", html=""):
    info = klass.get_info(url, html)
    return encode(info['name']), info['size'], info['status'], info['url']


class Base(Plugin):
    __name__ = "Base"
    __type__ = "base"
    __version__ = "0.34"
    __status__ = "stable"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Base plugin for Hoster and Crypter"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    URL_REPLACEMENTS = []

    @classmethod
    def get_info(cls, url="", html=""):
        url = fixurl(url, unquote=True)
        info = {'name': parse_name(url),
                'hash': {},
                'pattern': {},
                'size': 0,
                'status': 7 if url else 8,
                'url': replace_patterns(url, cls.URL_REPLACEMENTS)}

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()

        except Exception:
            pass

        return info

    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        #: Engage wan reconnection
        self.wantReconnect = False  # TODO: Change to `want_reconnect` in 0.6.x

        #: Enable simultaneous processing of multiple downloads
        self.multiDL = True  # TODO: Change to `multi_dl` in 0.6.x

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

        #: Js engine, see `JsEngine`
        self.js = self.pyload.js

        #: Captcha stuff
        # TODO: Replace in 0.6.x:
        #_Captcha = self.pyload.pluginManager.loadClass("captcha", self.classname) or Captcha
        # self.captcha = _Captcha(pyfile)
        self.captcha = Captcha(pyfile)

        #: Some plugins store html code here
        self.data = ""

        #: Dict of the amount of retries already made
        self.retries = {}

        self.init_base()
        self.init()

    def _log(self, level, plugintype, pluginname, messages):
        log = getattr(self.pyload.log, level)
        msg = " | ".join(decode(a).strip() for a in messages if a)

        #: Hide any user/password
        try:
            msg = msg.replace(
                self.account.user, self.account.user[:3] + "*******")
        except Exception:
            pass

        try:
            msg = msg.replace(
                self.account.info['login']['password'], "**********")
        except Exception:
            pass

        log("{plugintype} {pluginname}[{id}]: {msg}".format(**{'plugintype': plugintype.upper(),
             'pluginname': pluginname,
             'id': self.pyfile.id,
             'msg': msg}))

    def init_base(self):
        pass

    def setup_base(self):
        pass

    def setup(self):
        """
        Setup for enviroment and other things, called before downloading (possibly more than one time)
        """
        pass

    def _setup(self):
        # TODO: Remove in 0.6.x
        self.pyfile.error = ""
        self.data = ""
        self.last_html = ""
        self.last_header = {}

        if self.config.get('use_premium', True):
            self.load_account()  # TODO: Move to PluginThread in 0.6.x
        else:
            self.account = False
            self.user = None  # TODO: Remove in 0.6.x

        try:
            self.req.close()
        except Exception:
            pass

        if self.account:
            self.req = self.pyload.requestFactory.getRequest(
                self.classname, self.account.user)
            # NOTE: Avoid one unnecessary get_info call by `self.account.premium` here
            self.premium = self.account.info['data']['premium']
        else:
            self.req = self.pyload.requestFactory.getRequest(self.classname)
            self.premium = False

        self.req.setOption("timeout", 60)  # TODO: Remove in 0.6.x

        self.setup_base()
        self.grab_info()
        self.setup()
        self.check_status()

    def load_account(self):
        if not self.account:
            self.account = self.pyload.accountManager.getAccountPlugin(
                self.classname)

        if not self.account:
            self.account = False
            self.user = None  # TODO: Remove in 0.6.x

        else:
            self.account.choose()
            self.user = self.account.user  # TODO: Remove in 0.6.x
            if self.account.user is None:
                self.account = False

    def _update_name(self):
        name = decode(self.info.get('name'))

        if name and name != decode(self.info.get('url')):
            self.pyfile.name = name
        else:
            name = decode(self.pyfile.name)

        self.log_info(_("Link name: {}").format(name))

    def _update_size(self):
        size = self.info.get('size')

        if size > 0:
            # TODO: Fix int conversion in 0.6.x
            self.pyfile.size = int(self.info.get('size'))
        else:
            size = self.pyfile.size

        if size:
            self.log_info(
                _("Link size: {} ({} bytes)").format(format_size(size), size))
        else:
            self.log_info(_("Link size: N/D"))

    def _update_status(self):
        self.pyfile.status = self.info.get('status', 14)
        self.pyfile.sync()

        self.log_info(_("Link status: ") + self.pyfile.getStatusName())

    def sync_info(self):
        self._update_name()
        self._update_size()
        self._update_status()

    def grab_info(self):
        self.log_info(_("Grabbing link info..."))

        old_info = dict(self.info)
        new_info = self.get_info(self.pyfile.url, self.data)

        self.info.update(new_info)

        self.log_debug("Link info: {}".format(self.info))
        self.log_debug("Previous link info: {}".format(old_info))

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
            self.abort(_("Plugin is temporarily unavailable"))

        elif self.__status__ == "testing":
            self.log_warning(_("Plugin may be unstable"))

    def _process(self, thread):
        """
        Handles important things to do before starting
        """
        self.thread = thread

        self._initialize()
        self._setup()

        # TODO: Enable in 0.6.x
        # self.pyload.hookManager.downloadPreparing(self.pyfile)
        # self.check_status()

        # TODO: Remove in 0.6.x
        if self.__type__ == "crypter":
            self.pyload.hookManager.downloadPreparing(self.pyfile)
            self.check_status()

        self.pyfile.setStatus("starting")

        self.log_info(_("Processing url: ") + self.pyfile.url)
        self.process(self.pyfile)
        self.check_status()

    #: Deprecated method, use `_process` instead (Remove in 0.6.x)
    def preprocessing(self, *args, **kwargs):
        # NOTE: Set pyfile status from `queued` to `starting` as soon as possible to avoid race condition in ThreadManager's assignJob function
        # NOTE: Move to ThreadManager in 0.6.x
        self.pyfile.setStatus("starting")

        # NOTE: Recheck info thread synchronization in 0.6.x
        return self._process(*args, **kwargs)

    def process(self, pyfile):
        """
        The "main" method of every hoster plugin, you **have to** overwrite it
        """
        raise NotImplementedError

    def set_reconnect(self, reconnect):
        if self.pyload.config.get('reconnect', 'activated'):
            reconnect = reconnect and self.pyload.api.isTimeReconnect()
            self.log_debug(
                "RECONNECT{} required".format(
                    "" if reconnect else " not"),
                    "Previous wantReconnect: {}".format(
                        self.wantReconnect))
            self.wantReconnect = bool(reconnect)

    def set_wait(self, seconds, strict=False):
        """
        Set a specific wait time later used with `wait`

        :param seconds: wait time in seconds
        :param reconnect: True if a reconnect would avoid wait time
        """
        wait_time = float(seconds)

        if wait_time < 0:
            return False

        old_wait_until = self.pyfile.waitUntil
        new_wait_until = time.time() + wait_time + float(not strict)

        self.log_debug("WAIT set to timestamp {}".format(new_wait_until),
                       "Previous waitUntil: {}".format(old_wait_until))

        self.pyfile.waitUntil = new_wait_until
        return True

    def wait(self, seconds=None, reconnect=None):
        """
        Waits the time previously set
        """
        if seconds is not None:
            self.set_wait(seconds)

        if reconnect is None:
            reconnect = (seconds > self.config.get('max_wait', 10) * 60)

        self.set_reconnect(reconnect)

        wait_time = self.pyfile.waitUntil - time.time()

        if wait_time < 1:
            self.log_warning(_("Invalid wait time interval"))
            return

        self.waiting = True

        status = self.pyfile.status  # NOTE: Recheck in 0.6.x
        self.pyfile.setStatus("waiting")

        self.log_info(_("Waiting {}...").format(format_time(wait_time)))

        if self.wantReconnect:
            self.log_info(_("Requiring reconnection..."))
            if self.account:
                self.log_warning(_("Reconnection ignored due logged account"))

        if not self.wantReconnect or self.account:
            while self.pyfile.waitUntil > time.time():
                self.check_status()
                time.sleep(2)

        else:
            while self.pyfile.waitUntil > time.time():
                self.check_status()
                self.thread.m.reconnecting.wait(1)

                if self.thread.m.reconnecting.isSet():
                    self.waiting = False
                    self.wantReconnect = False

                    self.req.clearCookies()
                    raise Reconnect

                time.sleep(2)

        self.waiting = False
        self.pyfile.status = status  # NOTE: Recheck in 0.6.x

    def skip(self, msg=""):
        """
        Skip and give msg
        """
        raise Skip(encode(msg or self.pyfile.error or self.pyfile.pluginname)
                   )  # TODO: Remove `encode` in 0.6.x

    # TODO: Remove in 0.6.x
    def fail(self, msg=""):
        """
        Fail and give msg
        """
        msg = msg.strip()

        if msg:
            self.pyfile.error = msg
        else:
            msg = self.pyfile.error or self.info.get(
                'error') or self.pyfile.getStatusName()

        raise Fail(encode(msg))  # TODO: Remove `encode` in 0.6.x

    def error(self, msg="", type=_("Parse")):
        type = _("{} error").format(type.strip(
        ).capitalize() if type else _("Unknown"))
        msg = _("{type}: {msg} | Plugin may be out of date").format(
            **{'type': type, 'msg': msg or self.pyfile.error})

        self.fail(msg)

    def abort(self, msg=""):
        """
        Abort and give msg
        """
        if msg:  # TODO: Remove in 0.6.x
            self.pyfile.error = encode(msg)

        raise Abort

    # TODO: Recheck in 0.6.x
    def offline(self, msg=""):
        """
        Fail and indicate file is offline
        """
        self.fail("offline")

    # TODO: Recheck in 0.6.x
    def temp_offline(self, msg=""):
        """
        Fail and indicates file ist temporary offline, the core may take consequences
        """
        self.fail("temp. offline")

    def restart(self, msg="", premium=True):
        if not msg:
            msg = _("Restart plugin") if premium else _(
                "Fallback to free processing")

        if not premium:
            if self.premium:
                self.restart_free = True
            else:
                self.fail("{} | {}".format(msg, _("Url was already processed as free")))

        self.req.clearCookies()

        raise Retry(encode(msg))  # TODO: Remove `encode` in 0.6.x

    def retry(self, attemps=5, wait=1, msg="", msgfail=_("Max retries reached")):
        """
        Retries and begin again from the beginning

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

        raise Retry(encode(msg))  # TODO: Remove `encode` in 0.6.x

    def retry_captcha(self, attemps=10, wait=1, msg="",
                      msgfail=_("Max captcha retries reached")):
        self.captcha.invalid(msg)
        self.retry(attemps, wait, msg=_("Retry Captcha"), msgfail=msgfail)

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
        return Plugin.load(self, *args, **kwargs)

    def parse_html_form(self, attr_str="", input_names={}):
        return parse_html_form(attr_str, self.data, input_names)

    def get_password(self):
        """
        Get the password the user provided in the package
        """
        return self.pyfile.package().password or ""

    def clean(self):
        """
        Clean everything and remove references
        """
        Plugin.clean(self)
        for attr in ("account", "html", "pyfile", "thread"):
            if hasattr(self, attr):
                setattr(self, attr, None)
