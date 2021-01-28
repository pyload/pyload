# -*- coding: utf-8 -*-

import fnmatch
import os
import time
import urllib

import pycurl
from module.network.HTTPRequest import BadHeader

from ..hoster.DebridlinkFr import error_description
from ..internal.Crypter import Crypter
from ..internal.misc import exists, json, safejoin, uniqify

try:
    from module.network.HTTPRequest import FormFile
except ImportError:
    pass


class DebridlinkFrTorrent(Crypter):
    __name__ = "DebridlinkFrTorrent"
    __type__ = "crypter"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("include_filter", "str", "File types to include (e.g. *.iso;*.zip, leave empty to select none)", "*.*"),
                  ("exclude_filter", "str", "File types to exclude (e.g. *.exe;advertisement.txt, leave empty to select none)", "")]

    __description__ = """"Debrid-link.fr torrents crypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    #: See https://debrid-link.fr/api_doc/v2
    API_URL = "https://debrid-link.fr/api/"

    def api_response(self, method, get={}, post={}):
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["Authorization: Bearer " + self.api_token])
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/%s" % self.pyload.version)
        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader, e:
            json_data = e.content

        return json.loads(json_data)

    def api_response_safe(self, method, get={}, post={}):
        for _i in range(2):
            api_data = self.api_response(method, get=get, post=post)

            if 'error' in api_data:
                if api_data['error'] == 'badToken':  #: token expired, refresh the token and retry
                    self.account.relogin()
                    if not self.account.info['login']['valid']:
                        return api_data

                    else:
                        self.api_token = self.account.accounts[self.account.accounts.keys()[0]]["api_token"]
                        continue

                else:
                    return api_data

            return api_data

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
                    api_data = json.loads(self.load("https://up1.debrid.link/seedbox",
                                                    post={'file': FormFile(torrent_filename, mimetype="application/x-bittorrent")},
                                                    multipart=True))
                    if api_data['result'] != "OK":
                        self.fail(api_data['ERR'])

                    api_data = self.api_response_safe("v2/seedbox/add",
                                                      post={'url': api_data['link'],
                                                            'wait': True,
                                                            'async': True})

                except NameError:
                    self.fail(_("Posting file attachments is not supported by HTTPRequest, please update your pyLoad installation"))
            else:
                self.fail(_("Illegal URL"))  #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_response_safe("v2/seedbox/add",
                                              post={'url': self.pyfile.url,
                                                    'wait': True,
                                                    'async': True})

        if not api_data['success']:
            self.fail("%s (code: %s)" % (api_data.get('error_description', error_description(api_data["error"])), api_data['error']))

        torrent_id = api_data['value']['id']

        self.pyfile.setCustomStatus("metadata")
        self.pyfile.setProgress(0)

        #: Get the file list of the torrent
        page = 0
        files = []
        while True:
            api_data = self.api_response_safe("v2/seedbox/list",
                                              get={'ids': torrent_id,
                                                   'page': page,
                                                   'perPage': 50})

            if not api_data['success']:
                self.fail("%s (code: %s)" % (api_data.get('error_description', error_description(api_data["error"])), api_data['error']))

            if api_data['value'][0]['status'] == 1:
                files.extend([{'id': _file['id'], 'name': _file['name'], 'size': _file['size'], 'url': _file['downloadUrl']}
                              for _file in api_data['value'][0]['files']])

                page = api_data['pagination']['next']
                if page == -1:
                    break
                else:
                    continue

            self.sleep(5)

        self.pyfile.name = api_data['value'][0]['name']

        #: Filter and select files for downloading
        exclude_filters = self.config.get('exclude_filter').split(';')
        excluded_ids = []
        for _filter in exclude_filters:
            excluded_ids.extend([_file['id'] for _file in files
                                 if fnmatch.fnmatch(_file['name'], _filter)])

        excluded_ids = uniqify(excluded_ids)

        include_filters = self.config.get('include_filter').split(';')
        included_ids = []
        for _filter in include_filters:
            included_ids.extend([_file['id'] for _file in files
                                 if fnmatch.fnmatch(_file['name'], _filter)])

        included_ids = uniqify(included_ids)

        selected_ids = [_id for _id in included_ids
                        if _id not in excluded_ids]

        unwanted_ids = [_file['id'] for _file in files
                        if _file['id'] not in selected_ids]

        self.pyfile.size = sum([_file['size'] for _file in files
                               if _file['id'] in selected_ids])

        api_data = self.api_response_safe("v2/seedbox/%s/config" % torrent_id,
                                          post={'files-unwanted': json.dumps(unwanted_ids)})

        if not api_data['success']:
            self.fail("%s (code: %s)" % (api_data.get('error_description', error_description(api_data["error"])), api_data['error']))

        return torrent_id, [_file['url'] for _file in files
                            if _file['id'] in selected_ids]

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        api_data = self.api_response_safe("v2/seedbox/activity",
                                         get={'ids': torrent_id})

        if not api_data['success']:
            self.fail("%s (code: %s)" % (api_data.get('error_description', api_data.get('error_description', error_description(api_data["error"]))), api_data['error']))

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        progress = int(api_data['value'][torrent_id]['downloadPercent'])
        while progress != 100:
            progress = int(api_data['value'][torrent_id]['downloadPercent'])
            self.pyfile.setProgress(progress)

            self.sleep(5)

            api_data = self.api_response_safe("v2/seedbox/activity",
                                              get={'ids': torrent_id})

            if not api_data['success']:
                self.fail("%s (code: %s)" % (api_data.get('error_description', api_data.get('error_description', error_description(api_data["error"]))), api_data['error']))

            if not api_data['value']:
                self.fail("Torrent deleted from server")

        self.pyfile.setProgress(100)

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """
        url = "%sv2/seedbox/%s/remove" % (self.API_URL, torrent_id)
        self.log_debug("DELETE URL %s" % url)
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.USERAGENT, "pyLoad/%s" % self.pyload.version)
        c.setopt(pycurl.HTTPHEADER, ["Authorization: Bearer " + self.api_token,
                                     "Accept: */*",
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
        if 'DebridlinkFr' not in self.pyload.accountManager.plugins:
            self.fail(_("This plugin requires an active Debrid-slink.fr account"))

        self.account = self.pyload.accountManager.getAccountPlugin("DebridlinkFr")
        if len(self.account.accounts) == 0:
            self.fail(_("This plugin requires an active Debrid-slink.fr account"))

        self.api_token = self.account.accounts[self.account.accounts.keys()[0]]["api_token"]

        torrent_id, torrent_urls = self.send_request_to_server()
        self.wait_for_server_dl(torrent_id)

        self.packages = [(pyfile.package().name, torrent_urls, pyfile.package().name)]
