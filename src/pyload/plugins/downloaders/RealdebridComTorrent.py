# -*- coding: utf-8 -*-

import json
import os
import time
import urllib.request

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.downloader import BaseDownloader
from ..helpers import exists


class RealdebridComTorrent(BaseDownloader):
    __name__ = "RealdebridComTorrent"
    __type__ = "downloader"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r"(?:file|https?)://.+\.torrent|magnet:\?.+"
    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("del_finished", "bool", "Delete downloaded torrents from the server", True),
    ]

    __description__ = """Realdebrid.com torrents downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_response(self, namespace, get={}, post={}):
        try:
            json_data = self.load(self.API_URL + namespace, get=get, post=post)

            return json.loads(json_data) if len(json_data) > 0 else {}

        except BadHeader as exc:
            error_msg = json.loads(exc.content)["error"]
            if exc.code == 400:
                self.fail(error_msg)
            elif exc.code == 401:
                self.fail(self._("Bad token (expired, invalid)"))
            elif exc.code == 403:
                self.fail(self._("Permission denied (account locked, not premium)"))
            elif exc.code == 503:
                self.fail(self._("Service unavailable - {}").format(error_msg))

    def setup(self):
        self.resume_download = True
        self.multi_dl = True
        self.limit_dl = 25

        self.premium = True
        self.no_fallback = True

    def sleep(self, sec):
        for _ in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def send_request_to_server(self):
        """
        Send torrent/magnet to the server.
        """
        if self.pyfile.url.endswith(".torrent"):
            #: torrent URL
            if self.pyfile.url.startswith("http"):
                #: remote URL, download the torrent to tmp directory
                torrent_content = self.load(self.pyfile.url, decode=False)
                torrent_filename = os.path.join(
                    self.pyload.tempdir,
                    "tmp_{}.torrent".format(self.pyfile.package().name),
                )  #: `tmp_` files are deleted automatically
                with open(torrent_filename, mode="wb") as fp:
                    fp.write(torrent_content)
            else:
                #: URL is local torrent file (uploaded container)
                torrent_filename = urllib.request.url2pathname(
                    self.pyfile.url[7:]
                )  #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(self._("File does not exists"))

            #: Check if the torrent file path is inside pyLoad's config directory
            if os.path.realpath(torrent_filename).startswith(
                os.path.realpath(os.getcwd()) + os.sep
            ):
                try:
                    #: send the torrent content to the server
                    api_data = json.loads(
                        self.upload(
                            torrent_filename,
                            self.API_URL + "/torrents/addTorrent",
                            get={"auth_token": self.api_token},
                        )
                    )
                except BadHeader as exc:
                    error_msg = json.loads(exc.content)["error"]
                    if exc.code == 400:
                        self.fail(error_msg)
                    elif exc.code == 401:
                        self.fail(self._("Bad token (expired, invalid)"))
                    elif exc.code == 403:
                        self.fail(
                            self._("Permission denied (account locked, not premium)")
                        )
                    elif exc.code == 503:
                        self.fail(self._("Service unavailable - {}").format(error_msg))

            else:
                # : We don't allow files outside pyLoad's config directory
                self.fail(self._("Illegal URL"))

        else:
            #: magnet URL, send to the server
            api_data = self.api_response(
                "/torrents/addMagnet",
                get={"auth_token": self.api_token},
                post={"magnet": self.pyfile.url},
            )

        #: Select all the files for downloading
        torrent_id = api_data["id"]
        self.api_response(
            "/torrents/selectFiles/" + torrent_id,
            get={"auth_token": self.api_token},
            post={"files": "all"},
        )

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """
        Show progress while the server does the download.
        """
        torrent_info = self.api_response(
            "/torrents/info/" + torrent_id, get={"auth_token": self.api_token}
        )

        self.pyfile.name = torrent_info["original_filename"]
        self.pyfile.size = torrent_info["original_bytes"]

        self.pyfile.set_custom_status("torrent")
        self.pyfile.set_progress(0)

        while torrent_info["status"] != "downloaded" or torrent_info["progress"] != 100:
            progress = int(torrent_info["progress"])
            self.pyfile.set_progress(progress)

            self.sleep(5)

            torrent_info = self.api_response(
                "/torrents/info/" + torrent_id, get={"auth_token": self.api_token}
            )

        self.pyfile.set_progress(100)

        return torrent_info["links"][0]

    def download_torrent(self, torrent_url):
        """
        Download the file after the server finished downloading the torrent.
        """
        api_data = self.api_response(
            "/unrestrict/link",
            get={"auth_token": self.api_token},
            post={"link": torrent_url},
        )
        if "error" in api_data:
            self.fail("{} (code: {})".format(api_data["error"], api_data["error_code"]))

        else:
            self.pyfile.name = api_data["filename"]
            self.pyfile.size = api_data["filesize"]
            self.chunk_limit = (
                api_data["chunks"] if api_data["filesize"] < 2 << 10 ** 3 else 1
            )
            self.download(api_data["download"])

    def delete_torrent_from_server(self, torrent_id):
        """
        Remove the torrent from the server.
        """
        with pycurl.Curl() as c:
            c.setopt(
                pycurl.URL,
                "{}/torrents/delete/{}?auth_token={}".format(
                    self.API_URL, torrent_id, self.api_token
                ),
            )
            c.setopt(pycurl.SSL_VERIFYPEER, 0)
            c.setopt(
                pycurl.USERAGENT,
                self.config.get("useragent", plugin="UserAgentSwitcher"),
            )
            c.setopt(
                pycurl.HTTPHEADER,
                [
                    "Accept: */*",
                    "Accept-Language: en-US,en",
                    "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                    "Connection: keep-alive",
                    "Keep-Alive: 300",
                    "Expect:",
                ],
            )
            c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
            c.perform()
            code = c.getinfo(pycurl.RESPONSE_CODE)
        return code

    def process(self, pyfile):
        if "RealdebridCom" not in self.pyload.accountManager.plugins:
            self.fail(self._("This plugin requires an active Realdebrid.com account"))

        account_plugin = self.pyload.accountManager.getAccountPlugin("RealdebridCom")
        if len(account_plugin.accounts) == 0:
            self.fail(self._("This plugin requires an active Realdebrid.com account"))

        self.api_token = account_plugin.accounts[
            list(account_plugin.accounts.keys())[0]
        ]["password"]

        torrent_id = self.send_request_to_server()
        torrent_url = self.wait_for_server_dl(torrent_id)
        self.download_torrent(torrent_url)
        if self.config.get("del_finished"):
            self.delete_torrent_from_server(torrent_id)
