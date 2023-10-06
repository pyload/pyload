# -*- coding: utf-8 -*-

import json
import re
import time

from ..base.multi_downloader import MultiDownloader


class AlldebridCom(MultiDownloader):
    __name__ = "AlldebridCom"
    __type__ = "downloader"
    __version__ = "0.66"
    __status__ = "testing"

    __pattern__ = r"https?://(?:\w+\.)?(?:alldebrid\.com|debrid\.it|alld\.io)/(?:dl|f)/[\w^_]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
        (
            "stream_quality",
            "Lowest;LD 144p;LD 240p;SD 380p;HQ 480p;HD 720p;HD 1080p;Highest",
            "Quality to download from stream hosters",
            "Highest",
        ),
    ]

    __description__ = """Alldebrid.com multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Andy Voigt", "spamsales@online.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    DISPOSITION = False
    URL_REPLACEMENTS = [
        (
            r"https?://(?:www\.)?mega(?:\.co)?\.nz/#N!(?P<ID>[\w^_]+)!(?P<KEY>[\w\-,=]+)###n=(?P<OWNER>[\w^_]+)",
            lambda m: "https://mega.nz/#!{}!{}~~{}".format(
                m.group("ID"), m.group("KEY"), m.group("OWNER")
            ),
        ),
        (
            r"https?://(?:www\.)?mega(?:\.co)?\.nz/.*",
            lambda m: m.group(0).replace("_", "/"),
        ),
    ]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/v4/"

    def api_request(self, method, get={}, post={}, multipart=False):
        get.update({"agent": "pyLoad", "version": self.pyload.version})
        json_data = json.loads(
            self.load(self.API_URL + method, get=get, post=post, multipart=multipart)
        )
        if json_data["status"] == "success":
            return json_data["data"]
        else:
            return json_data

    def sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        api_data = self.api_request(
            "link/unlock",
            get={
                "link": pyfile.url,
                "password": self.get_password(),
                "apikey": self.account.info["login"]["password"],
            },
        )

        if api_data.get("error", False):
            if api_data["error"]["code"] == "LINK_DOWN":
                self.offline()

            else:
                self.log_error(api_data["error"]["message"])
                self.temp_offline()

        else:
            if api_data["link"] == "" and "streams" in api_data:
                unlock_id = api_data["id"]
                streams = dict(
                    [
                        (
                            _s["quality"],
                            {
                                "ext": _s["ext"],
                                "filesize": _s["filesize"],
                                "id": _s["id"],
                            },
                        )
                        for _s in api_data["streams"]
                        if type(_s["quality"]) == int
                    ]
                )
                qualities = sorted(streams.keys())
                self.log_debug("AVAILABLE STREAMS: {}".format(qualities))
                desired_quality = self.config.get("stream_quality")
                if desired_quality == "Lowest":
                    chosen_quality = qualities[0]
                elif desired_quality == "Highest":
                    chosen_quality = qualities[-1]
                else:
                    desired_quality = int(re.search(r"\d+", desired_quality).group(0))
                    chosen_quality = min(qualities, key=lambda x: abs(x - desired_quality))
                self.log_debug("CHOSEN STREAM: {}".format(chosen_quality))

                stream_id = streams[chosen_quality]["id"]
                stream_name = (
                    api_data["filename"] + "." + streams[chosen_quality]["ext"]
                )
                stream_size = streams[chosen_quality]["filesize"]
                api_data = self.api_request(
                    "link/streaming",
                    get={
                        "apikey": self.account.info["login"]["password"],
                        "id": unlock_id,
                        "stream": stream_id,
                    },
                )
                if api_data.get("error", False):
                    self.log_error(api_data["error"]["message"])
                    self.temp_offline()

                delayed_id = api_data.get("delayed")
                if delayed_id:
                    pyfile.set_custom_status("delayed stream")
                    while True:
                        api_data = self.api_request(
                            "link/delayed",
                            get={
                                "apikey": self.account.info["login"]["password"],
                                "id": delayed_id,
                            },
                        )
                        if "link" in api_data:
                            pyfile.name = stream_name
                            pyfile.size = stream_size
                            self.chunk_limit = api_data.get("max_chunks", 16)
                            self.link = api_data["link"]
                            return

                        self.sleep(5)

            pyfile.name = api_data["filename"]
            pyfile.size = api_data["filesize"]
            self.chunk_limit = api_data.get("max_chunks", 16)
            self.link = api_data["link"]
