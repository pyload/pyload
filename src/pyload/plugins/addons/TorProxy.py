# -*- coding: utf-8 -*-

import os
import subprocess

from ..base.addon import BaseAddon, expose


class TorProxy(BaseAddon):
    __name__ = "TorProxy"
    __type__ = "addon"
    __version__ = "0.01"
    __status__ = "testing"

    # config is sorted by abc ...
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("f_host", "str", "Tor host", "127.0.0.1"),
        ("g_socks_port", "int", "Tor SocksPort", 9050),
    ]
    __description__ = ""
    __license__ = "MIT"
    __authors__ = []

    def download_preparing(self, pyfile):
        """a download was just queued and will be prepared now"""

        # FIXME use tor only if we must wait too long (1 hour or more)
        # similar to reconnect

        pyload_pid = 123 # TODO

        pyfile.proxy = dict(
            type="socks5",
            host=self.config.get("f_host"),
            port=self.config.get("g_socks_port"),
            # use curl socks5h to avoid dns leaks
            socks_resolve_dns=True,
            # proxy username specifies the tor identity
            username=f"pyload{pyload_pid}-file{pyfile.id}",
            password="",
        )
