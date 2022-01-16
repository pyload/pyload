# -*- coding: utf-8 -*-

import json
import re

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_downloader import SimpleDownloader


class WetransferCom(SimpleDownloader):
    __name__ = "WetransferCom"
    __type__ = "downloader"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?wetransfer.com/downloads/(?P<ID>[0-9a-f]+)/(?:(?P<RID>[0-9a-f]+)/)?(?P<SHASH>[0-9a-f]{6})$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Wetransfer.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [
        ("https?://(?:www\.)?wetransfer.com/", "https://wetransfer.com/")
    ]
    DIRECT_LINK = False

    API_URL = "https://wetransfer.com/api/v4/"

    def api_request(self, method, file_id, **kwargs):
        self.req.http.c.setopt(
            pycurl.HTTPHEADER,
            ["X-Requested-With: XMLHttpRequest", "Content-Type: application/json"],
        )

        try:
            json_data = self.load(
                "%s%s/%s/%s" % (self.API_URL, "transfers", file_id, method),
                post=json.dumps(kwargs),
            )
        except BadHeader as ex:
            json_data = ex.content

        api_data = json.loads(json_data)

        return api_data

    def api_info(self, url):
        info = {}
        m = re.search(self.__pattern__, url)
        file_id = m.group("ID")
        recipient_id = m.group("RID")
        security_hash = m.group("SHASH")

        if recipient_id is not None:
            api_data = self.api_request(
                "prepare-download",
                file_id,
                security_hash=security_hash,
                recipient_id=recipient_id,
            )

        else:
            api_data = self.api_request(
                "prepare-download", file_id, security_hash=security_hash
            )

        if "message" in api_data:
            message = api_data['message']
            if message == "Transfer not found":
                info['status'] = 1
            else:
                info['error'] = message
                info['status'] = 8

        else:
            info["status"] = 2 if api_data["state"] == "downloadable" else 1
            info["name"] = api_data["recommended_filename"]
            info["size"] = api_data["size"]

        return info

    def setup(self):
        self.multiDL = True
        self.chunk_limit = -1
        self.resume_download = True

    def handle_free(self, pyfile):
        file_id = self.info["pattern"]["ID"]
        recipient_id = self.info["pattern"]["RID"]
        security_hash = self.info["pattern"]["SHASH"]
        if recipient_id is not None:
            api_data = self.api_request(
                "download",
                file_id,
                intent="entire_transfer",
                security_hash=security_hash,
                recipient_id=recipient_id,
            )

        else:
            api_data = self.api_request(
                "download",
                file_id,
                intent="entire_transfer",
                security_hash=security_hash,
            )

        if "message" in api_data:
            self.fail(api_data["message"])

        self.link = api_data.get("direct_link")
