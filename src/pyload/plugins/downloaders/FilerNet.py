import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.HCaptcha import HCaptcha
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
        ("fallback", "bool", "Fallback to free download if premium fails", True),
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

    HCAPTCHA_KEY = "45623a98-7b08-43ae-b758-c21c13024e2a"

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def api_request(self, method, user=None, password=None):
        try:
            if user and password:
                self.req.add_auth(f"{user}:{password}")
            json_data = self.load(f"{self.API_URL}{method}.json")
        except BadHeader as exc:
            json_data = exc.content
        finally:
            if user and password:
                self.req.remove_auth()

        return json.loads(json_data)

    def old_api_request(self, method, is_post=True, **kwargs):
        try:
            if is_post:
                json_data = self.load(self.API_URL + method, post=kwargs)
            else:
                json_data = self.load(self.API_URL + method, get=kwargs)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")

        api_data = self.api_request(f"status/{file_id}")
        if api_data["code"] == 200:
            data = api_data["data"]
            info.update({
                "name": data["file_name"],
                "size": data["file_size"],
                "premium_only": data["premium_only"],
                "status": 2,  #: online
            })
        else:
            info["status"] = 1  #: offline

        return info

    def handle_free(self, pyfile):
        if self.info["premium_only"] is True and not self.premium:
            self.fail(self._("File can be downloaded by premium users only"))

        if self.account:
            self.fail(self._("Free account downloads are unsupported"))

        file_id = self.info["pattern"]["ID"]

        self.captcha = HCaptcha(pyfile)
        captcha_response = self.captcha.challenge(self.HCAPTCHA_KEY)
        api_data = self.old_api_request(f"file/request/{file_id}", False, hCaptchaToken=captcha_response)
        error = api_data.get("error")
        if error:
            self.log_error(error)
            if error == "HOURLY_DOWNLOAD_LIMIT":
                self.retry(wait=3600)
            elif error in ("CONCURRENT_DOWNLOAD_LIMIT", "TICKET_LIMIT_REACHED"):
                self.temp_offline()
            else:
                self.fail(error)


        wait_time = api_data["wt"]
        self.wait(wait_time)
        api_data = self.old_api_request("file/download", True, ticket=api_data["t"])
        error = api_data.get("error")
        if error:
            self.log_error(error)
            if error == "HOURLY_DOWNLOAD_LIMIT":
                self.retry(wait=3600)
            else:
                self.fail(error)
        else:
            self.link = api_data["downloadUrl"]

    def handle_premium(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        user = self.account.user
        password = self.account.info["login"]["password"]
        api_data = self.api_request(f"dl/{file_id}", user, password)
        code = api_data["code"]
        if code == 200:
            self.link = api_data["data"]["download_url"]

        elif code == 429:
            self.temp_offline(self._("Concurrent download limit reached"))
        elif code == 503:
            self.temp_offline(self._("No download server available"))

