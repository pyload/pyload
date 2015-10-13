# -*- coding: utf-8 -*-

from __future__ import with_statement

import datetime
import inspect
import os
import re
import sys
import time
import traceback
import urllib
import urlparse

import pycurl

if os.name is not "nt":
    import grp
    import pwd

from module.common.json_layer import json_dumps, json_loads
from module.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload as Skip  #@TODO: Remove in 0.4.10
from module.utils import (fs_encode, fs_decode, get_console_encoding, html_unescape,
                          parseFileSize as parse_size, save_join as fs_join)


#@TODO: Move to utils in 0.4.10
def isiterable(obj):
    return hasattr(obj, "__iter__")


#@TODO: Move to utils in 0.4.10
def decode(string, encoding=None):
    """Encoded string (default to UTF-8) -> unicode string"""
    if type(string) is str:
        try:
            res = unicode(string, encoding or "utf-8")

        except UnicodeDecodeError, e:
            if encoding:
                raise UnicodeDecodeError(e)

            encoding = get_console_encoding(sys.stdout.encoding)
            res = unicode(string, encoding)

    elif type(string) is unicode:
        res = string

    else:
        res = unicode(string)

    return res


#@TODO: Remove in 0.4.10
def _decode(*args, **kwargs):
    return decode(*args, **kwargs)


#@TODO: Move to utils in 0.4.10
def encode(string, encoding=None, decoding=None):
    """Unicode or decoded string -> encoded string (default to UTF-8)"""
    if type(string) is unicode:
        res = string.encode(encoding or "utf-8")

    elif type(string) is str:
        res = encode(decode(string, decoding), encoding)

    else:
        res = str(string)

    return res


#@TODO: Move to utils in 0.4.10
def exists(path):
    if os.path.exists(path):
        if os.name is "nt":
            dir, name = os.path.split(path.rstrip(os.sep))
            return name in os.listdir(dir)
        else:
            return True
    else:
        return False


def fixurl(url, unquote=None):
    newurl = urllib.unquote(url)

    if unquote is None:
        unquote = newurl == url

    newurl = html_unescape(decode(newurl).decode('unicode-escape'))
    newurl = re.sub(r'(?<!:)/{2,}', '/', newurl).strip().lstrip('.')

    if not unquote:
        newurl = urllib.quote(newurl)

    return newurl


def parse_name(string):
    path  = fixurl(decode(string), unquote=False)
    url_p = urlparse.urlparse(path.rstrip('/'))
    name  = (url_p.path.split('/')[-1] or
             url_p.query.split('=', 1)[::-1][0].split('&', 1)[0] or
             url_p.netloc.split('.', 1)[0])

    return urllib.unquote(name)


#@TODO: Move to utils in 0.4.10
def str2int(string):
    try:
        return int(string)
    except:
        pass

    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
            "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety"]

    o_tuple = [(w, i) for i, w in enumerate(ones)]
    t_tuple = [(w, i * 10) for i, w in enumerate(tens)]

    numwords = dict(o_tuple + t_tuple)
    tokens   = re.split(r"[\s\-]+", string.lower())

    try:
        return sum(numwords[word] for word in tokens)
    except:
        return 0


def parse_time(string):
    if re.search("da(il)?y|today", string):
        seconds = seconds_to_midnight()

    else:
        regex   = re.compile(r'(\d+| (?:this|an?) )\s*(hr|hour|min|sec|)', re.I)
        seconds = sum((int(v) if v.strip() not in ("this", "a", "an") else 1) *
                      {'hr': 3600, 'hour': 3600, 'min': 60, 'sec': 1, '': 1}[u.lower()]
                      for v, u in regex.findall(string))
    return seconds


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


def seconds_to_nexthour(strict=False):
    now      = datetime.datetime.today()
    nexthour = now.replace(minute=0 if strict else 1, second=0, microsecond=0) + datetime.timedelta(hours=1)
    return (nexthour - now).seconds


def seconds_to_midnight(utc=None, strict=False):
    if utc is None:
        now = datetime.datetime.today()
    else:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=utc)

    midnight = now.replace(hour=0, minute=0 if strict else 1, second=0, microsecond=0) + datetime.timedelta(days=1)

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
                            html, re.I | re.S):
        inputs = {}
        action = parse_html_tag_attr_value("action", form.group('TAG'))

        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('CONTENT'), re.I | re.S):
            name = parse_html_tag_attr_value("name", inputtag.group(1))
            if name:
                value = parse_html_tag_attr_value("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ""
                else:
                    inputs[name] = value

        if not input_names:
            #: No attribute check
            return action, inputs
        else:
            #: Check input attributes
            for key, val in input_names.items():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] is val:
                        continue
                    elif isinstance(val, tuple) and inputs[key] in val:
                        continue
                    elif hasattr(val, "search") and re.match(val, inputs[key]):
                        continue
                    else:
                        break  #: Attibute value does not match
                else:
                    break  #: Attibute name does not match
            else:
                return action, inputs  #: Passed attribute check

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
    __version__ = "0.57"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core):
        self._init(core)
        self.init()


    def __repr__(self):
        return "<%(type)s %(name)s>" % {'type': self.__type__.capitalize(),
                                        'name': self.classname}


    @property
    def classname(self):
        return self.__class__.__name__


    def _init(self, core):
        self.pyload    = core
        self.info      = {}    #: Provide information in dict here
        self.req       = None  #: Browser instance, see `network.Browser`
        self.last_html = None


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


    def log_debug(self, *args, **kwargs):
        self._log("debug", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            frame = inspect.currentframe()
            print "Traceback (most recent call last):"
            traceback.print_stack(frame.f_back)
            del frame


    def log_info(self, *args, **kwargs):
        self._log("info", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            frame = inspect.currentframe()
            print "Traceback (most recent call last):"
            traceback.print_stack(frame.f_back)
            del frame


    def log_warning(self, *args, **kwargs):
        self._log("warning", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            frame = inspect.currentframe()
            print "Traceback (most recent call last):"
            traceback.print_stack(frame.f_back)
            del frame


    def log_error(self, *args, **kwargs):
        self._log("error", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace', True):
            frame = inspect.currentframe()
            print "Traceback (most recent call last):"
            traceback.print_stack(frame.f_back)
            del frame


    def log_critical(self, *args, **kwargs):
        self._log("critical", self.__type__, self.__name__, args)
        if kwargs.get('trace', True):
            frame = inspect.currentframe()
            print "Traceback (most recent call last):"
            traceback.print_stack(frame.f_back)
            del frame


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
            if os.name is not "nt" and self.pyload.config.get("permission", "change_dl"):
                uid = pwd.getpwnam(self.pyload.config.get("permission", "user"))[2]
                gid = grp.getgrnam(self.pyload.config.get("permission", "group"))[2]
                os.chown(path, uid, gid)

        except OSError, e:
            self.log_warning(_("Setting owner and group failed"), e)


    def set_config(self, option, value, plugin=None):
        """
        Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.pyload.api.setConfigValue(plugin or self.classname, option, value, section="plugin")


    def get_config(self, option, default="", plugin=None):
        """
        Returns config value for current plugin

        :param option:
        :return:
        """
        try:
            return self.pyload.config.getPlugin(plugin or self.classname, option)

        except KeyError:
            self.log_debug("Config option `%s` not found, use default `%s`" % (option, default or None))  #@TODO: Restore to `log_warning` in 0.4.10
            return default


    def store(self, key, value):
        """
        Saves a value persistently to the database
        """
        value = map(decode, value) if isiterable(value) else decode(value)
        entry = json_dumps(value).encode('base64')
        self.pyload.db.setStorage(self.classname, key, entry)


    def retrieve(self, key=None, default=None):
        """
        Retrieves saved value or dict of all saved entries if key is None
        """
        entry = self.pyload.db.getStorage(self.classname, key)

        if key:
            if entry is None:
                value = default
            else:
                value = json_loads(entry.decode('base64'))
        else:
            if not entry:
                value = default
            else:
                value = dict((k, json_loads(v.decode('base64'))) for k, v in value.items())

        return value


    def delete(self, key):
        """
        Delete entry in db
        """
        self.pyload.db.delStorage(self.classname, key)


    def fail(self, msg):
        """
        Fail and give msg
        """
        raise Fail(encode(msg))  #@TODO: Remove `encode` in 0.4.10


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=True,
             multipart=False, redirect=True, req=None):
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
                           *["%s=%s" % (key, val) for key, val in locals().items() if key not in ("self", "url", "_[1]")])

        url = fixurl(url, unquote=True)  #: Recheck in 0.4.10

        if req is None:
            req = self.req or self.pyload.requestFactory.getRequest(self.classname)

        #@TODO: Move to network in 0.4.10
        if isinstance(cookies, list):
            set_cookies(req.cj, cookies)

        #@TODO: Move to network in 0.4.10
        if not redirect:
            req.http.c.setopt(pycurl.FOLLOWLOCATION, 0)

        elif type(redirect) is int:
            req.http.c.setopt(pycurl.MAXREDIRS, redirect)

        html = req.load(url, get, post, ref, bool(cookies), just_header, multipart, decode is True)  #@TODO: Fix network multipart in 0.4.10

        #@TODO: Move to network in 0.4.10
        if not redirect:
            req.http.c.setopt(pycurl.FOLLOWLOCATION, 1)

        elif type(redirect) is int:
            req.http.c.setopt(pycurl.MAXREDIRS,
                              self.get_config("maxredirs", 5, plugin="UserAgentSwitcher"))

        #@TODO: Move to network in 0.4.10
        if decode:
            html = html_unescape(html)

        #@TODO: Move to network in 0.4.10
        if isinstance(decode, basestring):
            html = _decode(html, decode)  #@NOTE: Use `utils.decode()` in 0.4.10

        self.last_html = html

        if self.pyload.debug:
            frame = inspect.currentframe()

            try:
                framefile = fs_join("tmp", self.classname, "%s_line%s.dump.html" %
                                    (frame.f_back.f_code.co_name, frame.f_back.f_lineno))

                if not exists(os.path.join("tmp", self.classname)):
                    os.makedirs(os.path.join("tmp", self.classname))

                with open(framefile, "wb") as f:
                    f.write(encode(html))

            except IOError, e:
                self.log_error(e, trace=True)

            finally:
                del frame  #: Delete the frame or it wont be cleaned

        if not just_header:
            return html

        else:
            #@TODO: Move to network in 0.4.10
            header = {'code': req.code}
            for line in html.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                key, none, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()

                if key in header:
                    header_key = header.get(key)
                    if type(header_key) is list:
                        header_key.append(value)
                    else:
                        header[key] = [header_key, value]
                else:
                    header[key] = value

            return header


    def clean(self):
        """
        Remove references
        """
        try:
            self.req.clearCookies()
            self.req.close()

        except Exception:
            pass

        else:
            self.req = None
