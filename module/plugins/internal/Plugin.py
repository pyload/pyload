# -*- coding: utf-8 -*-

from __future__ import with_statement

import inspect
import os
import pycurl
import re

if os.name != "nt":
    import grp
    import pwd


from module.network.RequestFactory import getRequest as get_request
from module.plugins.Plugin import Abort, Fail, Reconnect, Retry, SkipDownload as Skip  #@TODO: Remove in 0.4.10
from module.plugins.internal.misc import (Config, DB, decode, encode, exists, fixurl, fsjoin,
                                          format_exc, html_unescape, parse_html_header, remove, set_cookies)


class Plugin(object):
    __name__    = "Plugin"
    __type__    = "plugin"
    __version__ = "0.66"
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
        #: Internal modules
        self.pyload = core
        self.db     = DB(self)
        self.config = Config(self)

        #: Provide information in dict here
        self.info = {}

        #: Browser instance, see `network.Browser`
        self.req = self.pyload.requestFactory.getRequest(self.classname)
        self.req.setOption("timeout", 60)  #@TODO: Remove in 0.4.10

        #: Last loaded html
        self.last_html   = ""
        self.last_header = {}


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
            self._print_exc()


    def log_info(self, *args, **kwargs):
        self._log("info", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            self._print_exc()


    def log_warning(self, *args, **kwargs):
        self._log("warning", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace'):
            self._print_exc()


    def log_error(self, *args, **kwargs):
        self._log("error", self.__type__, self.__name__, args)
        if self.pyload.debug and kwargs.get('trace', True):
            self._print_exc()


    def log_critical(self, *args, **kwargs):
        self._log("critical", self.__type__, self.__name__, args)
        if kwargs.get('trace', True):
            self._print_exc()


    def _print_exc(self):
        frame = inspect.currentframe()
        try:
            print format_exc(frame.f_back)
        finally:
            del frame


    def remove(self, path, trash=False):  #@TODO: Change to `trash=True` in 0.4.10
        try:
            remove(path, trash)

        except (NameError, OSError), e:
            self.log_warning(_("Error removing `%s`") % os.path.abspath(path), e)
            return False

        else:
            self.log_info(_("Path deleted: ") + os.path.abspath(path))
            return True


    def set_permissions(self, path):
        path = encode(path)

        if not exists(path):
            return

        file_perms = False
        dl_perms   = False

        if self.pyload.config.get('permission', "change_file"):
            permission = self.pyload.config.get('permission', "folder" if os.path.isdir(path) else "file")
            mode = int(permission, 8)
            os.chmod(path, mode)

        if os.name != "nt" and self.pyload.config.get('permission', "change_dl"):
            uid = pwd.getpwnam(self.pyload.config.get('permission', "user"))[2]
            gid = grp.getgrnam(self.pyload.config.get('permission', "group"))[2]
            os.chown(path, uid, gid)


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
                           *["%s=%s" % (key, value) for key, value in locals().items()
                             if key not in ("self", "url", "_[1]")])

        url = fixurl(url, unquote=True)  #: Recheck in 0.4.10

        if req is False:
            req = get_request()
            req.setOption("timeout", 60)  #@TODO: Remove in 0.4.10

        elif not req:
            req = self.req

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
            maxredirs = int(self.pyload.api.getConfigValue("UserAgentSwitcher", "maxredirs", "plugin")) or 5  #@TODO: Remove `int` in 0.4.10
            req.http.c.setopt(pycurl.MAXREDIRS, maxredirs)

        #@TODO: Move to network in 0.4.10
        if decode:
            html = html_unescape(html)

        #@TODO: Move to network in 0.4.10
        if isinstance(decode, basestring):
            html = decode(html, decode)

        self.last_html = html

        if self.pyload.debug:
            self.dump_html()

        #@TODO: Move to network in 0.4.10
        header = {'code': req.code, 'url': req.lastEffectiveURL}
        header.update(parse_html_header(req.http.header if hasattr(req, "http") else req.header))  #@NOTE: req can be a HTTPRequest or a Browser object

        self.last_header = header

        if just_header:
            return header
        else:
            return html


    def dump_html(self):
        frame = inspect.currentframe()

        try:
            framefile = fsjoin("tmp", self.classname, "%s_line%s.dump.html"
                               % (frame.f_back.f_code.co_name, frame.f_back.f_lineno))

            if not exists(os.path.join("tmp", self.classname)):
                os.makedirs(os.path.join("tmp", self.classname))

            with open(framefile, "wb") as f:
                try:
                    html = encode(self.last_html)
                except Exception:
                    html = self.last_html

                f.write(html)

        except IOError, e:
            self.log_error(e)

        finally:
            del frame  #: Delete the frame or it wont be cleaned


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
