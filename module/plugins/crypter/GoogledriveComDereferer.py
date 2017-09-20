# -*- coding: utf-8 -*

from module.network.HTTPRequest import BadHeader

from ..internal.Crypter import Crypter
from ..internal.misc import json


class GoogledriveComDereferer(Crypter):
    __name__ = "GoogledriveComDereferer"
    __type__ = "crypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:drive|docs)\.google\.com/open\?(?:.+;)?id=(?P<ID>[-\w]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Drive.google.com dereferer plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r"folderName: '(?P<N>.+?)'"
    OFFLINE_PATTERN = r'<TITLE>'

    API_URL = "https://www.googleapis.com/drive/v3/"
    API_KEY = "AIzaSyAcA9c4evtwSY1ifuvzo6HKBkeot5Bk_U4"

    def api_response(self, cmd, **kwargs):
        kwargs['key'] = self.API_KEY
        try:
            json_data = json.loads(self.load("%s%s" % (self.API_URL, cmd),
                                             get=kwargs))
            self.log_debug("API response: %s" % json_data)
            return json_data

        except BadHeader, e:
            try:
                json_data = json.loads(e.content)
                self.log_error("API Error: %s" % cmd,
                               json_data['error']['message'],
                               "ID: %s" % self.info['pattern']['ID'],
                               "Error code: %s" % e.code)

            except ValueError:
                self.log_error("API Error: %s" % cmd,
                               e,
                               "ID: %s" % self.info['pattern']['ID'],
                               "Error code: %s" % e.code)
            return None

    def decrypt(self, pyfile):
        json_data = self.api_response("files/%s" % self.info['pattern']['ID'])
        if json_data is None:
            self.fail("API error")

        if 'error' in json_data:
            if json_data['error']['code'] == 404:
                self.offline()

            else:
                self.fail(json_data['error']['message'])

        link = "https://drive.google.com/%s/%s" % \
               (("file/d" if json_data['mimeType'] != "application/vnd.google-apps.folder" else "drive/folders"),
                self.info['pattern']['ID'])

        self.packages = [(pyfile.package().folder, [link], pyfile.package().name)]
