# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster
from module.plugins.internal.misc import json


class OpenloadIo(SimpleHoster):
    __name__    = "OpenloadIo"
    __type__    = "hoster"
    __version__ = "0.16"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?openload\.(co|io)/(f|embed)/(?P<ID>[\w\-]+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Openload.co hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [(None, None)]


    # The API reference, that this implementation uses is available at https://openload.co/api
    API_URL = 'https://api.openload.co/1'

    _DOWNLOAD_TICKET_URI_PATTERN = '/file/dlticket?file=%s'
    _DOWNLOAD_FILE_URI_PATTERN   = '/file/dl?file=%s&ticket=%s'
    _FILE_INFO_URI_PATTERN       = '/file/info?file=%s'

    OFFLINE_PATTERN = r'>We are sorry'


    @classmethod
    def _load_json(cls, uri):
        return json.loads(get_url(cls.API_URL + uri))


    @classmethod
    def api_info(cls, url):
        file_id   = re.match(cls.__pattern__, url).group('ID')
        info_json = cls._load_json(cls._FILE_INFO_URI_PATTERN % file_id)
        file_info = info_json['result'][file_id]

        return {'name': file_info['name'],
                'size': file_info['size']}


    def setup(self):
        self.multiDL     = True
        self.chunk_limit = 1


    def handle_free(self, pyfile):
        # If the link is being handled here, then it matches the file_id_pattern,
        # therefore, we can call [0] safely.
        file_id     = self.info['pattern']['ID']
        ticket_json = self._load_json(self._DOWNLOAD_TICKET_URI_PATTERN % file_id)

        if ticket_json['status'] == 404:
            self.offline(ticket_json['msg'])

        elif ticket_json['status'] == 509:
            self.temp_offline(ticket_json['msg'])

        elif ticket_json['status'] != 200:
            self.fail(ticket_json['msg'])

        self.wait(ticket_json['result']['wait_time'])

        ticket = ticket_json['result']['ticket']

        download_json = self._load_json(self._DOWNLOAD_FILE_URI_PATTERN % (file_id, ticket))
        self.link = download_json['result']['url']
