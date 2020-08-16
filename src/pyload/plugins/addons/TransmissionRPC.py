# -*- coding: utf-8 -*-

import json
import random
import re

import pycurl
from pyload.core.network.http.exceptions import BadHeader
from pyload.core.network.request_factory import get_request

from ..base.addon import BaseAddon


class TransmissionRPC(BaseAddon):
    __name__ = "TransmissionRPC"
    __type__ = "addon"
    __version__ = "0.19"
    __status__ = "testing"

    __pattern__ = r"https?://.+\.torrent|magnet:\?.+"
    __config__ = [
        ("enabled", "bool", "Activated", False),
        (
            "rpc_url",
            "str",
            "Transmission RPC URL",
            "http://127.0.0.1:9091/transmission/rpc",
        ),
    ]

    __description__ = (
        """Send torrent and magnet URLs to Transmission Bittorent daemon via RPC"""
    )
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    def init(self):
        self.event_map = {"links_added": "links_added"}

    def links_added(self, links, pid):
        _re_link = re.compile(self.__pattern__)
        urls = [link for link in links if _re_link.match(link)]
        for url in urls:
            self.log_debug(f"Sending link: {url}")
            self.send_to_transmission(url)
            links.remove(url)

    def send_to_transmission(self, url):
        transmission_rpc_url = self.config.get("rpc_url")
        client_request_id = self.classname + "".join(
            random.choice("0123456789ABCDEF") for _ in range(4)
        )
        req = get_request()

        try:
            response = self.load(
                transmission_rpc_url,
                post=json.dumps(
                    {
                        "arguments": {"filename": url},
                        "method": "torrent-add",
                        "tag": client_request_id,
                    }
                ),
                req=req,
            )

        except Exception as exc:
            if isinstance(exc, BadHeader) and exc.code == 409:
                headers = dict(
                    re.findall(r"(?P<name>.+?): (?P<value>.+?)\r?\n", req.header)
                )
                session_id = headers["X-Transmission-Session-Id"]
                req.c.setopt(
                    pycurl.HTTPHEADER, [f"X-Transmission-Session-Id: {session_id}"]
                )
                try:
                    response = self.load(
                        transmission_rpc_url,
                        post=json.dumps(
                            {
                                "arguments": {"filename": url},
                                "method": "torrent-add",
                                "tag": client_request_id,
                            }
                        ),
                        req=req,
                    )

                    res = json.loads(response)
                    if "result" in res:
                        self.log_debug(f"Result: {res['result']}")

                except Exception as exc:
                    self.log_error(exc)

            else:
                self.log_error(exc)
