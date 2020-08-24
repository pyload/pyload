# -*- coding: utf-8 -*-

import re
import urlparse

from module.network.HTTPRequest import BadHeader

from ..base.downloader import BaseDownloader
from ..internal.misc import json


class ArteTv(BaseDownloader):
    __name__ = "ArteTv"
    __type__ = "downloader"
    __version__ = "0.1"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r"https://(?:www\.)?arte\.tv/.*/videos/(?P<ID>[-0-9A]+)"
    __config__ = [
        ("activated", "bool", "Activated", True),
        ("quality", "360p;720p", "Quality", "720p"),
        ("language", "german;french", "Language", "german"),
    ]

    __description__ = """Arte.tv hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    apiUrl = "0"
    videoElemName = "0"

    API_URL_DE = "https://api.arte.tv/api/player/v1/config/de/"
    API_URL_FR = "https://api.arte.tv/api/player/v1/config/fr/"

    def setup(self):
        if self.config.get("language") == "german":
            self.apiUrl = self.API_URL_DE

            if self.config.get("quality") == "360p":
                self.videoElemName = "HTTPS_HQ_1"
            else:
                self.videoElemName = "HTTPS_SQ_1"

        else:
            self.apiUrl = self.API_URL_FR

            if self.config.get("quality") == "360p":
                self.videoElemName = "HTTPS_HQ_2"
            else:
                self.videoElemName = "HTTPS_SQ_2"

    # Handles API JSON retrieval
    def api_response(self, cmd):

        try:
            json_data = json.loads(self.load("%s%s" % (self.apiUrl, cmd)))
            self.log_debug("API response: %s" % json_data)
            return json_data

        except BadHeader, e:
            try:
                json_data = json.loads(e.content)
                self.log_error(
                    "API Error: %s" % cmd,
                    json_data["error"]["message"],
                    "ID: %s" % self.info["pattern"]["ID"],
                    "Error code: %s" % e.code,
                )

            except ValueError:
                self.log_error(
                    "API Error: %s" % cmd,
                    e,
                    "ID: %s" % self.info["pattern"]["ID"],
                    "Error code: %s" % e.code,
                )
            return None

    def process(self, pyfile):

        videoID = self.info["pattern"]["ID"]
        json_data = self.api_response(videoID)

        # Check if valid json
        try:
            json_data["videoJsonPlayer"]["VSR"]

        except:
            self.fail("Invalid URL or video not available")

        # Get filename from XML and set it
        pyfile.name = json_data["videoJsonPlayer"]["VTI"] + " - arte.tv.mp4"

        # Get final download URL from JSON data
        finalurl = json_data["videoJsonPlayer"]["VSR"][self.videoElemName]["url"]

        self.download(finalurl)
