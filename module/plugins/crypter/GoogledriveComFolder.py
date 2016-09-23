# -*- coding: utf-8 -*

import os

from module.network.HTTPRequest import BadHeader
from module.plugins.internal.Crypter import Crypter
from module.plugins.internal.misc import json


class GoogledriveComFolder(Crypter):
    __name__    = "GoogledriveComFolder"
    __type__    = "crypter"
    __version__ = "0.08"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?drive\.google\.com/(?:folderview\?.*id=|drive/(?:.+?/)?folders/)(?P<ID>[-\w]+)'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Drive.google.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN    = r"folderName: '(?P<N>.+?)'"
    OFFLINE_PATTERN = r'<TITLE>'

    API_URL = "https://www.googleapis.com/drive/v3/"
    API_KEY = "AIzaSyAcA9c4evtwSY1ifuvzo6HKBkeot5Bk_U4"



    def api_response(self, cmd, **kwargs):
        kwargs['key'] = self.API_KEY
        try:
            json_data = json.loads(self.load("%s%s" % (self.API_URL, cmd), get=kwargs))
            self.log_debug("API response: %s" % json_data)
            return json_data

        except BadHeader, e:
            self.log_error("API Error: %s" % cmd, e, "ID: %s" % self.info['pattern']['ID'], "Error code: %s" % e.code)
            return None


    def decrypt(self, pyfile):
        links = []

        json_data = self.api_response("files/%s" %  self.info['pattern']['ID'])
        if json_data is None:
            self.fail("API error")

        if 'error' in json_data:
            if json_data['error']['code'] == 404:
                self.offline()

            else:
                self.fail(json_data['error']['message'])

        pack_name = json_data.get('name', pyfile.package().name)

        json_data = self.api_response("files", q="'%s' in parents" % self.info['pattern']['ID'],
                                               pageSize=100,
                                               fields="files/id,nextPageToken")

        if json_data is None:
            self.fail("API error")

        if 'error' in json_data:
            self.fail(json_data['error']['message'])

        for _f in json_data.get('files', []):
            links.append("https://drive.google.com/file/d/" + _f['id'])

        next_page = json_data.get('nextPageToken', None)
        while next_page:
            json_data = self.api_response("files", q="'%s' in parents" % self.info['pattern']['ID'],
                                          pageToken=next_page,
                                          pageSize=100,
                                          fields="files/id,nextPageToken")

            if json_data is None:
                self.fail("API error")

            if 'error' in json_data:
                self.fail(json_data['error']['message'])

            for _f in json_data.get('files', []):
                links.append("https://drive.google.com/file/d/" + _f['id'])

            next_page = json_data.get('nextPageToken', None)

        if links:
            self.packages = [(pack_name, links, pack_name)]


