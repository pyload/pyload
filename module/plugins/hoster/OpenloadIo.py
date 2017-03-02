# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class OpenloadIo(SimpleHoster):
    __name__ = "OpenloadIo"
    __type__ = "hoster"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?openload\.(co|io)/(f|embed)/(?P<ID>[\w\-]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Openload.co hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [(None, None)]

    # The API reference, that this implementation uses is available at
    # https://openload.co/api
    API_URL = 'https://api.openload.co/1'

    _DOWNLOAD_TICKET_URI_PATTERN = '/file/dlticket?file=%s'
    _DOWNLOAD_FILE_URI_PATTERN = '/file/dl?file=%s&ticket=%s&captcha_response=%s'
    _FILE_INFO_URI_PATTERN = '/file/info?file=%s'

    OFFLINE_PATTERN = r'>We are sorry'

    @classmethod
    def _load_json(cls, uri):
        return json.loads(get_url(cls.API_URL + uri))

    @classmethod
    def api_info(cls, url):
        file_id = re.match(cls.__pattern__, url).group('ID')
        info_json = cls._load_json(cls._FILE_INFO_URI_PATTERN % file_id)
        file_info = info_json['result'][file_id]

        return {'name': file_info['name'],
                'size': file_info['size']}

    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        # If the link is being handled here, then it matches the file_id_pattern,
        # therefore, we can call [0] safely.
        file_id = self.info['pattern']['ID']

        while True:
            ticket_json = self._load_json(
                self._DOWNLOAD_TICKET_URI_PATTERN % file_id)

            if ticket_json['status'] == 404:
                self.offline(ticket_json['msg'])

            elif ticket_json['status'] == 509:
                self.temp_offline(ticket_json['msg'])

            elif ticket_json['status'] != 200:
                self.fail(ticket_json['msg'])

            self.wait(ticket_json['result']['wait_time'])

            # check if a captcha is required for this download
            captchaResponse = ''
            if 'captcha_url' in ticket_json['result'] and ticket_json[
                    'result']['captcha_url'] != False:
                self.log_debug(
                    'This download requires a captcha solution: %s' %
                    (ticket_json['result']['captcha_url']))
                captchaResponse = self.captcha.decrypt(
                    ticket_json['result']['captcha_url'])

            ticket = ticket_json['result']['ticket']

            download_json = self._load_json(
                self._DOWNLOAD_FILE_URI_PATTERN %
                (file_id, ticket, captchaResponse))

            # check download link request result status
            if download_json['status'] == 403:
                # wrong captcha, get new captcha and try again
                self.log_debug('Captcha solution is incorrect')
                continue

            if download_json['status'] == 200:
                # start downloading
                break

            # no status 403 or 200 means getting the download url failed, abort
            self.fail(download_json['msg'])

        self.link = download_json['result']['url']
