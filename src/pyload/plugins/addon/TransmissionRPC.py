# -*- coding: utf-8 -*-

import json
import random
import re
from builtins import range

import pycurl
from pyload.core.network.http_request import BadHeader
from pyload.core.network.request_factory import getRequest as get_request
from pyload.plugins.internal.addon import Addon


class TransmissionRPC(Addon):
    __name__ = "TransmissionRPC"
    __type__ = "addon"
    __version__ = "0.19"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r"https?://.+\.torrent|magnet:\?.+"
    __config__ = [
        ("activated", "bool", "Activated", False),
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
        self.event_map = {"linksAdded": "links_added"}

    def links_added(self, links, pid):
        _re_link = re.compile(self.__pattern__)
        urls = [link for link in links if _re_link.match(link)]
        for url in urls:
            self.log_debug("Sending link: {}".format(url))
            self.send_to_transmission(url)
            links.remove(url)

    def send_to_transmission(self, url):
        transmission_rpc_url = self.config.get("rpc_url")
        client_request_id = self.classname + "".join(
            random.choice("0123456789ABCDEF") for _i in range(4)
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

        except Exception as e:
            if isinstance(e, BadHeader) and e.code == 409:
                headers = dict(
                    re.findall(r"(?P<name>.+?): (?P<value>.+?)\r?\n", req.header)
                )
                session_id = headers["X-Transmission-Session-Id"]
                req.c.setopt(
                    pycurl.HTTPHEADER, ["X-Transmission-Session-Id: {}" % session_id]
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
                        self.log_debug("Result: {}".format(res["result"]))

                except Exception as e:
                    self.log_error(e)

            else:
                self.log_error(e)
