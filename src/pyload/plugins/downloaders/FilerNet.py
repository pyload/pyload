import json
import re

from pyload.core.network.http.exceptions import BadHeader

from ..anticaptchas.HCaptcha import HCaptcha
from ..base.simple_downloader import SimpleDownloader


class FilerNet(SimpleDownloader):
    __name__ = "FilerNet"
    __type__ = "downloader"
    __version__ = "0.39"
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

    # See https://filer.net/api/#/
    API_URL = "https://filer.net/api/"

    def api_request(self, method, user=None, password=None):
        try:
            if user and password:
                self.req.add_auth(f"{user}:{password}")
            # /dl/{hash}.json returns 302 redirect with empty body
            # We need to extract the Location header for the download URL
            url = f"{self.API_URL}{method}.json"
            json_data = self.load(url, redirect=False)

            # Handle 302 redirect from premium download endpoint
            if self.req.code == 302:
                location = self.req.http.response_headers.get("Location", "")
                if location:
                    return {"download_url": location}
                elif json_data:
                    return self.parse_json(json_data)
                else:
                    self.log_error("302 redirect but no Location header")
                    raise ValueError("No download URL from redirect")

        except BadHeader as exc:
            json_data = exc.content
        finally:
            if user and password:
                self.req.remove_auth()

        return self.parse_json(json_data)

    def api_info(self, url):
        info = {}
        file_id = re.match(self.__pattern__, url).group("ID")

        # Try new API first, fall back to old API
        api_data = self._get_file_status_new(file_id)
        if api_data is None:
            api_data = self._get_file_status_old(file_id)

        if api_data:
            info.update(api_data)
        else:
            info["status"] = 1  #: offline

        return info

    def _get_file_status_new(self, file_id):
        """New API: GET /api/file/{hash}"""
        try:
            json_data = self.load(f"{self.API_URL}file/{file_id}", redirect=False)
            api_data = json.loads(json_data)
        except (BadHeader, json.JSONDecodeError):
            return None

        if "file_hash" in api_data:
            return {
                "name": api_data.get("file_name"),
                "size": api_data.get("file_size"),
                "premium_only": api_data.get("premium_only", False),
                "status": 2,  #: online
            }
        return None

    def _get_file_status_old(self, file_id):
        """Old API: GET /api/status/{hash}.json"""
        try:
            json_data = self.load(f"{self.API_URL}status/{file_id}.json", redirect=False)
            api_data = json.loads(json_data)
        except (BadHeader, json.JSONDecodeError):
            return None

        if api_data.get("code") == 200:
            data = api_data.get("data", {})
            return {
                "name": data.get("file_name"),
                "size": data.get("file_size"),
                "premium_only": data.get("premium_only", False),
                "status": 2,  #: online
            }
        return None

    def handle_free(self, pyfile):
        if self.info.get("premium_only") is True and not self.premium:
            self.fail(self._("File can be downloaded by premium users only"))

        if self.account:
            self.fail(self._("Free account downloads are unsupported"))

        file_id = self.info["pattern"]["ID"]

        # Step 1: Request download ticket with hCaptcha
        self.captcha = HCaptcha(pyfile)
        captcha_response = self.captcha.challenge(self.HCAPTCHA_KEY)

        url = f"{self.API_URL}file/request/{file_id}?hCaptchaToken={captcha_response}"
        api_data = self.load(url, redirect=False)
        try:
            api_data = json.loads(api_data)
        except json.JSONDecodeError:
            self.fail(self._("Invalid response from server"))

        # New API uses "message" for errors, old API used "error"
        message = api_data.get("message")
        error = api_data.get("error")
        if message:
            self.log_error(message)
            self.fail(message)
        if error:
            self.log_error(error)
            if error == "HOURLY_DOWNLOAD_LIMIT":
                self.retry(wait=3600)
            elif error in ("CONCURRENT_DOWNLOAD_LIMIT", "TICKET_LIMIT_REACHED"):
                self.temp_offline()
            else:
                self.fail(error)

        ticket = api_data.get("ticket")
        if not ticket:
            self.fail(self._("No ticket received from server"))

        wait_time = api_data.get("wt", 0)
        self.wait(wait_time)

        # Step 2: Get download URL with ticket
        api_data = self.load(
            f"{self.API_URL}file/download",
            post={"ticket": ticket},
            redirect=False
        )
        try:
            api_data = json.loads(api_data)
        except json.JSONDecodeError:
            self.fail(self._("Invalid response from server"))

        error = api_data.get("error")
        if error:
            self.log_error(error)
            if error == "HOURLY_DOWNLOAD_LIMIT":
                self.retry(wait=3600)
            elif error in ("CONCURRENT_DOWNLOAD_LIMIT", "TICKET_LIMIT_REACHED"):
                self.temp_offline()
            else:
                self.fail(error)
        else:
            self.link = api_data.get("downloadUrl")

    def handle_premium(self, pyfile):
        file_id = self.info["pattern"]["ID"]

        user = self.account.user
        password = self.account.get_login("password")
        api_data = self.api_request(f"dl/{file_id}", user, password)

        # New API /dl/{hash}.json returns 302 redirect with download_url
        download_url = api_data.get("download_url")
        if download_url:
            self.link = download_url
            return

        # Fallback to old API response format
        code = api_data.get("code", 200)
        if code == 200:
            download_url = api_data.get("data", {}).get("download_url")
            if download_url:
                self.link = download_url
        elif code == 429:
            self.temp_offline(self._("Concurrent download limit reached"))
        elif code == 503:
            self.temp_offline(self._("No download server available"))
        elif code == 403:
            self.fail(self._("Premium account required"))
        elif code == 401:
            self.fail(self._("Authentication failed"))
        else:
            self.log_error(api_data.get("status", "unknown error"))
            self.fail(api_data.get("status", "unknown error"))
