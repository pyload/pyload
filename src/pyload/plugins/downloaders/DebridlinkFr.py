# -*- coding: utf-8 -*-

import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_downloader import MultiDownloader


def error_description(error_code):
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
        "notAddTorrent": "Unable to add the torrent, check url",
        "torrentTooBig": "The torrent is too big or have too many files",
        "maxTorrent": "Limitation of torrents per day reached",
    }.get(error_code)

    return err_message or "Unknown error: '{}'".format(error_code)


class DebridlinkFr(MultiDownloader):
    __name__ = "DebridlinkFr"
    __type__ = "downloader"
    __version__ = "0.07"
    __status__ = "testing"

    __pattern__ = r"https?://.*\.debrid\.link/.*"
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

    #: See https://debrid-link.fr/api_doc/v2
    API_URL = "https://debrid-link.fr/api/"

    def api_request(self, method, get={}, post={}):
        api_token = self.account.info["data"].get("api_token", None)
        if api_token:
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + api_token]
            )
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def handle_premium(self, pyfile):
        api_data = self.api_request("v2/downloader/add", post={"url": pyfile.url})

        if api_data["success"]:
            self.link = api_data["value"]["downloadUrl"]
            pyfile.name = api_data["value"].get("name", pyfile.name)
            self.resume_download = api_data["value"].get("resume", self.resume_download)
            self.chunk_limit = api_data["value"].get("chunk", self.chunk_limit)

        else:
            err_code = api_data["error"]
            if err_code == "fileNotFound":
                self.offline()

            else:
                self.fail(
                    api_data.get(
                        "error_description", error_description(api_data["error"])
                    )
                )
