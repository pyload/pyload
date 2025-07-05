# -*- coding: utf-8 -*-

import inspect
import os
import sys

import pycurl
from pyload.core.network.exceptions import Fail, Skip
from pyload.core.network.request_factory import get_request
from pyload.core.utils import fs
from pyload.core.utils.old import fixurl
from pyload.core.utils.web import purge

from ..helpers import DB, Config, exists, format_exc, parse_html_header, set_cookies

if os.name != "nt":
    import grp
    import pwd


class BasePlugin:
    __name__ = "BasePlugin"
    __type__ = "base"
    __version__ = "0.79"
    __status__ = "stable"

    __config__ = []  #: [("name", "type", "desc", "default")]

    __description__ = """Base plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def __init__(self, core):
        self._init(core)
        self.init()

    def __repr__(self):
        return "<{type} {name}>".format(
            type=self.__type__.capitalize(), name=self.classname
        )

    @property
    def classname(self):
        return self.__class__.__name__

    def _init(self, core):
        #: Internal modules
        self.pyload = core
        self._ = core._
        self.db = DB(self)
        self.config = Config(self)

        #: Provide information in dict here
        self.info = {}

        #: Browser instance, see `network.Browser`
        self.req = self.pyload.request_factory.get_request(self.classname)

        #: Last loaded html
        self.last_html = ""
        self.last_header = {}

    def init(self):
        """
        Initialize the plugin (in addition to `__init__`)
        """
        pass

    # TODO: Rewrite to use unique logger from logfactory
    def _log(self, level, plugintype, pluginname, args, kwargs):
        log = getattr(self.pyload.log, level)
        log(
            "{plugintype} {pluginname}: {msg}".format(
                plugintype=plugintype.upper(),
                pluginname=pluginname,
                msg=" | ".join(["%s"] * len(args)),
            ),
            *args,
            **kwargs,
        )

    def log_debug(self, *args, **kwargs):
        self._log("debug", self.__type__, self.__name__, args, kwargs)

    def log_info(self, *args, **kwargs):
        self._log("info", self.__type__, self.__name__, args, kwargs)

    def log_warning(self, *args, **kwargs):
        self._log("warning", self.__type__, self.__name__, args, kwargs)

    def log_error(self, *args, **kwargs):
        kwargs["exc_info"] = kwargs.get(
            "exc_info", self.pyload.debug > 1 and sys.exc_info() != (None, None, None)
        )
        kwargs["stack_info"] = kwargs.get("stack_info", self.pyload.debug > 2)
        self._log("error", self.__type__, self.__name__, args, kwargs)

    def log_critical(self, *args, **kwargs):
        kwargs["exc_info"] = kwargs.get(
            "exc_info", sys.exc_info() != (None, None, None)
        )
        kwargs["stack_info"] = kwargs.get("stack_info", True)
        self._log("critical", self.__type__, self.__name__, args, kwargs)

    # def _print_exc(self):
    # frame = inspect.currentframe()
    # try:
    # print(format_exc(frame.f_back))
    # finally:
    # del frame

    def remove(self, path, try_trash=True):  # TODO: Change to `trash=True` in 0.6.x
        try:
            fs.remove(path, try_trash=try_trash)

        except (NameError, OSError) as exc:
            self.log_warning(
                self._("Error removing `{}`").format(os.path.realpath(path)), exc
            )
            return False

        else:
            self.log_info(self._("Path deleted: ") + os.path.realpath(path))
            return True

    def set_permissions(self, path):
        path = os.fsdecode(path)

        if not exists(path):
            return

        if self.pyload.config.get("permission", "change_file"):
            permission = self.pyload.config.get(
                "permission", "folder" if os.path.isdir(path) else "file"
            )
            mode = int(permission, 8)
            os.chmod(path, mode)

        if os.name != "nt" and self.pyload.config.get("permission", "change_dl"):
            uid = pwd.getpwnam(self.pyload.config.get("permission", "user"))[2]
            gid = grp.getgrnam(self.pyload.config.get("permission", "group"))[2]
            os.chown(path, uid, gid)

    def skip(self, msg):
        """
        Skip and give msg.
        """
        raise Skip(msg)

    def fail(self, msg):
        """
        Fail and give msg.
        """
        raise Fail(msg)

    def load(
        self,
        url,
        get={},
        post={},
        ref=True,
        cookies=True,
        just_header=False,
        decode=True,
        multipart=False,
        redirect=True,
        req=None,
    ):
        """
        Load content at url and returns it.

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
            self.log_debug(
                "LOAD URL " + url,
                *[
                    "{}={}".format(key, value)
                    for key, value in locals().items()
                    if key not in ("self", "url", "_[1]")
                ],
            )

        url = fixurl(url, unquote=True)  #: Recheck in 0.6.x

        if req is False:
            req = get_request()

        elif not req:
            req = self.req

        # TODO: Move to network in 0.6.x
        if isinstance(cookies, list):
            set_cookies(req.cj, cookies)

        # NOTE: req can be a HTTPRequest or a Browser object
        http_req = self.req.http if hasattr(self.req, "http") else self.req

        # TODO: Move to network in 0.6.x
        if not redirect:
            http_req.c.setopt(pycurl.FOLLOWLOCATION, 0)

        elif type(redirect) is int:
            http_req.c.setopt(pycurl.MAXREDIRS, redirect)

        # TODO: Move to network in 0.6.x
        if isinstance(ref, str):
            req.last_url = ref

        html = req.load(
            url,
            get,
            post,
            bool(ref),
            bool(cookies),
            just_header,
            multipart,
            decode is True,
        )

        # TODO: Move to network in 0.6.x
        if not redirect:
            # NOTE: req can be a HTTPRequest or a Browser object
            http_req.c.setopt(pycurl.FOLLOWLOCATION, 1)

        elif type(redirect) is int:
            maxredirs = (
                self.pyload.api.get_config_value(
                    "UserAgentSwitcher", "maxredirs", "plugin"
                )
                or 5
            )
            # NOTE: req can be a HTTPRequest or a Browser object
            http_req.c.setopt(pycurl.MAXREDIRS, maxredirs)

        # TODO: Move to network in 0.6.x
        if decode:
            html = purge.unescape(html)

        self.last_html = html

        if self.pyload.debug:
            self.dump_html()

        # TODO: Move to network in 0.6.x
        header = {"code": req.code, "url": req.last_effective_url}
        header.update(parse_html_header(http_req.response_header))

        self.last_header = header

        if just_header:
            return header
        else:
            return html

    def upload(
        self,
        path,
        url,
        get={},
        ref=True,
        cookies=True,
        just_header=False,
        decode=True,
        redirect=True,
        req=None,
    ):
        # TODO: This should really go to HTTPRequest.py
        """
        Uploads a file at url and returns response content.

        :param url:
        :param get:
        :param ref:
        :param cookies:
        :param just_header: If True only the header will be retrieved and returned as dict
        :param decode: Wether to decode the output according to http header, should be True in most cases
        :return: Response content
        """
        if self.pyload.debug:
            self.log_debug(
                "UPLOAD URL " + url,
                *[
                    "{}={}".format(key, value)
                    for key, value in locals().items()
                    if key not in ("self", "url", "_[1]")
                ],
            )

        with open(os.fsencode(path), mode="rb") as fp:
            url = fixurl(url, unquote=True)  #: Recheck in 0.6.x

            if req is False:
                req = get_request()

            elif not req:
                req = self.req

            if isinstance(cookies, list):
                set_cookies(req.cj, cookies)

            # NOTE: req can be a HTTPRequest or a Browser object
            http_req = req.http if hasattr(req, "http") else req

            if not redirect:
                http_req.c.setopt(pycurl.FOLLOWLOCATION, 0)

            elif isinstance(redirect, int):
                http_req.c.setopt(pycurl.MAXREDIRS, redirect)

            if isinstance(ref, str):
                http_req.last_url = ref

            http_req.set_request_context(url, get, {}, bool(ref), bool(cookies), False)
            http_req.c.setopt(pycurl.HTTPHEADER, http_req.request_headers)
            http_req.response_header = b""

            http_req.c.setopt(pycurl.UPLOAD, 1)
            http_req.c.setopt(pycurl.READFUNCTION, fp.read)
            http_req.c.setopt(pycurl.INFILESIZE, os.path.getsize(path))

            if just_header:
                http_req.c.setopt(pycurl.FOLLOWLOCATION, 0)
                http_req.c.setopt(pycurl.NOBODY, 1)
                http_req.c.perform()

                http_req.c.setopt(pycurl.FOLLOWLOCATION, 1)
                http_req.c.setopt(pycurl.NOBODY, 0)

            else:
                http_req.c.perform()

            http_req.c.setopt(pycurl.UPLOAD, 0)
            http_req.c.setopt(pycurl.INFILESIZE, 0)

            http_req.c.setopt(pycurl.POSTFIELDS, "")
            http_req.last_effective_url = http_req.c.getinfo(pycurl.EFFECTIVE_URL)

            http_req.add_cookies()

            http_req.code = http_req.verify_header()

            html = http_req.response_header if just_header else http_req.get_response()

            http_req.rep.close()
            http_req.rep = None

            if decode is True:
                html = http_req.decode_response(html)

            if not redirect:
                http_req.c.setopt(pycurl.FOLLOWLOCATION, 1)

            elif isinstance(redirect, int):
                maxredirs = (
                    self.pyload.api.get_config_value(
                        "UserAgentSwitcher", "maxredirs", "plugin"
                    )
                    or 5
                )
                # NOTE: req can be a HTTPRequest or a Browser object
                http_req.c.setopt(pycurl.MAXREDIRS, maxredirs)

            if decode:
                html = purge.unescape(html)

            self.last_html = html

            if self.pyload.debug:
                self.dump_html()

            # TODO: Move to network in 0.6.x
            header = {"code": req.code, "url": req.last_effective_url}
            # NOTE: req can be a HTTPRequest or a Browser object
            header.update(parse_html_header(http_req.response_header))

            self.last_header = header

            if just_header:
                return header
            else:
                return html

    def dump_html(self):
        frame = inspect.currentframe()

        try:
            framefile = os.path.join(
                self.pyload.tempdir,
                self.classname,
                "{}_line{}.dump.html".format(
                    frame.f_back.f_code.co_name, frame.f_back.f_lineno
                ),
            )

            os.makedirs(os.path.dirname(framefile), exist_ok=True)

            is_bytes = isinstance(self.last_html, (bytes, bytearray))
            with open(framefile, mode="wb" if is_bytes else "w", encoding=None if is_bytes else "utf-8") as fp:
                fp.write(self.last_html)

        except IOError as exc:
            self.log_error(exc)

        finally:
            del frame  #: Delete the frame or it won't be cleaned

    def clean(self):
        """
        Remove references.
        """
        try:
            # self.req.clear_cookies()
            self.req.close()

        except AttributeError:
            pass

        else:
            self.req = None
