# -*- coding: utf-8 -*-

import fnmatch
import os
import time
import urllib

import pycurl
from module.network.HTTPRequest import BadHeader

from ..internal.Crypter import Crypter
from ..internal.misc import exists, json, safejoin, uniqify


class RealdebridComTorrent(Crypter):
    __name__ = "RealdebridComTorrent"
    __type__ = "crypter"
    __version__ = "0.15"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("include_filter", "str", "File types to include (e.g. *.iso;*.zip, leave empty to select none)", "*.*"),
                  ("exclude_filter", "str", "File types to exclude (e.g. *.exe;advertisement.txt, leave empty to select none)", ""),
                  ("del_finished", "bool", "Delete downloaded torrents from the server", True)]

    __description__ = """Realdebrid.com torrents crypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    # See https://api.real-debrid.com/
    API_URL = "https://api.real-debrid.com/rest/1.0"
    API_ERRORS_MAX = 20

    def api_error_message(self, res):
        """ Formatted API error message with defaults handled """
        return "Error from API %s (%s) - %s." % (
            res.get('error', 'unhandled'),
            res.get('error_code', '-1'),
            res.get('error_details', '')
        )

    def api_error(self, res):
        """ Fail with formatted API error message """
        self.fail(self.api_error_message(res))

    def api_response(self, method, get={}, post={}, fail_on_error=True):
        """ Get API response with re-login support. """
        self.req.http.c.setopt(pycurl.USERAGENT,
                               "pyLoad/%s" % self.pyload.version)

        for _i in range(2):
            try:
                json_data = self.load(self.API_URL + method,
                                      get=get,
                                      post=post)

            except BadHeader, e:
                json_data = e.content

            except Exception, e:
                self.log_debug("Unhandled exception %s" % e)
                json_data = ""

            res = json.loads(json_data) if len(json_data) > 0 else {}

            if 'error_code' in res:
                # token expired, refresh the token and retry
                if res['error_code'] == 8:
                    self.account.relogin()
                    if not self.account.info['login']['valid']:
                        return res

                    else:
                        self.api_token = self.account.accounts[
                            self.account.accounts.keys()[0]]["api_token"]
                        get['auth_token'] = self.api_token
                        continue

                elif fail_on_error:
                    self.api_error(res)

            return res

        else:
            self.fail(_("Refresh token has failed"))

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
                torrent_filename = urllib.url2pathname(self.pyfile.url[7:]).encode('latin1').decode('utf8')  #: trim the starting `file://`
                if not exists(torrent_filename):
                    self.fail(_("Torrent file does not exist"))

            #: Check if the torrent file path is inside pyLoad's config directory
            if os.path.abspath(torrent_filename).startswith(os.path.abspath(os.getcwd()) + os.sep):
                for _i in range(2):
                    try:
                        #: send the torrent content to the server
                        json_data = self.upload(torrent_filename,
                                                self.API_URL + "/torrents/addTorrent",
                                                get={'auth_token': self.api_token})
                    except BadHeader, e:
                        json_data = e.content

                    api_data = json.loads(json_data) if len(json_data) > 0 else {}

                    if 'error_code' in api_data:
                        if api_data['error_code'] == 8:  #: token expired, refresh the token and retry
                            self.account.relogin()
                            if not self.account.info['login']['valid']:
                                self.fail(_("Token refresh has failed"))

                            else:
                                self.api_token = self.account.accounts[self.account.accounts.keys()[0]]["api_token"]

                        else:
                            error_msg = api_data['error']
                            self.fail(error_msg)

                    else:
                        break

                else:
                    self.fail(_("Token refresh has failed"))

            else:
                self.fail(_("Illegal URL"))  #: We don't allow files outside pyLoad's config directory

        else:
            #: magnet URL, send to the server
            api_data = self.api_response("/torrents/addMagnet",
                                          get={'auth_token': self.api_token},
                                          post={'magnet': self.pyfile.url})

        torrent_id = api_data['id']

        torrent_info = self.api_response("/torrents/info/" + torrent_id,
                                         get={'auth_token': self.api_token})

        if 'error' in torrent_info:
            self.api_error(torrent_info)

        #: Filter and select files for downloading
        exclude_filters = self.config.get('exclude_filter').split(';')
        excluded_ids = []
        for _filter in exclude_filters:
            excluded_ids.extend([_file['id'] for _file in torrent_info['files']
                                 if fnmatch.fnmatch(os.path.basename(_file['path']), _filter)])

        excluded_ids = uniqify(excluded_ids)

        include_filters = self.config.get('include_filter').split(';')
        included_ids = []
        for _filter in include_filters:
            included_ids.extend([_file['id'] for _file in torrent_info['files']
                                 if fnmatch.fnmatch(os.path.basename(_file['path']), _filter)])

        included_ids = uniqify(included_ids)

        selected_ids = ",".join([str(_id) for _id in included_ids
                                 if _id not in excluded_ids])

        if len(selected_ids) == 0:
            self.delete_torrent_from_server(torrent_id)
            self.fail(("No files for TorrentID %s. "
                       "Possibly wrong magnet or error "
                       "on Real-Debrid's side.") % torrent_id)

        self.api_response("/torrents/selectFiles/" + torrent_id,
                          get={'auth_token': self.api_token},
                          post={'files': selected_ids})

        return torrent_id

    def wait_for_server_dl(self, torrent_id):
        """ Show progress while the server does the download """

        torrent_info = self.api_response("/torrents/info/" + torrent_id,
                                         get={'auth_token': self.api_token})

        if 'error' in torrent_info:
            self.api_error(torrent_info)

        self.pyfile.name = torrent_info['original_filename']
        self.pyfile.size = torrent_info['original_bytes']

        self.pyfile.setCustomStatus("torrent")
        self.pyfile.setProgress(0)

        api_errors_count = 0
        while torrent_info['status'] != 'downloaded' or torrent_info['progress'] != 100:
            progress = int(torrent_info['progress'])
            self.pyfile.setProgress(progress)

            self.sleep(5)

            res = self.api_response("/torrents/info/" + torrent_id,
                                    get={'auth_token': self.api_token},
                                    fail_on_error=False)

            log_info = ["WAITING [%s]" % torrent_id]
            error = False

            # we received json status from API
            if len(res) > 0:
                torrent_info = res

                # There was error status (known) received from API
                #
                # FIXME: we are currently retrying for all error types
                # but in some cases (missing parameter) retry won't help.
                # But it also doesn't hurt much, so probably not worth to
                # decide which cases should be retried and which ones not
                # https://api.real-debrid.com/#api_error_codes
                #
                if 'error' in torrent_info:
                    log_info.append(self.api_error_message(torrent_info))
                    error = True

                # reset errors count when everything is OK
                else:
                    api_errors_count = 0

                    # Even with no API errors, torrent may still be in error
                    # state. We cancel such downloads immediately.
                    if torrent_info["status"] in ['magnet_error',
                                                  'error',
                                                  'virus',
                                                  'waiting_files_selection',
                                                  'dead']:
                        log_info.append("Torrent in error state: %s" % torrent_info["status"])
                        # hackish way to disable retrying
                        api_errors_count = self.API_ERRORS_MAX

            # No JSON from API. We definitely want to retry,
            # maybe API was just down or glitching.
            else:
                log_info.append("Receiving JSON status from API failed")
                error = True

            if error:
                api_errors_count += 1
                log_info.append("Retrying %d/%d" % (api_errors_count,
                                                        self.API_ERRORS_MAX))

            if self.pyload.debug:
                log_info.append("Torrent info: %s" % torrent_info)

            if api_errors_count < self.API_ERRORS_MAX:
                self.log_debug(" | ".join(log_info))
            else:
                self.fail(" | ".join(log_info))

        self.pyfile.setProgress(100)

        return torrent_info['links']

    def delete_torrent_from_server(self, torrent_id):
        """ Remove the torrent from the server """
        url = "%s/torrents/delete/%s?auth_token=%s" % (self.API_URL, torrent_id, self.api_token)
        self.log_debug("DELETE URL %s" % url)
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.USERAGENT, "pyLoad/%s" % self.pyload.version)
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
        torrent_id = 0
        if 'RealdebridCom' not in self.pyload.accountManager.plugins:
            self.fail(_("This plugin requires an active Realdebrid.com account"))

        self.account = self.pyload.accountManager.getAccountPlugin("RealdebridCom")
        if len(self.account.accounts) == 0:
            self.fail(_("This plugin requires an active Realdebrid.com account"))

        self.api_token = self.account.accounts[self.account.accounts.keys()[0]]["api_token"]

        try:
            torrent_id = self.send_request_to_server()
            torrent_urls = self.wait_for_server_dl(torrent_id)

            self.packages = [(pyfile.package().name, torrent_urls, pyfile.package().name)]

        finally:
            if torrent_id and self.config.get("del_finished"):
                self.delete_torrent_from_server(torrent_id)
