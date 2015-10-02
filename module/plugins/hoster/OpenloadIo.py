# -*- coding: utf-8 -*-

import json
import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class OpenloadIo(SimpleHoster):
    __name__    = "OpenloadIo"
    __type__    = "hoster"
    __version__ = "0.07"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?openload\.(?:co|io)/f/([\w-_]+)'

    __description__ = """Openload.co hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [(None, None)]


    # The API reference, that this implementation uses is available at https://openload.co/api
    API_URL = 'https://api.openload.co/1'

    _FILE_ID_PATTERN = '/f/([\w-_]+)'

    _DOWNLOAD_TICKET_URI_PATTERN = '/file/dlticket?file={0}'
    _DOWNLOAD_FILE_URI_PATTERN   = '/file/dl?file={0}&ticket={1}'
    _FILE_INFO_URI_PATTERN       = '/file/info?file={0}'


    @classmethod
    def _load_json(cls, uri):
        return json.loads(getURL(cls.API_URL + uri))


    @classmethod
    def get_info(cls, url="", html=""):
        file_id = re.findall(cls._FILE_ID_PATTERN, url, re.I)
        if not file_id:
            return super(OpenloadIo, cls).get_info(url)

        file_id = file_id[0]
        info_json = cls._load_json(cls._FILE_INFO_URI_PATTERN.format(file_id))
        file_info = info_json['result'][file_id]

        return {'name'  : file_info['name'],
                'size'  : file_info['size'],
                'status': 3 if url.strip() else 8,
                'url'   : url}


    def setup(self):
        self.multiDL     = True
        self.chunk_limit = 1


    def handle_free(self, pyfile):
        # If the link is being handled here, then it matches the file_id_pattern,
        # therefore, we can call [0] safely.
        file_id = re.findall(self._FILE_ID_PATTERN, pyfile.url, re.I)[0]

        ticket_json = self._load_json(self._DOWNLOAD_TICKET_URI_PATTERN.format(file_id))

        self.wait(ticket_json['result']['wait_time'])

        ticket = ticket_json['result']['ticket']

        download_json = self._load_json(self._DOWNLOAD_FILE_URI_PATTERN.format(file_id, ticket))
        self.link = download_json['result']['url']


getInfo = create_getInfo(OpenloadIo)
