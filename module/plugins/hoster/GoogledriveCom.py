# -*- coding: utf-8 -*
#
# Test links:
#   https://drive.google.com/file/d/0B6RNTe4ygItBQm15RnJiTmMyckU/view?pli=1


from module.network.HTTPRequest import BadHeader

from ..internal.Hoster import Hoster
from ..internal.misc import json


class GoogledriveCom(Hoster):
    __name__ = "GoogledriveCom"
    __type__ = "hoster"
    __version__ = "0.27"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:drive|docs)\.google\.com/(?:file/d/|uc\?.*id=)(?P<ID>[-\w]+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Drive.google.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://www.googleapis.com/drive/v3/"
    API_KEY = "AIzaSyAcA9c4evtwSY1ifuvzo6HKBkeot5Bk_U4"

    def setup(self):
        self.multiDL = True
        self.resume_download = True
        self.chunk_limit = 1

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

    def api_download(self):
        try:
            self.download("%s%s/%s" % (self.API_URL, "files", self.info['pattern']['ID']),
                          get={'alt': "media",
                               # 'acknowledgeAbuse': "true",
                               'key': self.API_KEY})

        except BadHeader, e:
            if e.code == 404:
                self.offline()

            elif e.code == 403:
                self.temp_offline()

            else:
                raise

    def process(self, pyfile):
        json_data = self.api_response("files/" + self.info['pattern']['ID'], fields="md5Checksum,name,size")

        if json_data is None:
            self.fail("API error")

        if 'error' in json_data:
            if json_data['error']['code'] == 404:
                self.offline()

            else:
                self.fail(json_data['error']['message'])

        pyfile.size = long(json_data['size'])
        pyfile.name = json_data['name']
        self.info['md5'] = json_data['md5Checksum']

        self.api_download()
