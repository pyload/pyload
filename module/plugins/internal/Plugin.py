# -*- coding: utf-8 -*-

from __future__ import with_statement

import inspect
import os

if os.name is not "nt":
    import grp
    import pwd

import pycurl

import module.plugins.internal.utils as utils

from module.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload as Skip  #@TODO: Remove in 0.4.10
from module.plugins.internal.utils import *


class Plugin(object):
    __name__    = "Plugin"
    __type__    = "plugin"
    __version__ = "0.59"
    __status__  = "stable"

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
        log("%(plugintype)s %(pluginname)s: %(msg)s" %
            {'plugintype': plugintype.upper(),
             'pluginname': pluginname,
             'msg'       : msg})


    def log_debug(self, *args, **kwargs):
        self._log("debug", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            self.print_exc()


    def log_info(self, *args, **kwargs):
        self._log("info", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            self.print_exc()


    def log_warning(self, *args, **kwargs):
        self._log("warning", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            self.print_exc()


    def log_error(self, *args, **kwargs):
        self._log("error", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace', True):
            self.print_exc()


    def log_critical(self, *args, **kwargs):
        self._log("critical", self.__type__, self.__name__, args)
        if kwargs.get('trace', True):
            self.print_exc()


    def print_exc(self):
        frame = inspect.currentframe()
        print format_exc(frame.f_back)
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
        entry = json.dumps(value).encode('base64')
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
                value = json.loads(entry.decode('base64'))
        else:
            if not entry:
                value = default
            else:
                value = dict((k, json.loads(v.decode('base64'))) for k, v in value.items())

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
            maxredirs = self.get_config("maxredirs", default=5, plugin="UserAgentSwitcher")
            req.http.c.setopt(pycurl.MAXREDIRS, maxredirs)

        #@TODO: Move to network in 0.4.10
        if decode:
            html = html_unescape(html)

        #@TODO: Move to network in 0.4.10
        if isinstance(decode, basestring):
            html = utils.decode(html, decode)

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
                self.log_error(e)

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

                key   = key.strip().lower()
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
