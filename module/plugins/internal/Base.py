# -*- coding: utf-8 -*-

import inspect
import os
import re
import time
import urlparse

from module.plugins.internal.Captcha import Captcha
from module.plugins.internal.Plugin import Plugin, Abort, Fail, Reconnect, Retry, Skip
from module.plugins.internal.utils import (decode, encode, fixurl, format_size, format_time,
                                           parse_html_form, parse_name, replace_patterns)


#@TODO: Remove in 0.4.10
def getInfo(urls):
    #: result = [ .. (name, size, status, url) .. ]
    pass


#@TODO: Remove in 0.4.10
def parse_fileInfo(klass, url="", html=""):
    info = klass.get_info(url, html)
    return encode(info['name']), info['size'], info['status'], info['url']


#@TODO: Remove in 0.4.10
def create_getInfo(klass):
    def get_info(urls):
        for url in urls:
            yield parse_fileInfo(klass, url)

    return get_info


class Base(Plugin):
    __name__    = "Base"
    __type__    = "base"
    __version__ = "0.20"
    __status__  = "stable"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"  , "bool", "Activated"                       , True),
                   ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Base plugin for Hoster and Crypter"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = []


    @classmethod
    def get_info(cls, url="", html=""):
        url  = fixurl(url, unquote=True)
        info = {'name'   : parse_name(url),
                'pattern': {},
                'size'   : 0,
                'status' : 3 if url else 8,
                'url'    : replace_patterns(url, cls.URL_REPLACEMENTS)}

        try:
            info['pattern'] = re.match(cls.__pattern__, url).groupdict()

        except Exception:
            pass

        return info


    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        #:
        self.premium = None

        #: Engage wan reconnection
        self.wantReconnect = False  #@TODO: Change to `want_reconnect` in 0.4.10

        #: Enable simultaneous processing of multiple downloads
        self.multiDL = True  #@TODO: Change to `multi_dl` in 0.4.10

        #: time.time() + wait in seconds
        self.waiting    = False

        #: Account handler instance, see :py:class:`Account`
        self.account = None
        self.user    = None  #@TODO: Remove in 0.4.10

        #: Associated pyfile instance, see `PyFile`
        self.pyfile = pyfile

        self.thread = None  #: Holds thread in future

        #: Js engine, see `JsEngine`
        self.js = self.pyload.js

        #: Captcha stuff
        self.captcha = Captcha(self)

        #: Some plugins store html code here
        self.data = ""

        #: Dict of the amount of retries already made
        self.retries = {}

        self.init_base()
        self.init()


    def _log(self, level, plugintype, pluginname, messages):
        log = getattr(self.pyload.log, level)
        msg = u" | ".join(decode(a).strip() for a in messages if a)
        log("%(plugintype)s %(pluginname)s[%(id)s]: %(msg)s" %
            {'plugintype': plugintype.upper(),
             'pluginname': pluginname,
             'id'        : self.pyfile.id,
             'msg'       : msg})


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
        #@TODO: Remove in 0.4.10
        self.data         = ""
        self.pyfile.error = ""
        self.last_html    = None

        if self.get_config('use_premium', True):
            self.load_account()  #@TODO: Move to PluginThread in 0.4.10
        else:
            self.account = False
            self.user    = None  #@TODO: Remove in 0.4.10

        try:
            self.req.close()
        except Exception:
            pass

        if self.account:
            self.req     = self.pyload.requestFactory.getRequest(self.classname, self.account.user)
            self.premium = self.account.info['data']['premium']  #@NOTE: Avoid one unnecessary get_info call by `self.account.premium` here
        else:
            self.req     = self.pyload.requestFactory.getRequest(self.classname)
            self.premium = False

        self.setup_base()
        self.grab_info()
        self.setup()


    def load_account(self):
        if not self.account:
            self.account = self.pyload.accountManager.getAccountPlugin(self.classname)

        if not self.account:
            self.account = False
            self.user    = None  #@TODO: Remove in 0.4.10

        else:
            self.account.choose()
            self.user = self.account.user  #@TODO: Remove in 0.4.10
            if self.account.user is None:
                self.account = False


    def _update_name(self):
        name = self.info.get('name')

        if name and name is not self.info.get('url'):
            self.pyfile.name = name
        else:
            name = self.pyfile.name

        self.log_info(_("Link name: ") + name)


    def _update_size(self):
        size = self.info.get('size')

        if size > 0:
            self.pyfile.size = int(self.info['size'])  #@TODO: Fix int conversion in 0.4.10
        else:
            size = self.pyfile.size

        if size:
            self.log_info(_("Link size: %s (%s bytes)") % (format_size(size), size))
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

        self.log_debug("Link info: %s" % self.info)
        self.log_debug("Previous link info: %s" % old_info)

        self.sync_info()


    def check_status(self):
        status = self.pyfile.status

        if status is 1:
            self.offline()

        elif status is 4:
            self.skip(self.pyfile.statusname)

        elif status is 6:
            self.temp_offline()

        elif status is 8:
            self.fail()

        elif status is 9 or self.pyfile.abort:
            self.abort()


    def _process(self, thread):
        """
        Handles important things to do before starting
        """
        self.log_debug("Plugin version: " + self.__version__)
        self.log_debug("Plugin status: " + self.__status__)

        if self.__status__ is "broken":
            self.fail(_("Plugin is temporarily unavailable"))

        elif self.__status__ is "testing":
            self.log_warning(_("Plugin may be unstable"))

        self.thread = thread
        self._setup()

        # self.pyload.hookManager.downloadPreparing(self.pyfile)  #@TODO: Recheck in 0.4.10
        self.check_status()

        self.pyfile.setStatus("starting")

        self.log_info(_("Processing url: ") + self.pyfile.url)
        self.process(self.pyfile)
        self.check_status()


    #: Deprecated method, use `_process` instead (Remove in 0.4.10)
    def preprocessing(self, *args, **kwargs):
        return self._process(*args, **kwargs)


    def follow_redirects_and_get_header(self, redirect=10, update_pyfile=True):
        maxredirs = 1

        if type(redirect) is int:
            maxredirs = max(redirect, 1)

        elif redirect:
            maxredirs = self.get_config("maxredirs", default=maxredirs, plugin="UserAgentSwitcher")

        url = self.pyfile.url
        for i in xrange(maxredirs):
            self.log_debug("Redirect #%d to: %s" % (i, url))

            header = self.load(url, just_header=True)

            if header.get('location'):
                url = self.fixurl(header.get('location'), url)
                if update_pyfile:
                    self.pyfile.url = url
            else:
                return header
        return header


    def process(self, pyfile):
        """
        The "main" method of every hoster plugin, you **have to** overwrite it
        """
        raise NotImplementedError


    def set_reconnect(self, reconnect):
        self.log_debug("RECONNECT %s required" % ("" if reconnect else "not"),
                       "Previous wantReconnect: %s" % self.wantReconnect)
        self.wantReconnect = bool(reconnect)
        return True


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

        self.log_debug("WAIT set to timestamp %f" % new_wait_until,
                       "Previous waitUntil: %f"   % old_wait_until)

        self.pyfile.waitUntil = new_wait_until
        return True


    def wait(self, seconds=None, reconnect=None):
        """
        Waits the time previously set
        """
        pyfile = self.pyfile

        if seconds is not None:
            self.set_wait(seconds)

        if reconnect is not None:
            self.set_reconnect(reconnect)

        wait_time = pyfile.waitUntil - time.time()

        if wait_time < 1:
            self.log_warning(_("Invalid wait time interval"))
            return

        self.waiting = True

        status = pyfile.status  #@NOTE: Recheck in 0.4.10
        pyfile.setStatus("waiting")

        self.log_info(_("Waiting %s...") % format_time(wait_time))

        if self.wantReconnect:
            self.log_info(_("Requiring reconnection..."))
            if self.account:
                self.log_warning(_("Reconnection ignored due logged account"))

        if not self.wantReconnect or self.account:
            while pyfile.waitUntil > time.time():
                self.check_status()
                time.sleep(2)

        else:
            while pyfile.waitUntil > time.time():
                self.check_status()
                self.thread.m.reconnecting.wait(1)

                if self.thread.m.reconnecting.isSet():
                    self.waiting = False
                    self.wantReconnect = False

                    self.req.clearCookies()
                    raise Reconnect

                time.sleep(2)

        self.waiting = False
        pyfile.status = status  #@NOTE: Recheck in 0.4.10


    def skip(self, msg=""):
        """
        Skip and give msg
        """
        raise Skip(encode(msg or self.pyfile.error or self.pyfile.pluginname))  #@TODO: Remove `encode` in 0.4.10


    #@TODO: Remove in 0.4.10
    def fail(self, msg=""):
        """
        Fail and give msg
        """
        msg = msg.strip()

        if msg:
            self.pyfile.error = msg
        else:
            msg = self.pyfile.error or self.info.get('error') or self.pyfile.getStatusName()

        raise Fail(encode(msg))  #@TODO: Remove `encode` in 0.4.10


    def error(self, msg="", type=_("Parse")):
        type = _("%s error") % type.strip().capitalize() if type else _("Unknown")
        msg  = _("%(type)s: %(msg)s | Plugin may be out of date"
                 % {'type': type, 'msg': msg or self.pyfile.error})

        self.fail(msg)


    def abort(self, msg=""):
        """
        Abort and give msg
        """
        if msg:  #@TODO: Remove in 0.4.10
            self.pyfile.error = encode(msg)

        raise Abort


    #@TODO: Recheck in 0.4.10
    def offline(self, msg=""):
        """
        Fail and indicate file is offline
        """
        self.fail("offline")


    #@TODO: Recheck in 0.4.10
    def temp_offline(self, msg=""):
        """
        Fail and indicates file ist temporary offline, the core may take consequences
        """
        self.fail("temp. offline")


    def restart(self, msg="", premium=True):
        if not msg:
            msg = _("Restart plugin") if premium else _("Fallback to free processing")

        if not premium:
            if self.premium:
                self.restart_free = True
            else:
                self.fail("%s | %s" % (msg, _("Url was already processed as free")))

        self.req.clearCookies()

        raise Retry(encode(msg))  #@TODO: Remove `encode` in 0.4.10


    def retry(self, attemps=5, wait=1, msg=""):
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
            del frame

        if id not in self.retries:
            self.retries[id] = 0

        if 0 < attemps <= self.retries[id]:
            self.fail(msg or _("Max retries reached"))

        self.wait(wait, False)

        self.retries[id] += 1
        raise Retry(encode(msg))  #@TODO: Remove `encode` in 0.4.10


    def retry_captcha(self, attemps=10, wait=1, msg=_("Max captcha retries reached")):
        self.captcha.invalid()
        self.retry(attemps, wait, msg)


    def fixurl(self, url, baseurl=None, unquote=True):
        url     = fixurl(url, unquote=True)
        baseurl = fixurl(baseurl or self.pyfile.url, unquote=True)

        if not urlparse.urlparse(url).scheme:
            url_p = urlparse.urlparse(baseurl)
            baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
            url = urlparse.urljoin(baseurl, url)

        return fixurl(url, unquote)


    def load(self, *args, **kwargs):
        self.check_status()
        return super(Base, self).load(*args, **kwargs)


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
        super(Base, self).clean()

        for attr in ("account", "html", "pyfile", "thread"):
            if hasattr(self, attr):
                setattr(self, attr, None)
