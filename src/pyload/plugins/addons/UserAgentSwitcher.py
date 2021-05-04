# -*- coding: utf-8 -*-

import pycurl
from pyload.core.network.browser import Browser
from pyload.core.network.http.http_request import HTTPRequest

from ..base.addon import BaseAddon


class UserAgentSwitcher(BaseAddon):
    __name__ = "UserAgentSwitcher"
    __type__ = "addon"
    __version__ = "0.18"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("connecttimeout", "int", "Max timeout for link connection in seconds", 60),
        ("maxredirs", "int", "Maximum number of redirects to follow", 10),
        (
            "useragent",
            "str",
            "Custom user-agent string",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0",
        ),
    ]

    __description__ = """Custom user-agent"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def download_preparing(self, pyfile):
        if not isinstance(pyfile.plugin.req, HTTPRequest) and not isinstance(
            pyfile.plugin.req, Browser
        ):
            return

        connecttimeout = self.config.get("connecttimeout")
        maxredirs = self.config.get("maxredirs")
        useragent = self.config.get("useragent")

        if connecttimeout:
            self.log_debug(
                "Setting connection timeout to {} seconds".format(connecttimeout)
            )
            pyfile.plugin.req.http.c.setopt(pycurl.CONNECTTIMEOUT, connecttimeout)

        if maxredirs:
            self.log_debug(f"Setting maximum redirections to {maxredirs}")
            pyfile.plugin.req.http.c.setopt(pycurl.MAXREDIRS, maxredirs)

        if useragent:
            self.log_debug(f"Use custom user-agent string `{useragent}`")
            pyfile.plugin.req.http.c.setopt(pycurl.USERAGENT, useragent.encode())
