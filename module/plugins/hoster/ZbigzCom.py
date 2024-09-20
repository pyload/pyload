# -*- coding: utf-8 -*-

import os
import time
import urllib
import urlparse

from ..internal.Hoster import Hoster
from ..internal.misc import json, safejoin

try:
    from module.network.HTTPRequest import FormFile
except ImportError:
    pass



class ZbigzCom(Hoster):
    __name__ = "ZbigzCom"
    __type__ = "hoster"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", False)]

    __description__ = """Zbigz.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    API_URL = "https://api.zbigz.com/v1/"

    def load_json(self, url, **kwargs):
        json_data = self.load(url, **kwargs)
        return json.loads(json_data)

    def api_call(self, method, **kwargs):
        return self.load_json(self.API_URL + method, **kwargs)

    def sleep(self, sec):
        for _ in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def exit_error(self, msg):
        if self.tmp_file:
            os.remove(self.tmp_file)

        self.fail(msg)

    def send_request_to_server(self):
        """ Send torrent/magnet to the server """

        if self.pyfile.url.startswith("magnet:"):
            #: magnet URL, send it to the server
            api_data = self.api_call(
                "torrent/add",
                post={'url': self.pyfile.url},
                multipart=True
            )

        else:
            #: torrent URL
            if self.pyfile.url.startswith("http"):
                #: remote URL, download the torrent to tmp directory
                torrent_content = self.load(self.pyfile.url, decode=False)
                torrent_filename = safejoin(self.pyload.tempdir, "tmp_{}.torrent".format(self.pyfile.package().name))
                with open(torrent_filename, "wb") as f:
                    f.write(torrent_content)

            else:
                #: URL is a local torrent file (uploaded container)
                torrent_filename = urllib.url2pathname(self.pyfile.url[7:])  #: trim the starting `file://`
                if not  os.path.exists(torrent_filename):
                    self.fail(_("Torrent file does not exist"))

            self.tmp_file = torrent_filename

            #: Check if the torrent file path is inside pyLoad's temp directory
            if os.path.abspath(torrent_filename).startswith(self.pyload.tempdir + os.sep):
                #: send the torrent content to the server
                api_data = self.api_call(
                    "torrent/add",
                    post={'file': FormFile(torrent_filename, mimetype="application/octet-stream")},
                    multipart=True
                )

            else:
                self.fail(_("Illegal URL"))  #: We don't allow files outside pyLoad's temp directory

        if api_data['error']:
            self.fail(api_data['message'])

        api_data = self.api_call("storage/list")
        if api_data['error']:
            self.fail(api_data['error_msg'])

        torrent_id = api_data["0"]["hash"]
        server = api_data["0"]["server"]

        if self.tmp_file:
            os.remove(self.tmp_file)
            self.tmp_file = None

        return torrent_id, server

    def wait_for_server_dl(self, torrent_id, server):
        """ Show progress while the server does the download """

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        while True:
            api_data = self.load_json(
                "https://%s/gate/status" % server,
                get={"hash": torrent_id}
            )

            if api_data["error"] == 404 and api_data["result"] == "not found +init":
                pass

            elif api_data["error"]:
                self.exit_error(api_data["result"])

            if api_data.get("has_metadata", False):
                self.pyfile.name = api_data["name"]
                self.pyfile.size = api_data["size"]
                break

            self.sleep(5)

        while True:
            api_data = self.load_json(
                "https://%s/gate/status" % server,
                get={"hash": torrent_id}
            )
            if api_data["error"]:
                self.exit_error(api_data["result"])

            progress = api_data["progress"]
            self.pyfile.setProgress(progress)
            if progress >= 100:
                break

            self.sleep(5)

        self.pyfile.setProgress(100)

    def download_from_server(self, torrent_id, server):
        api_data = self.api_call("storage/download/%s" % torrent_id)
        if api_data['error']:
            self.fail(api_data['error_msg'])

        if "state" in api_data:
            zip_status_url = urlparse.urljoin("https://", api_data["state"])
            self.pyfile.setCustomStatus("zipping")
            self.pyfile.setProgress(0)

            while True:
                zip_status = self.load_json(zip_status_url)
                progress = zip_status["proc"]
                self.pyfile.setProgress(progress)
                if progress >= 100:
                    break

                self.sleep(2)

            self.pyfile.setProgress(100)

        download_url = api_data["link"]
        self.download(download_url)

    def process(self, pyfile):
        self.tmp_file = None
        torrent_id, server = self.send_request_to_server()
        self.wait_for_server_dl(torrent_id, server)
        self.download_from_server(torrent_id, server)

        if self.tmp_file:
            os.remove(self.tmp_file)
