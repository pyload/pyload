# -*- coding: utf-8 -*-

from __future__ import with_statement

import inspect
import os
import re
import urllib

from module.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload as Skip  #@TODO: Remove in 0.4.10
from module.utils import fs_encode, fs_decode, html_unescape, save_join as fs_join


#@TODO: Move to utils in 0.4.10
def fixurl(url):
    return html_unescape(urllib.unquote(url.decode('unicode-escape'))).strip()


#@TODO: Move to utils in 0.4.10
def timestamp():
    return int(time.time() * 1000)


def seconds_to_midnight(gmt=0):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=gmt)

    if now.hour is 0 and now.minute < 10:
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


def set_cookies(cj, cookies):
    for cookie in cookies:
        if isinstance(cookie, tuple) and len(cookie) == 3:
            domain, name, value = cookie
            cj.setCookie(domain, name, value)


def parse_html_tag_attr_value(attr_name, tag):
    m = re.search(r"%s\s*=\s*([\"']?)((?<=\")[^\"]+|(?<=')[^']+|[^>\s\"'][^>\s]*)\1" % attr_name, tag, re.I)
    return m.group(2) if m else None


def parse_html_form(attr_str, html, input_names={}):
    for form in re.finditer(r"(?P<TAG><form[^>]*%s[^>]*>)(?P<CONTENT>.*?)</?(form|body|html)[^>]*>" % attr_str,
                            html, re.S | re.I):
        inputs = {}
        action = parseHtmlTagAttrValue("action", form.group('TAG'))

        for inputtag in re.finditer(r'(<(input|textarea)[^>]*>)([^<]*(?=</\2)|)', form.group('CONTENT'), re.S | re.I):
            name = parseHtmlTagAttrValue("name", inputtag.group(1))
            if name:
                value = parseHtmlTagAttrValue("value", inputtag.group(1))
                if not value:
                    inputs[name] = inputtag.group(3) or ""
                else:
                    inputs[name] = value

        if input_names:
            #: Check input attributes
            for key, val in input_names.iteritems():
                if key in inputs:
                    if isinstance(val, basestring) and inputs[key] == val:
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
    __version__ = "0.13"

    __pattern__ = r'^unmatchable$'
    __config__  = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"         , "RaNaN@pyload.org" ),
                       ("spoob"         , "spoob@pyload.org" ),
                       ("mkaay"         , "mkaay@mkaay.de"   ),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def __init__(self, core):
        self.core = core

        #: Provide information in dict here
        self.info = {}


    def _log(self, level, args):
        log = getattr(self.core.log, level)
        msg = fs_encode(" | ".join((a if isinstance(a, basestring) else str(a)).strip() for a in args if a))  #@NOTE: `fs_encode` -> `encode` in 0.4.10
        log("%(plugin)s%(id)s: %(msg)s" % {'plugin': self.__name__,
                                           'id'    : ("[%s]" % self.pyfile.id) if hasattr(self, 'pyfile') else "",
                                           'msg'   : msg or _(level.upper() + " MARK")})


    def log_debug(self, *args):
        if self.core.debug:
            return self._log("debug", args)


    def log_info(self, *args):
        return self._log("info", args)


    def log_warning(self, *args):
        return self._log("warning", args)


    def log_error(self, *args):
        return self._log("error", args)


    def log_critical(self, *args):
        return self._log("critical", args)


    def set_config(self, option, value):
        """
        Set config value for current plugin

        :param option:
        :param value:
        :return:
        """
        self.core.config.setPlugin(self.__name__, option, value)


    #: Deprecated method, use `set_config` instead
    def setConf(self, *args, **kwargs):
        """
        See `set_config`
        """
        return self.set_config(*args, **kwargs)


    def get_config(self, option, default="", plugin=None):
        """
        Returns config value for current plugin

        :param option:
        :return:
        """
        try:
            return self.core.config.getPlugin(plugin or self.__name__, option)

        except KeyError:
            self.log_warning(_("Config option or plugin not found"))
            return default


    #: Deprecated method, use `get_config` instead
    def getConf(self, *args, **kwargs):
        """
        See `get_config`
        """
        return self.get_config(*args, **kwargs)


    def store(self, key, value):
        """
        Saves a value persistently to the database
        """
        self.core.db.setStorage(self.__name__, key, value)


    #: Deprecated method, use `store` instead
    def setStorage(self, *args, **kwargs):
        """
        Same as `store`
        """
        return self.store(*args, **kwargs)


    def retrieve(self, key, default=None):
        """
        Retrieves saved value or dict of all saved entries if key is None
        """
        return self.core.db.getStorage(self.__name__, key) or default


    #: Deprecated method, use `retrieve` instead
    def getStorage(self, *args, **kwargs):
        """
        Same as `retrieve`
        """
        return self.retrieve(*args, **kwargs)


    def delete(self, key):
        """
        Delete entry in db
        """
        self.core.db.delStorage(self.__name__, key)


    #: Deprecated method, use `delete` instead
    def delStorage(self, *args, **kwargs):
        """
        Same as `delete`
        """
        return self.delete(*args, **kwargs)


    def fail(self, reason):
        """
        Fail and give reason
        """
        raise Fail(fs_encode(reason))


    def error(self, reason="", type=_("Parse")):
        if not reason:
            type = _("Unknown")

        msg  = _("%s error") % type.strip().capitalize() if type else _("Error")
        msg += (": %s" % reason.strip()) if reason else ""
        msg += _(" | Plugin may be out of date")

        raise Fail(msg)


    def load(self, url, get={}, post={}, ref=True, cookies=True, just_header=False, decode=True, multipart=True, req=None):
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

        if self.core.debug:
            self.log_debug("Load url " + url, *["%s=%s" % (key, val) for key, val in locals().iteritems() if key not in ("self", "url")])

        if req is None:
            if hasattr(self, "req"):
                req = self.req
            else:
                req = self.core.requestFactory.getRequest(self.__name__)

        res = req.load(url, get, post, ref, cookies, just_header, multipart, bool(decode))

        if decode:
            res = html_unescape(res).decode(decode if isinstance(decode, basestring) else 'utf8')

        if self.core.debug:
            frame = inspect.currentframe()
            framefile = fs_join("tmp", self.__name__, "%s_line%s.dump.html" % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))
            try:
                if not os.path.exists(os.path.join("tmp", self.__name__)):
                    os.makedirs(os.path.join("tmp", self.__name__))

                with open(framefile, "wb") as f:
                    del frame  #: Delete the frame or it wont be cleaned
                    f.write(res.encode('utf8'))
            except IOError, e:
                self.log_error(e)

        if just_header:
            #: Parse header
            header = {"code": req.code}
            for line in res.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue

                key, none, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()

                if key in header:
                    if type(header[key]) == list:
                        header[key].append(value)
                    else:
                        header[key] = [header[key], value]
                else:
                    header[key] = value
            res = header

        return res
