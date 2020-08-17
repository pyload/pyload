# -*- coding: utf-8 -*-

import hashlib
import json
import time

import pycurl

from ..base.multi_downloader import MultiDownloader


def args(**kwargs):
    return kwargs


class DebridlinkFr(MultiDownloader):
    __name__ = "DebridlinkFr"
    __type__ = "downloader"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """Debrid-slink.fr multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://debrid-link.fr/api"

    def api_request(self, method, data=None, get={}, post={}):

        session = self.account.info["data"].get("session", None)
        if session:
            ts = str(int(time.time() - float(session["tsd"])))

            m = hashlib.sha1()
            data = ts + method + session["key"]
            m.update(data.encode())
            sign = m.hexdigest()

            self.req.http.c.setopt(
                pycurl.HTTPHEADER,
                [
                    "X-DL-TOKEN: " + session["token"],
                    "X-DL-SIGN: " + sign,
                    "X-DL-TS: " + ts,
                ],
            )

        json_data = self.load(self.API_URL + method, get=get, post=post)

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        res = self.api_request("/downloader/add", post=args(link=pyfile.url))

        if res["result"] == "OK":
            self.link = res["value"]["downloadLink"]
            pyfile.name = res["value"].get("filename", None) or pyfile.name
            self.resume_download = res["value"].get("resume") or self.resume_download
            self.chunk_limit = res["value"].get("chunk") or self.chunk_limit

        else:
            err_code = res["ERR"]
            if err_code == "fileNotFound":
                self.offline()

            else:
                err_message = {
                    "notLink": "Check the 'link' parameter (Empty or bad)",
                    "notDebrid": "Maybe the filehoster is down or the link is not online",
                    "badFileUrl": "The link format is not valid",
                    "hostNotValid": "The filehoster is not supported",
                    "notFreeHost": "This filehoster is not available for the free member",
                    "disabledHost": "The filehoster are disabled",
                    "noGetFilename": "Unable to retrieve the file name",
                    "maxLink": "Limitation of number links per day reached",
                    "maxLinkHost": "Limitation of number links per day for this host reached",
                }.get(err_code)

                self.fail(err_message or "Unknown error: `{}`".format(err_code))
