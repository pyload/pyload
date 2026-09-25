import json
import re

from ..anticaptchas.HCaptcha import HCaptcha
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.Turnstile import Turnstile
from ..base.simple_downloader import SimpleDownloader


class TurbobitNet(SimpleDownloader):
    __name__ = "TurbobitNet"
    __type__ = "downloader"
    __version__ = "0.58"
    __status__ = "testing"

    __pattern__ = r"https?://(?:(?:www|m)\.)?(?:(?:trbbt|turbo(?:beet|bit[ea]?)|torbobit)\.net|(?:tourbobit|turbobi(?:tn?|f))\.com|turbo?\.(?:to|cc)|turb\.pw|trbt\.cc)/(?:download/free/)?(?P<ID>\w+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Turbobit.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("prOq", None),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://turbobit.net/\g<ID>.html")]
    SIZE_REPLACEMENTS = [(r' ', "")]

    COOKIES = [("turbobit.net", "user_lang", "en")]

    LINK_PREMIUM_PATTERN = r'href=[\'"](.+?/download/redirect/[^"\']+)'

    API_URL = "https://app.turbobit.net/api/"

    def api_request(self, method, **kwargs):
        self.req.http.set_header("Accept", "application/json, text/plain, */*")
        if kwargs:
            self.req.http.set_header("Content-Type", "application/json")
            post_data = json.dumps(kwargs)
        else:
            post_data = None

        data = self.load(self.API_URL + method, post=post_data)
        return json.loads(data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")
        api_data = self.api_request(
            "download/info",
            fileId=file_id,
            referrer=None,
            site=None,
            shortDomain=""
        )

        err = api_data.get("error_name")
        if err == "file_is_not_available_for_download":
            info["status"] = 1
        else:
            info["status"] = 2
            info["name"] = api_data["file"]["name"]
            info["size"] = api_data["file"]["size"]
            if api_data.get("premium"):
                info["premium_download_url"] = api_data["downloadUrls"][0]
            else:
                info["premium_only"] = api_data["premiumOnlyDownload"]

        return info

    def handle_free(self, pyfile):
        file_id=self.info["pattern"]["ID"]
        if self.info["premium_only"] is True:
            self.fail(self._("File can be downloaded by premium users only"))

        api_data = self.api_request("captcha")
        captcha_key = api_data.get("publicKey")
        if not captcha_key:
            self.fail(self._("Captcha key not found in API response"))
        captcha_type = api_data.get("driver")
        if captcha_type == "recaptcha":
            self.captcha = ReCaptcha(self.pyfile)
        elif captcha_type == "hcaptcha":
            self.captcha = HCaptcha(self.pyfile)
        elif captcha_type == "turnstile":
            self.captcha = Turnstile(self.pyfile)
        else:
            self.fail(self._("Unsupported captcha type: {}").format(captcha_type))

        api_data = self.api_request("download/free/init", fileId=file_id)
        delay = (api_data.get("ipBan") or {}).get("delay")
        if delay:
            self.retry(wait=api_data["ipBan"]["delay"], msg=self._("IP is banned for free downloads"))

        response = self.captcha.challenge(captcha_key)
        api_data = self.api_request("download/free/captcha", fileId=file_id, captchaResponse=response)
        if "delay" not in api_data:
            self.fail(self._("API response does not contain delay information"))
        self.wait(api_data["delay"])
        api_data = self.api_request("download/free/prepare", fileId=file_id)
        if api_data.get("success") is not True:
            self.fail(self._("API response indicates failure to prepare download"))
        api_data = self.api_request("download/free/start", fileId=file_id)
        if "downloadUrl" not in api_data:
            self.fail(self._("API response does not contain download URL"))
        self.link = api_data["downloadUrl"]

    def handle_premium(self, pyfile):
        self.link = self.info["premium_download_url"]
