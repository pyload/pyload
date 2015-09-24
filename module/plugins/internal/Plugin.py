# -*- coding: utf-8 -*-

from __future__ import with_statement

import datetime
import inspect
import os
import re
import sys
import traceback
import urllib
import urlparse

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
        return unicode(string)


#@TODO: Move to utils in 0.4.10
def encode(string, encoding='utf8'):
    """ Decode string to utf8 """
    if type(string) is unicode:
        return string.encode(encoding, "replace")
    else:
        return str(string)


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
def parse_name(url):
    url = urllib.unquote(url)
    url = url.decode('unicode-escape')
    url = html_unescape(url)
    url = urllib.quote(url)

    url_p = urlparse.urlparse(url.strip().rstrip('/'))

    name = (url_p.path.split('/')[-1] or
            url_p.query.split('=', 1)[::-1][0].split('&', 1)[0] or
            url_p.netloc.split('.', 1)[0])

    return urllib.unquote(name)


#@TODO: Move to utils in 0.4.10
def timestamp():
    return int(time.time() * 1000)


#@TODO: Move to utils in 0.4.10
def which(program):
    """
    Works exactly like the unix command which
    Courtesy of http://stackoverflow.com/a/377028/675646
    """
    isExe = lambda x: os.path.isfile(x) and os.access(x, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if isExe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path.strip('"'), program)
            if isExe(exe_file):
                return exe_file


def seconds_to_midnight(utc=None):
    if utc is None:
        now = datetime.datetime.today()
    else:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=utc)

    midnight = now.replace(hour=0, minute=10, second=0, microsecond=0) + datetime.timedelta(days=1)

    return (midnight - now).seconds


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
    __type__    = "plugin"
    __version__ = "0.37"
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


    def __repr__(self):
        return "<%(type)s %(name)s>" % {'type': self.__type__.capitalize(),
                                        'name': self.__name__}


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
        msg = u" | ".join(decode(a).strip() for a in messages if a)
        log("%(plugintype)s %(pluginname)s: %(msg)s"
            % {'plugintype': plugintype.upper(),
               'pluginname': pluginname,
               'msg'       : msg})


    def log_debug(self, *args):
        if not self.pyload.debug:
            return
        self._log("debug", self.__type__, self.__name__, args)


    def log_info(self, *args):
        self._log("info", self.__type__, self.__name__, args)


    def log_warning(self, *args):
        self._log("warning", self.__type__, self.__name__, args)
        if self.pyload.debug:
            traceback.print_exc()


    def log_error(self, *args):
        self._log("error", self.__type__, self.__name__, args)
        if self.pyload.debug:
            traceback.print_exc()


    def log_critical(self, *args):
        return self._log("critical", self.__type__, self.__name__, args)
        if self.pyload.debug:
            traceback.print_exc()


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


    def fail(self, msg):
        """
        Fail and give msg
        """
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
        if self.pyload.debug:
            self.log_debug("LOAD URL " + url,
                           *["%s=%s" % (key, val) for key, val in locals().items() if key not in ("self", "url")])

        if req is None:
            req = self.req or self.pyload.requestFactory.getRequest(self.__name__)

        #@TODO: Move to network in 0.4.10
        if isinstance(cookies, list):
            set_cookies(req.cj, cookies)

        res = req.load(url, get, post, ref, bool(cookies), just_header, multipart, decode is True)  #@TODO: Fix network multipart in 0.4.10

        #@TODO: Move to network in 0.4.10
        if decode:
            res = html_unescape(res)

        #@TODO: Move to network in 0.4.10
        if isinstance(decode, basestring):
            res = sys.modules[self.__name__].decode(res, decode)  #@TODO: See #1787, use utils.decode() in 0.4.10

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
