# -*- coding: utf-8 -*-

from __future__ import with_statement

import datetime
import inspect
import os
import re
import urllib

if os.name != "nt":
    import grp
    import pwd

from module.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload as Skip  #@TODO: Remove in 0.4.10
from module.utils import fs_encode, fs_decode, html_unescape, save_join as fs_join


#@TODO: Move to utils in 0.4.10
def decode(string, encoding='utf8'):
    """ Decode string to unicode with utf8 """
    if type(string) is str:
        return string.decode(encoding, "replace")
    else:
        return string


#@TODO: Move to utils in 0.4.10
def encode(string, encoding='utf8'):
    """ Decode string to utf8 """
    if type(string) is unicode:
        return string.encode(encoding, "replace")
    else:
        return string


#@TODO: Move to utils in 0.4.10
def exists(path):
    if os.path.exists(path):
        if os.name == "nt":
            dir, name = os.path.split(path)
            return name in os.listdir(dir)
        else:
            return True
    else:
        return False


#@TODO: Move to utils in 0.4.10
def fixurl(url):
    return html_unescape(urllib.unquote(url.decode('unicode-escape'))).strip().rstrip('/')


#@TODO: Move to utils in 0.4.10
def timestamp():
    return int(time.time() * 1000)


def seconds_to_midnight(gmt=0):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=gmt)

    if now.hour == 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + datetime.timedelta(days=1)

    td = midnight.replace(hour=0, minute=10, second=0, microsecond=0) - now

    if hasattr(td, 'total_seconds'):
        res = td.total_seconds()
    else:  #@NOTE: work-around for python 2.5 and 2.6 missing datetime.timedelta.total_seconds
        res = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    return int(res)


def replace_patterns(string, ruleslist):
    for r in ruleslist:
        rf, rt = r
        string = re.sub(rf, rt, string)
    return string


#@TODO: Remove in 0.4.10 and fix CookieJar.setCookie
def set_cookie(cj, domain, name, value):
    return cj.setCookie(domain, name, encode(value))


def set_cookies(cj, cookies):
    for cookie in cookies:
        if isinstance(cookie, tuple) and len(cookie) == 3:
            set_cookie(cj, *cookie)


def parse_html_tag_attr_value(attr_name, tag):
    m = re.search(r"%s\s*=\s*([\"']?)((?<=\")[^\"]+|(?<=')[^']+|[^>\s\"'][^>\s]*)\1" % attr_name, tag, re.I)
    return m.group(2) if m else None


def parse_html_form(attr_str, html, input_names={}):
    for form in re.finditer(r"(?P<TAG><form[^>]*%s[^>]*>)(?P<CONTENT>.*?)</?(form|body|html)[^>]*>" % attr_str,
                            html, re.S | re.I):
        inputs = {}
        action = parse_html_tag_attr_value("action", form.group('TAG'))

        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('CONTENT'), re.S | re.I):
            name = parse_html_tag_attr_value("name", inputtag.group(1))
            if name:
                value = parse_html_tag_attr_value("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ""
                else:
                    inputs[name] = value

        if input_names:
            #: Check input attributes
            for key, val in input_names.items():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] is val:
                        continue
                    elif isinstance(val, tuple) and inputs[key] in val:
                        continue
                    elif hasattr(val, "search") and re.match(val, inputs[key]):
                        continue
                    break  #: Attibute value does not match
                else:
                    break  #: Attibute name does not match
            else:
                return action, inputs  #: Passed attribute check
        else:
            #: No attribute check
            return action, inputs

    return {}, None  #: No matching form found


#@TODO: Move to utils in 0.4.10
def chunks(iterable, size):
    it   = iter(iterable)
    item = list(islice(it, size))
    while item:
        yield item
        item = list(islice(it, size))


class Plugin(object):
    __name__    = "Plugin"
    __type__    = "hoster"
    __version__ = "0.29"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core):
        self._init(core)
        self.init()


    def _init(self, core):
        self.pyload = core
        self.info   = {}  #: Provide information in dict here
        self.req    = None


    def init(self):
        """
        Initialize the plugin (in addition to `__init__`)
        """
        pass


    def _log(self, level, plugintype, pluginname, messages):
        log = getattr(self.pyload.log, level)
        msg = encode(" | ".join((a if isinstance(a, basestring) else str(a)).strip() for a in messages if a))
        log("%(plugintype)s %(pluginname)s%(id)s: %(msg)s"
            % {'plugintype': plugintype.upper(),
               'pluginname': pluginname,
               'id'        : ("[%s]" % self.pyfile.id) if hasattr(self, 'pyfile') else "",
               'msg'       : msg})


    def log_debug(self, *args):
        if self.pyload.debug:
            return self._log("debug", self.__type__, self.__name__, args)


    def log_info(self, *args):
        return self._log("info", self.__type__, self.__name__, args)


    def log_warning(self, *args):
        return self._log("warning", self.__type__, self.__name__, args)


    def log_error(self, *args):
        return self._log("error", self.__type__, self.__name__, args)


    def log_critical(self, *args):
        return self._log("critical", self.__type__, self.__name__, args)


    def set_permissions(self, path):
        if not os.path.exists(path):
            return

        try:
            if self.pyload.config.get("permission", "change_file"):
                if os.path.isfile(path):
                    os.chmod(path, int(self.pyload.config.get("permission", "file"), 8))

                elif os.path.isdir(path):
                    os.chmod(path, int(self.pyload.config.get("permission", "folder"), 8))

        except OSError, e:
            self.log_warning(_("Setting path mode failed"), e)

        try:
            if os.name != "nt" and self.pyload.config.get("permission", "change_dl"):
                uid = pwd.getpwnam(self.pyload.config.get("permission", "user"))[2]
                gid = grp.getgrnam(self.pyload.config.get("permission", "group"))[2]
                os.chown(path, uid, gid)

        except OSError, e:
            self.log_warning(_("Setting owner and group failed"), e)


    def get_chunk_count(self):
        if self.chunk_limit <= 0:
            return self.pyload.config.get("download", "chunks")
        return min(self.pyload.config.get("download", "chunks"), self.chunk_limit)


    def set_config(self, option, value):
        """
        Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.pyload.config.setPlugin(self.__name__, option, value)


    def get_config(self, option, default="", plugin=None):
        """
        Returns config value for current plugin

        :param option:
        :return:
        """
        try:
            return self.pyload.config.getPlugin(plugin or self.__name__, option)

        except KeyError:
            self.log_debug("Config option `%s` not found, use default `%s`" % (option, default or None))  #@TODO: Restore to `log_warning` in 0.4.10
            return default


    def store(self, key, value):
        """
        Saves a value persistently to the database
        """
        self.pyload.db.setStorage(self.__name__, key, value)


    def retrieve(self, key, default=None):
        """
        Retrieves saved value or dict of all saved entries if key is None
        """
        return self.pyload.db.getStorage(self.__name__, key) or default


    def delete(self, key):
        """
        Delete entry in db
        """
        self.pyload.db.delStorage(self.__name__, key)


    def fail(self, reason):
        """
        Fail and give reason
        """
        raise Fail(encode(reason))  #@TODO: Remove `encode` in 0.4.10


    def error(self, reason="", type=_("Parse")):
        if not reason:
            type = _("Unknown")

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += (": %s" % reason.strip()) if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(encode(msg))  #@TODO: Remove `encode` in 0.4.10


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=True, multipart=False, req=None):
        """
        Load content at url and returns it

        :param url:
        :param get:
        :param post:
        :param ref:
        :param cookies:
        :param just_header: If True only the header will be retrieved and returned as dict
        :param decode: Wether to decode the output according to http header, should be True in most cases
        :return: Loaded content
        """
        if hasattr(self, 'pyfile') and self.pyfile.abort:
            self.abort()

        url = fixurl(url)

        if not url or not isinstance(url, basestring):
            self.fail(_("No url given"))

        if self.pyload.debug:
            self.log_debug("LOAD URL " + url,
                           *["%s=%s" % (key, val) for key, val in locals().items() if key not in ("self", "url")])

        if req is None:
            req = self.req or self.pyload.requestFactory.getRequest(self.__name__)

        #@TODO: Move to network in 0.4.10
        if hasattr(self, 'COOKIES') and isinstance(self.COOKIES, list):
            set_cookies(req.cj, self.COOKIES)

        res = req.load(url, get, post, ref, bool(cookies), just_header, multipart, decode is True)  #@TODO: Fix network multipart in 0.4.10

        #@TODO: Move to network in 0.4.10
        if decode:
            res = html_unescape(res)

        #@TODO: Move to network in 0.4.10
        if isinstance(decode, basestring):
            res = decode(res, decode)

        if self.pyload.debug:
            frame = inspect.currentframe()
            framefile = fs_join("tmp", self.__name__, "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))
            try:
                if not exists(os.path.join("tmp", self.__name__)):
                    os.makedirs(os.path.join("tmp", self.__name__))

                with open(framefile, "wb") as f:
                    del frame  #: Delete the frame or it wont be cleaned
                    f.write(encode(res))

            except IOError, e:
                self.log_error(e)

        if just_header:
            #: Parse header
            header = {'code': req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                key, none, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()

                if key in header:
                    if type(header[key]) is list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res


    def clean(self):
        """
        Clean everything and remove references
        """
        try:
            self.req.close()
        except Exception:
            pass

        for a in ("pyfile", "thread", "html", "req"):
            if hasattr(self, a):
                setattr(self, a, None)
