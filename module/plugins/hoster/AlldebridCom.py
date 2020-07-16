# -*- coding: utf-8 -*-

from ..internal.misc import json
from ..internal.MultiHoster import MultiHoster


class AlldebridCom(MultiHoster):
    __name__ = "AlldebridCom"
    __type__ = "hoster"
    __version__ = "0.61"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?alldebrid\.com/dl/[\w^_]+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Alldebrid.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Andy Voigt", "spamsales@online.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    URL_REPLACEMENTS = [(r'https?://(?:www\.)?mega(?:\.co)?\.nz/#N!(?P<ID>[\w^_]+)!(?P<KEY>[\w\-,=]+)###n=(?P<OWNER>[\w^_]+)',
                         lambda m:"https://mega.nz/#!%s!%s~~%s" % (m.group("ID"), m.group("KEY"), m.group("OWNER"))),
                        (r'https?://(?:www\.)?mega(?:\.co)?\.nz/.*', lambda m:m.group(0).replace('_', '/'))]

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

    def setup(self):
        self.chunk_limit = 16

    def handle_premium(self, pyfile):
        api_data = self.api_response("link/unlock",
                                      get={'link': pyfile.url,
                                           'apikey': self.account.info['login']['password']})

        if api_data.get("error", False):
            if api_data['error']['code'] == 'LINK_DOWN':
                self.offline()

            else:
                self.log_error(api_data['error']['message'])
                self.temp_offline()

        else:
            pyfile.name = api_data['filename']
            pyfile.size = api_data['filesize']
            self.link = api_data['link']
