# -*- coding: utf-8 -*-

import os
import pycurl
import time
import urllib

from module.network.HTTPRequest import BadHeader

from ..internal.Hoster import Hoster
from ..internal.misc import exists, json


class RealdebridComTorrent(Hoster):
    __name__ = "RealdebridComTorrent"
    __type__ = "hoster"
    __version__ = "0.03"
    __status__ = "testing"

    __pattern__ = r'(?:file|https?)://.+\.torrent|magnet:\?.+'
    __config__ = [("activated", "bool", "Activated", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("del_finished", "bool", "Delete downloaded torrents from the server", True)]

    __description__ = """Realdebrid.com torrents hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_response(self, namespace, get={}, post={}):
        try:
            json_data = self.load(self.API_URL + namespace, get=get, post=post)

            return json.loads(json_data) if len(json_data) > 0 else {}

        except BadHeader, e:
            error_msg = json.loads(e.content)['error']
            if e.code == 400:
                self.fail(error_msg)
            elif e.code == 401:
                self.fail(_("Bad token (expired, invalid)"))
            elif e.code == 403:
                self.fail(_("Permission denied (account locked, not premium)"))
            elif e.code == 503:
                self.fail(_("Service unavailable - %s") % error_msg)

    def setup(self):
        self.resume_download = True
        self.multiDL = True
        self.limitDL = 25

        self.premium = True
        self.no_fallback = True

    def sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)

    def send_request_to_server(self):
        """ Send torrent/magnet to the server """

        if self.pyfile.url.endswith(".torrent"):
            #: torrent URL
            if self.pyfile.url.startswith("http"):
                #: remote URL, download the torrent to tmp directory
                torrent_content = self.load(self.pyfile.url, decode=False)
                torrent_filename = os.path.join("tmp", "tmp_%s.torrent" % self.pyfile.package().name) #: `tmp_` files are deleted automatically
                with open(torrent_filename, "wb") as f:
                    f.write(torrent_content)

            else:
                #: URL is local torrent file (uploaded container)
                torrent_filename = urllib.url2pathname(self.pyfile.url[7:]) #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(_("File does not exists"))

            #: Check if the torrent file path is inside pyLoad's config directory
            if os.path.abspath(torrent_filename).startswith(os.path.abspath(os.getcwd()) + os.sep):
                try:
                    #: send the torrent content to the server
                    api_data = json.loads(self.upload(torrent_filename,
                                                      self.API_URL + "/torrents/addTorrent",
                                                      get={'auth_token': self.api_token}))
                except BadHeader, e:
                    error_msg = json.loads(e.content)['error']
                    if e.code == 400:
                        self.fail(error_msg)
                    elif e.code == 401:
                        self.fail(_("Bad token (expired, invalid)"))
                    elif e.code == 403:
                        self.fail(_("Permission denied (account locked, not premium)"))
                    elif e.code == 503:
                        self.fail(_("Service unavailable - %s") % error_msg)

            else:
                self.fail(_("Illegal URL")) #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_response("/torrents/addMagnet",
                                          get={'auth_token': self.api_token},
                                          post={'magnet': self.pyfile.url})

        torrent_id = api_data['id']

        #: Select all the files for downloading
        self.api_response("/torrents/selectFiles/" + torrent_id,
                          get={'auth_token': self.api_token},
                          post={'files': "all"})

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        torrent_info = self.api_response("/torrents/info/" + torrent_id,
                                         get={'auth_token': self.api_token})

        self.pyfile.name = torrent_info['original_filename']
        self.pyfile.size = torrent_info['original_bytes']

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        while torrent_info['status'] != 'downloaded' or torrent_info['progress'] != 100:
            progress = int(torrent_info['progress'])
            self.pyfile.setProgress(progress)

            self.sleep(5)

            torrent_info = self.api_response("/torrents/info/" + torrent_id,
                                             get={'auth_token': self.api_token})

        self.pyfile.setProgress(100)

        return torrent_info['links'][0]

    def download_torrent(self, torrent_url):
        """ Download the file after the server finished downloading the torrent """

        api_data = self.api_response("/unrestrict/link",
                                     get= {'auth_token': self.api_token},
                                     post={'link': torrent_url})
        if "error" in api_data:
            self.fail("%s (code: %s)" % (api_data["error"], api_data["error_code"]))

        else:
            self.pyfile.name = api_data['filename']
            self.pyfile.size = api_data['filesize']
            self.chunk_limit = api_data['chunks'] if api_data['filesize'] < 2 * 1024**3 else 1
            self.download(api_data['download'])

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """
        c = pycurl.Curl()
        c.setopt(pycurl.URL, "%s/torrents/delete/%s?auth_token=%s" % (self.API_URL, torrent_id, self.api_token))
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.USERAGENT, self.config.get("useragent", plugin="UserAgentSwitcher"))
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

    def process(self, pyfile):
        if 'RealdebridCom' not in self.pyload.accountManager.plugins:
            self.fail(_("This plugin requires an active Realdebrid.com account"))

        account_plugin = self.pyload.accountManager.getAccountPlugin("RealdebridCom")
        if len(account_plugin.accounts) == 0:
            self.fail(_("This plugin requires an active Realdebrid.com account"))

        self.api_token = account_plugin.accounts[account_plugin.accounts.keys()[0]]["password"]

        torrent_id = self.send_request_to_server()
        torrent_url = self.wait_for_server_dl(torrent_id)
        self.download_torrent(torrent_url)
        if self.config.get("del_finished"):
            self.delete_torrent_from_server(torrent_id)

