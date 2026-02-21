import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.HCaptcha import HCaptcha
from ..base.simple_downloader import SimpleDownloader


class FilerNet(SimpleDownloader):
    __name__ = "FilerNet"
    __type__ = "downloader"
    __version__ = "0.35"
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

    def api_request(self, method, is_post=True, **kwargs):
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

        api_data = self.api_request(f"file/{file_id}")
        if api_data.get("message") == "File not found":
            info["status"] = 1
        else:
            info.update({
                "name": api_data["name"],
                "size": api_data["size"],
                "premium_only": api_data["premiumOnly"],
                "status": 2
            })

        return info

    def handle_free(self, pyfile):
        if self.info["premium_only"] is True and not self.premium:
            self.fail(self._("File can be downloaded by premium users only"))

        file_id = self.info["pattern"]["ID"]

        self.captcha = HCaptcha(pyfile)
        captcha_response = self.captcha.challenge(self.HCAPTCHA_KEY)

        api_data = self.api_request(f"file/request/{file_id}", is_post=False, hCaptchaToken=captcha_response)
        error = api_data.get("error")
        if error:
            self.log_error(error)
            if error == "HOURLY_DOWNLOAD_LIMIT":
                self.retry(wait=3600)
            elif error == "CONCURRENT_DOWNLOAD_LIMIT":
                self.temp_offline()
            else:
                self.fail(error)

        wait_time = api_data["wt"]
        self.wait(wait_time)
        api_data = self.api_request("file/download", ticket=api_data["t"])
        if "error" in api_data:
            self.fail(api_data["error"])
        else:
            self.link = api_data["downloadUrl"]

    def handle_premium(self, pyfile):
        self.handle_free(pyfile)

