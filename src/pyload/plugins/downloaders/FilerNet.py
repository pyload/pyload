import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..base.simple_downloader import SimpleDownloader


class FilerNet(SimpleDownloader):
    __name__ = "FilerNet"
    __type__ = "downloader"
    __version__ = "0.36"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filer\.net/get/(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filer.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api/json
    API_URL = "https://filer.net/api"

    def api_request(self, endpoint, **kwargs):
        try:
            json_data = self.load(f"{self.API_URL}/{endpoint}", get=kwargs or None, redirect=False)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")

        api_data = self.api_request(f"status/{file_id}.json")
        if api_data.get("code") == 500:
            info["status"] = 1  #: offline
        else:
            data = api_data["data"]
            info.update({
                "name": data["file_name"],
                "size": data["file_size"],
                "premium_only": data["premium_only"],
                "status": 2,  #: online
            })

        return info

    def handle_free(self, pyfile):
        self.fail(self._("Only premium users can download from Filer.net"))

    def handle_premium(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        user = self.account.user
        password = self.account.info["login"]["password"]
        self.req.add_auth(f"{user}:{password}")
        try:
            api_data = self.api_request(f"dl/{file_id}.json")
        finally:
            self.req.remove_auth()

        code = api_data.get("code")
        if code == 401:
            self.fail(self._("Authentication required"))
        elif code == 403:
            self.fail(self._("Premium account required"))
        elif code == 429:
            self.temp_offline(self._("Concurrent download limit reached"))
        elif code == 500:
            self.offline()
        elif code == 503:
            self.temp_offline(self._("No download server available"))

        self.link = api_data["data"]["download_url"]

