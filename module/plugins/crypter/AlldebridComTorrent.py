# -*- coding: utf-8 -*-

import os
import time
import urllib

from ..internal.Crypter import Crypter
from ..internal.misc import exists, json, safejoin

try:
    from module.network.HTTPRequest import FormFile
except ImportError:
    pass



class AlldebridComTorrent(Crypter):
    __name__ = "AlldebridComTorrent"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    #_pattern__ = r'(?:file|https?)://.+\.torrent|magnet:\?.+'
    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("del_finished", "bool", "Delete downloaded torrents from the server", True)]

    __description__ = """Alldebrid.com torrents crypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    # See https://docs.alldebrid.com/
    API_URL = "https://api.alldebrid.com/v4/"

    def api_response(self, method, get={}, post={}, multipart=False):
        get.update({'agent': "pyLoad",
                    'version': self.pyload.version})
        json_data = json.loads(self.load(self.API_URL + method, get=get, post=post, multipart=multipart))
        if json_data['status'] == "success":
            return json_data['data']
        else:
            return json_data

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
                torrent_filename = safejoin("tmp", "tmp_%s.torrent" % self.pyfile.package().name) #: `tmp_` files are deleted automatically
                with open(torrent_filename, "wb") as f:
                    f.write(torrent_content)

            else:
                #: URL is local torrent file (uploaded container)
                torrent_filename = urllib.url2pathname(self.pyfile.url[7:]).encode('latin1').decode('utf8') #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(_("Torrent file does not exist"))

            #: Check if the torrent file path is inside pyLoad's config directory
            if os.path.abspath(torrent_filename).startswith(os.path.abspath(os.getcwd()) + os.sep):
                try:
                    #: send the torrent content to the server
                    api_data = self.api_response("magnet/upload/file",
                                                 get={'apikey': self.api_token},
                                                 post={'files[]': FormFile(torrent_filename, mimetype="application/x-bittorrent")},
                                                 multipart=True)
                except NameError:
                    self.fail(_("Posting file attachments is not supported by HTTPRequest, please update your pyLoad installation"))

                if api_data.get("error", False):
                    self.fail("%s (code: %s)" % (api_data['error']['message'], api_data['error']['code']))

                if api_data['files'][0].get('error', False):
                    self.fail("%s (code: %s)" % (api_data['files'][0]['error']['message'], api_data['files'][0]['error']['code']))

                torrent_id = api_data['files'][0]['id']

            else:
                self.fail(_("Illegal URL")) #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_response("magnet/upload",
                                         get={'apikey': self.api_token,
                                              'magnets[]': self.pyfile.url})

            if api_data.get("error", False):
                self.fail("%s (code: %s)" % (api_data['error']['message'], api_data['error']['code']))

            if api_data['magnets'][0].get('error', False):
                self.fail("%s (code: %s)" % (api_data['magnets'][0]['error']['message'], api_data['magnets'][0]['error']['code']))

            torrent_id = api_data['magnets'][0]['id']

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        prev_status = -1
        while True:
            torrent_info = self.api_response("magnet/status",
                                             get={'apikey': self.api_token,
                                                  'id': torrent_id})

            if torrent_info.get("error", False):
                self.fail("%s (code: %s)" % (torrent_info['error']['message'], torrent_info['error']['code']))

            status_code = torrent_info['magnets']['statusCode']
            torrent_size = torrent_info['magnets']['size']
            if status_code > 4:
                self.fail("%s (code: %s)" % (torrent_info["magnets"]['status'], status_code))

            if status_code != prev_status:
                if status_code in (0, 1):
                    self.pyfile.name = torrent_info['magnets']['filename']
                    self.pyfile.size = torrent_size

                elif status_code in (2, 3):
                    self.pyfile.setProgress(100)
                    self.pyfile.setCustomStatus("postprocessing")

            if status_code == 1:
                if torrent_size > 0:
                    self.pyfile.size = torrent_size
                    progress = int(100 * torrent_info['magnets']['downloaded'] / torrent_size)
                    self.pyfile.setProgress(progress)

            elif status_code == 4:
                self.pyfile.setProgress(100)
                break

            self.sleep(5)
            prev_status = status_code

        return [_l['link'] for _l in torrent_info['magnets']['links']]

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """

        api_data = self.api_response("magnet/delete",
                                     get={'apikey': self.api_token,
                                          'id': torrent_id})

        if api_data.get("error", False):
            self.log_warning("%s (code: %s)" % (api_data['error']['message'], api_data['error']['code']))

    def decrypt(self, pyfile):
        if 'AlldebridCom' not in self.pyload.accountManager.plugins:
            self.fail(_("This plugin requires an active Alldebrid.com account"))

        account_plugin = self.pyload.accountManager.getAccountPlugin("AlldebridCom")
        if len(account_plugin.accounts) == 0:
            self.fail(_("This plugin requires an active Alldebrid.com account"))

        self.api_token = account_plugin.accounts[account_plugin.accounts.keys()[0]]["password"]

        torrent_id = self.send_request_to_server()
        torrent_urls = self.wait_for_server_dl(torrent_id)

        self.packages = [(pyfile.package().name, torrent_urls, pyfile.package().name)]

        if self.config.get("del_finished"):
            self.delete_torrent_from_server(torrent_id)
