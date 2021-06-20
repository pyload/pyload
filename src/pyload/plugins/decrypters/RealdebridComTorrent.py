# -*- coding: utf-8 -*-

import fnmatch
import os
import time
import urllib.request
import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_decrypter import SimpleDecrypter
from ..helpers import exists
from pyload.core.utils.old import safejoin
from pyload.core.utils.purge import uniquify

class RealdebridComTorrent(SimpleDecrypter):
    __name__ = "RealdebridComTorrent"
    __type__ = "decrypter"
    __version__ = "0.14"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("enabled", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("include_filter", "str",
                   "File types to include (e.g. *.iso;*.zip, leave empty to select none)",
                   "*.*"),
                  ("exclude_filter", "str",
                   "File types to exclude (e.g. *.exe;advertisement.txt, leave empty to select none)",
                   ""),
                  ("del_finished", "bool", "Delete downloaded torrents from the server", True)]

    __description__ = """Realdebrid.com torrents decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    # See https://api.real-debrid.com/
    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_request(self, method, get={}, post={}):
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))

        for _i in range(2):
            try:
                json_data = self.load(self.API_URL + method, get=get, post=post)

            except BadHeader as e:
                json_data = e.content

            res = json.loads(json_data) if len(json_data) > 0 else {}

            if "error_code" in res:
                if res["error_code"] == 8:  #: token expired, refresh the token and retry
                    self.account.relogin()
                    if not self.account.info["login"]["valid"]:
                        return res

                    else:
                        self.api_token = self.account.accounts[list(self.account.accounts.keys())[0]]["api_token"]
                        get["auth_token"] = self.api_token
                        continue

                else:
                    error_msg = res["error"]
                    self.fail(error_msg)

            return res

        else:
            self.fail(self._("Refresh token has failed"))

    def sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def exit_error(self, msg):
        if self.tmp_file:
            os.remove(self.tmp_file)

        self.fail(msg)

    def send_request_to_server(self):
        """ Send torrent/magnet to the server """

        if self.pyfile.url.endswith(".torrent"):
            #: torrent URL
            if self.pyfile.url.startswith("http"):
                #: remote URL, download the torrent to tmp directory
                torrent_content = self.load(self.pyfile.url, decode=False)
                torrent_filename = safejoin(self.pyload.tempdir, "tmp_{}.torrent".format(self.pyfile.package().name))
                with open(torrent_filename, "wb") as f:
                    f.write(torrent_content)

            else:
                #: URL is local torrent file (uploaded container)
                torrent_filename = urllib.request.url2pathname(self.pyfile.url[7:])  #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(self._("Torrent file does not exist"))

            self.tmp_file = torrent_filename

            #: Check if the torrent file path is inside pyLoad's temp directory
            if os.path.abspath(torrent_filename).startswith(self.pyload.tempdir + os.sep):
                for _i in range(2):
                    try:
                        #: send the torrent content to the server
                        json_data = self.upload(torrent_filename,
                                                self.API_URL + "/torrents/addTorrent",
                                                get={'auth_token': self.api_token})
                    except BadHeader as exc:
                        json_data = exc.content

                    api_data = json.loads(json_data) if len(json_data) > 0 else {}

                    if "error_code" in api_data:
                        if api_data["error_code"] == 8:  #: token expired, refresh the token and retry
                            self.account.relogin()
                            if not self.account.info["login"]["valid"]:
                                self.exit_error(_("Token refresh has failed"))

                            else:
                                self.api_token = self.account.accounts[list(self.account.accounts.keys())[0]]["api_token"]

                        else:
                            error_msg = api_data["error"]
                            self.exit_error(error_msg)

                    else:
                        break

                else:
                    self.exit_error(self._("Token refresh has failed"))

            else:
                self.exit_error(self._("Illegal URL"))  #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_request("/torrents/addMagnet",
                                          get={"auth_token": self.api_token},
                                          post={"magnet": self.pyfile.url})

        torrent_id = api_data["id"]

        torrent_info = self.api_request("/torrents/info/" + torrent_id,
                                         get={'auth_token': self.api_token})

        if "error" in torrent_info:
            self.exit_error("{} (code: {})".format(torrent_info["error"], torrent_info.get("error_code", -1)))

        #: Filter and select files for downloading
        exclude_filters = self.config.get("exclude_filter").split(';')
        excluded_ids = []
        for _filter in exclude_filters:
            excluded_ids.extend([_file["id"] for _file in torrent_info["files"]
                                 if fnmatch.fnmatch(os.path.basename(_file["path"]), _filter)])

        excluded_ids = uniquify(excluded_ids)

        include_filters = self.config.get("include_filter").split(";")
        included_ids = []
        for _filter in include_filters:
            included_ids.extend([_file["id"] for _file in torrent_info["files"]
                                 if fnmatch.fnmatch(os.path.basename(_file["path"]), _filter)])

        included_ids = uniquify(included_ids)

        selected_ids = ",".join([str(_id) for _id in included_ids
                                 if _id not in excluded_ids])
        self.api_request("/torrents/selectFiles/" + torrent_id,
                          get={"auth_token": self.api_token},
                          post={"files": selected_ids})

        if self.tmp_file:
            os.remove(self.tmp_file)

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        torrent_info = self.api_request("/torrents/info/" + torrent_id,
                                         get={"auth_token": self.api_token})

        if "error" in torrent_info:
            self.fail("{} (code: {})".format(torrent_info["error"], torrent_info.get("error_code", -1)))

        self.pyfile.name = torrent_info["original_filename"]
        self.pyfile.size = torrent_info["original_bytes"]

        self.pyfile.set_custom_status("torrent")
        self.pyfile.set_progress(0)

        while torrent_info["status"] != "downloaded" or torrent_info["progress"] != 100:
            progress = int(torrent_info["progress"])
            self.pyfile.set_progress(progress)

            self.sleep(5)

            torrent_info = self.api_request("/torrents/info/" + torrent_id,
                                             get={"auth_token": self.api_token})
            if "error" in torrent_info:
                self.fail("{} (code: {})".format(torrent_info["error"], torrent_info.get("error_code", -1)))

        self.pyfile.set_progress(100)

        return torrent_info["links"]

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """
        url = "{}/torrents/delete/{}?auth_token={}".format(self.API_URL, torrent_id, self.api_token)
        self.log_debug("DELETE URL {}".format(url))
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
        c.setopt(pycurl.HTTPHEADER, ["Accept: */*",
                                     "Accept-Language: en-US,en",
                                     "Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                                     "Connection: keep-alive",
                                     "Keep-Alive: 300",
                                     "Expect:"])
        c.setopt(pycurl.CUSTOMREQUEST, "DELETE")
        c.perform()
        code = c.getinfo(pycurl.RESPONSE_CODE)
        c.close()

        return code

    def decrypt(self, pyfile):
        self.tmp_file = None
        torrent_id = 0
        if "RealdebridCom" not in self.pyload.account_manager.plugins:
            self.fail(self._("This plugin requires an active Realdebrid.com account"))

        self.account = self.pyload.account_manager.get_account_plugin("RealdebridCom")
        if len(self.account.accounts) == 0:
            self.fail(self._("This plugin requires an active Realdebrid.com account"))

        self.api_token = self.account.accounts[list(self.account.accounts.keys())[0]]["api_token"]

        try:
            torrent_id = self.send_request_to_server()
            torrent_urls = self.wait_for_server_dl(torrent_id)

            self.packages = [(pyfile.package().name, torrent_urls, pyfile.package().name)]

        finally:
            if torrent_id and self.config.get("del_finished"):
                self.delete_torrent_from_server(torrent_id)
