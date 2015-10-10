# -*- coding: utf-8 -*-

import inspect
import mimetypes
import os
import re
import time
import urlparse

from module.plugins.internal.Captcha import Captcha
from module.plugins.internal.Plugin import (Plugin, Abort, Fail, Reconnect, Retry, Skip,
                                            decode, encode, fixurl, parse_html_form,
                                            parse_name, replace_patterns)


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


#@NOTE: `check_abort` decorator
def check_abort(fn):

    def wrapper(self, *args, **kwargs):
        self.check_abort()
        return fn(self, *args, **kwargs)

    return wrapper


class Base(Plugin):
    __name__    = "Base"
    __type__    = "base"
    __version__ = "0.11"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"  , "bool", "Activated"                       , True),
                   ("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Base plugin for Hoster and Crypter"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = []


    def __init__(self, pyfile):
        self._init(pyfile.m.core)

        #:
        self.premium = None

        #: Engage wan reconnection
        self.wantReconnect = False  #@TODO: Change to `want_reconnect` in 0.4.10

        #: Enable simultaneous processing of multiple downloads
        self.multiDL = True  #@TODO: Change to `multi_dl` in 0.4.10

        #: time.time() + wait in seconds
        self.wait_until = 0
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
        self.html = None

        #: Dict of the amount of retries already made
        self.retries = {}

        self.init_base()
        self.init()


    def _log(self, level, plugintype, pluginname, messages):
        log = getattr(self.pyload.log, level)
        msg = u" | ".join(decode(a).strip() for a in messages if a)
        log("%(plugintype)s %(pluginname)s[%(id)s]: %(msg)s"
            % {'plugintype': plugintype.upper(),
               'pluginname': pluginname,
               'id'        : self.pyfile.id,
               'msg'       : msg})


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


    def init_base(self):
        pass


    def init(self):
        """
        Initialize the plugin (in addition to `__init__`)
        """
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
        self.html          = ""
        self.pyfile.error  = ""
        self.last_html     = None

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


    def _process(self, thread):
        """
        Handles important things to do before starting
        """
        self.thread = thread

        self._setup()

        # self.pyload.hookManager.downloadPreparing(self.pyfile)  #@TODO: Recheck in 0.4.10
        self.check_abort()

        self.pyfile.setStatus("starting")

        self.log_debug("PROCESS URL " + self.pyfile.url,
                       "PLUGIN VERSION %s" % self.__version__)
        self.process(self.pyfile)


    #: Deprecated method, use `_process` instead (Remove in 0.4.10)
    def preprocessing(self, *args, **kwargs):
        return self._process(*args, **kwargs)


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

        self.waiting = True

        status = pyfile.status  #@NOTE: Recheck in 0.4.10
        pyfile.setStatus("waiting")

        self.log_info(_("Waiting %d seconds...") % (pyfile.waitUntil - time.time()))

        if self.wantReconnect:
            self.log_info(_("Requiring reconnection..."))
            if self.account:
                self.log_warning("Ignore reconnection due logged account")

        if not self.wantReconnect or self.account:
            while pyfile.waitUntil > time.time():
                self.check_abort()
                time.sleep(2)

        else:
            while pyfile.waitUntil > time.time():
                self.check_abort()
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
    def fail(self, msg):
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
                self.rst_free = True
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
        #url = fixurl(url, unquote=False)

        if not baseurl:
            baseurl = fixurl(self.pyfile.url)

        if not urlparse.urlparse(url).scheme:
            url_p = urlparse.urlparse(baseurl)
            baseurl = "%s://%s" % (url_p.scheme, url_p.netloc)
            url = urlparse.urljoin(baseurl, url)

        return fixurl(url, unquote)


    @check_abort
    def load(self, *args, **kwargs):
        return super(Base, self).load(*args, **kwargs)


    def check_abort(self):
        if not self.pyfile.abort:
            return

        if self.pyfile.status is 8:
            self.fail()

        elif self.pyfile.status is 4:
            self.skip(self.pyfile.statusname)

        elif self.pyfile.status is 1:
            self.offline()

        elif self.pyfile.status is 6:
            self.temp_offline()

        else:
            self.abort()


    def direct_link(self, url, redirect=False):
        link = ""

        if not redirect:
            conn = 1

        elif type(redirect) is int:
            conn = max(redirect, 1)

        else:
            conn = self.get_config("maxredirs", 5, plugin="UserAgentSwitcher")

        for i in xrange(conn):
            try:
                self.log_debug("Redirect #%d to: %s" % (i, url))
                header = self.load(url, just_header=True)

            except Exception:  #: Bad bad bad... rewrite this part in 0.4.10
                res = self.load(url,
                                just_header=True,
                                req=self.pyload.requestFactory.getRequest(self.classname))

                header = {'code': req.code}
                for line in res.splitlines():
                    line = line.strip()
                    if not line or ":" not in line:
                        continue

                    key, none, value = line.partition(":")
                    key              = key.lower().strip()
                    value            = value.strip()

                    if key in header:
                        header_key = header.get(key)
                        if type(header_key) is list:
                            header_key.append(value)
                        else:
                            header[key] = [header_key, value]
                    else:
                        header[key] = value

            if 'content-disposition' in header:
                link = url

            elif header.get('location'):
                location = self.fixurl(header.get('location'), url)

                if header.get('code') == 302:
                    link = location

                if redirect:
                    url = location
                    continue

            else:
                extension = os.path.splitext(parse_name(url))[-1]

                if header.get('content-type'):
                    mimetype = header.get('content-type').split(';')[0].strip()

                elif extension:
                    mimetype = mimetypes.guess_type(extension, False)[0] or "application/octet-stream"

                else:
                    mimetype = ""

                if mimetype and (link or 'html' not in mimetype):
                    link = url
                else:
                    link = ""

            break

        else:
            try:
                self.log_error(_("Too many redirects"))

            except Exception:
                pass

        return link


    def parse_html_form(self, attr_str="", input_names={}):
        return parse_html_form(attr_str, self.html, input_names)


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
