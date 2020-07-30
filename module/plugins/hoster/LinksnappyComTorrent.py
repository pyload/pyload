# -*- coding: utf-8 -*-

import os
import time
import urllib

from ..internal.Hoster import Hoster
from ..internal.misc import exists, json, parse_size

try:
    from module.network.HTTPRequest import FormFile
except ImportError:
    pass



class LinksnappyComTorrent(Hoster):
    __name__ = "LinksnappyComTorrent"
    __type__ = "hoster"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("del_finished", "bool", "Delete downloaded torrents from the server", True)]

    __description__ = """Linksnappy.com torrents crypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    API_URL = "https://linksnappy.com/api/"

    def api_response(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method,
                                         get=kwargs))

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
                api_data = self.api_response("torrents/ADDURL", url=self.pyfile.url).items()[0][1]

                if api_data['status'] == "FAILED" and api_data['error'] != "This torrent already exists in your account":
                    self.fail(api_data['error'])

                torrent_id = api_data['torrentid']

            else:
                #: URL is local torrent file (uploaded container)
                torrent_filename = urllib.url2pathname(self.pyfile.url[7:]).encode('latin1').decode('utf8')  #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(_("Torrent file does not exist"))

                #: Check if the torrent file path is inside pyLoad's config directory
                if os.path.abspath(torrent_filename).startswith(os.path.abspath(os.getcwd()) + os.sep):
                        try:
                            #: send the torrent content to the server
                            api_data = self.load("https://linksnappy.com/includes/ajaxupload.php",
                                                 post={'torrents[]': FormFile(torrent_filename, mimetype="application/octet-stream")},
                                                 multipart=True)
                            api_data = json.loads(api_data).items()[0][1]

                        except NameError:
                            self.fail(_("Posting file attachments is not supported by HTTPRequest, please update your pyLoad installation"))

                        if api_data['error']:
                            self.fail(api_data['error'])

                        torrent_id = api_data['torrentid']

                else:
                    self.fail(_("Illegal URL")) #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_response("torrents/ADDMAGNET", magnetlinks=self.pyfile.url)

            if api_data['status'] != "OK":
                self.fail(api_data['error'])

            api_data = api_data['return'][0]

            if api_data['status'] != "OK" and api_data['error'] != "This torrent already exists in your account":
                self.fail(api_data['error'])

            torrent_id = api_data['torrentid']

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        api_data = self.api_response("torrents/STATUS", tid=torrent_id)
        if api_data['status'] != "OK":
            self.fail(api_data['error'])

        if api_data['return']['status'] == "ERROR":
            self.fail(api_data['return']['error'])

        self.pyfile.name = api_data['return']['name']

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        if api_data['return']['status'] != "FINISHED":
            api_data = self.api_response("torrents/START", tid=torrent_id)
            if api_data['status'] != "OK":
                if api_data['error'] == "Magnet URI processing in progress. Please wait.":
                    for _i in range(8):
                        self.sleep(3)
                        api_data = self.api_response("torrents/START", tid=torrent_id)
                        if api_data['status'] == "OK":
                            break
                    else:
                        self.fail(api_data['error'])

                elif api_data['error'] != "Already started.":
                    self.fail(api_data['error'])

            while True:
                api_data = self.api_response("torrents/STATUS", tid=torrent_id)
                if api_data['status'] != "OK":
                    self.fail(api_data['error'])

                if api_data['return']['status'] == "ERROR":
                    self.fail(api_data['return']['error'])

                torrent_size = api_data['return'].get('getSize')
                if torrent_size is not None and self.pyfile.size == 0:
                    self.pyfile.size = parse_size(torrent_size)

                progress = int(api_data['return']['percentDone'])
                self.pyfile.setProgress(progress)

                if api_data['return']['status'] == "FINISHED":
                    break

                self.sleep(2)

        self.pyfile.setProgress(100)

        self.sleep(1)

        self.pyfile.setCustomStatus("makezip")
        self.pyfile.setProgress(0)
        while True:
            api_data = self.api_response("torrents/GENZIP", torrentid=torrent_id)
            if api_data['status'] == "ERROR":
                self.fail(api_data['error'])

            elif api_data['status'] == "PENDING":
                self.sleep(2)

            else:
                break

        self.pyfile.setProgress(100)
        return api_data['return']

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """
        self.api_response("torrents/DELETETORRENT", tid=torrent_id, delFiles=1)

    def setup(self):
        self.multiDL = True
        self.resume_download = True
        self.chunk_limit = 1

        if 'LinksnappyCom' not in self.pyload.accountManager.plugins:
            self.fail(_("This plugin requires an active Linksnappy.com account"))

        self.account = self.pyload.accountManager.getAccountPlugin("LinksnappyCom")
        if len(self.account.accounts) == 0:
            self.fail(_("This plugin requires an active Linksnappy.com account"))

        self.load_account()

        #: Use the cookiejar of account plugin (for the logged on session cookie)
        cj = self.pyload.requestFactory.getCookieJar("LinksnappyCom", self.account.user)
        self.req.setCookieJar(cj)

    def process(self, pyfile):
        torrent_id = False
        try:
            torrent_id = self.send_request_to_server()
            torrent_url = self.wait_for_server_dl(torrent_id)

            self.pyfile.name = os.path.basename(torrent_url)
            self.download(torrent_url)

        finally:
            if torrent_id is not False and self.config.get("del_finished"):
                self.delete_torrent_from_server(torrent_id)
