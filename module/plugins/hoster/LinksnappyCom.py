# -*- coding: utf-8 -*-

import time
import urlparse

from ..internal.misc import format_size, json
from ..internal.MultiHoster import MultiHoster


class LinksnappyCom(MultiHoster):
    __name__ = "LinksnappyCom"
    __type__ = "hoster"
    __version__ = "0.20"
    __status__ = "testing"

    __pattern__ = r'https?://(?:[^/]+\.)?linksnappy\.com'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", False),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
                  ("revert_failed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Linksnappy.com multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it"),
                   ("Bilal Ghouri", None),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CHECK_TRAFFIC = True

    API_URL = "https://linksnappy.com/api/"

    def api_response(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method,
                                    get=kwargs))

    def handle_premium(self, pyfile):
        json_params = json.dumps({'link': pyfile.url})

        api_data = self.api_response("linkgen", genLinks=json_params)['links'][0]

        if api_data['status'] != "OK":
            self.fail(api_data['error'])

        if api_data.get('cacheDL', False):
            self._cache_dl(api_data['hash'])

        pyfile.name = api_data['filename']
        self.link = api_data['generated']

    def out_of_traffic(self):
        url_p = urlparse.urlparse(self.pyfile.url)
        json_data = self.api_response("FILEHOSTS")

        for k, v in json_data['return'].items():
            url = urlparse.urlunparse(url_p._replace(netloc=k))
            if self.pyload.pluginManager.plugins['hoster'][self.pyfile.pluginname]['re'].match(url) is not None:
                quota = v['Quota']
                if quota == "unlimited":
                    return False

                else:
                    size = self.pyfile.size
                    usage = v.get('Usage', 0)
                    traffic_left = quota - usage
                    self.log_info(_("Filesize: %s") % format_size(size),
                                  _("Traffic left for user `%s`: %s") % (self.account.user, format_size(traffic_left)))

                    return size > traffic_left

        else:
            self.log_warning(_("Could not determine traffic usage for host %s") % url_p.netloc)
            return False

    def _cache_dl(self,file_hash):
        self.pyfile.setCustomStatus("server dl")
        self.pyfile.setProgress(0)

        while True:
            api_data = self.api_response("CACHEDLSTATUS", id=file_hash)

            if api_data['status'] != "OK":
                self.fail(api_data['error'])

            progress = api_data['return']['percent']
            self.pyfile.setProgress(progress)
            if progress == 100:
                break

            self._sleep(2)

    def _sleep(self, sec):
        for _i in range(sec):
            if self.pyfile.abort:
                break
            time.sleep(1)
