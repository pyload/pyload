import json
import time

from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_downloader import MultiDownloader


class HighWayMe(MultiDownloader):
    __name__ = "HighWayMe"
    __type__ = "downloader"
    __version__ = "0.26"
    __status__ = "testing"

    __pattern__ = r"https?://(?:[\w\-]+\.)?(?:dwld\.link|high-way\.me)/dl2/[\w\-]+/?"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", False),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("revert_failed", "bool", "Revert to standard download if fails", True),
    ]

    __description__ = """High-Way.me multi-downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("EvolutionClip", "evolutionclip@live.de"),
        ("Yaknar", "yaknar[AT]high-way[DOT]me"),
    ]

    #: Download Center API, see the account plugin
    API_URL = "https://cloud.high-way.me/center-api/"

    #: Error codes of a link result
    TRAFFIC_ERRORS = (3, 14, 15, 18)  #: traffic of the host or the plan used up
    HOSTER_ERRORS = (8, 11, 16)  #: host temporarily unavailable or in maintenance
    OFFLINE_ERRORS = (9,)  #: file not found
    PASSWORD_ERRORS = (13,)  #: file is password protected

    #: Give up when the cache download makes no progress for this long (seconds)
    STALL_TIMEOUT = 30 * 60

    def setup(self):
        self.chunk_limit = 4

    def api_request(self, method, get=None, post=None):
        api_key = self.account.get_login("password")
        self.req.http.set_header("Authorization", f"Bearer {api_key}")
        self.req.http.set_header("Accept", "application/json")

        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)

        except BadHeader as exc:
            json_data = exc.content

        try:
            api_data = json.loads(json_data)

        except ValueError:
            self.log_warning(
                self._("Unable to get API data, waiting 1 minute and retry")
            )
            self.retry(5, 60, self._("Unable to get API data"))

        if "error" in api_data:
            #: Request failed as a whole (token, rights, unknown or aborted download)
            msg = api_data.get("message") or api_data["error"]
            if api_data["error"] in ("invalid_token", "authentication_required"):
                self.account.relogin()

            self.fail(msg)

        return api_data

    def sleep(self, sec):
        for _ in range(int(sec)):
            if self.pyfile.abort:
                break

            time.sleep(1)

    def check_result(self, result):
        code = int(result.get("code", 0))
        if code == 0:
            return

        msg = result.get("message") or result.get("error") or self._("Unknown error")
        wait = int(result.get("retry_in_seconds") or 0)

        if code in self.OFFLINE_ERRORS:
            self.offline(msg)

        elif code in self.PASSWORD_ERRORS:
            self.fail(msg)

        elif code in self.TRAFFIC_ERRORS:
            self.log_warning(msg)
            self.retry(5, max(wait, 3600), msg)

        elif code in self.HOSTER_ERRORS:
            self.log_warning(msg)
            self.retry(5, max(wait, 60), msg)

        elif code == 429:
            #: Limit of active transfers reached
            self.log_warning(msg)
            self.retry(12, 300, msg)

        else:
            self.fail(msg)

    def handle_premium(self, pyfile):
        api_data = self.api_request("download.php", post={"links": pyfile.url})
        results = api_data.get("results") or []
        if not results:
            self.fail(self._("No result for this link"))

        result = results[0]
        self.log_debug(
            f"Link result: code={result.get('code')} "
            f"cache_status={result.get('cache_status')}"
        )
        self.check_result(result)

        if result.get("queued"):
            #: Over the limit of active transfers, High-Way starts the link
            #: as soon as a slot is free
            msg = result.get("message") or self._("Waiting for a free transfer slot")
            self.log_info(msg)
            self.retry(12, 300, self._("Waiting for a free transfer slot"))

        if result.get("name"):
            pyfile.name = result["name"]

        if result.get("file_size"):
            pyfile.size = int(result["file_size"])

        if not result.get("cache_ready"):
            self.wait_for_cache(pyfile, result)

        if not result.get("download"):
            self.fail(self._("No download link"))

        self.link = result["download"]

    def wait_for_cache(self, pyfile, result):
        """
        The file is first loaded into High-Way's cache. Polling keeps that
        download alive, so poll until it is ready.
        """
        pyfile.set_custom_status("caching")
        progress = float(result.get("cache_percentage") or 0)
        pyfile.set_progress(int(progress))
        wait = int(result.get("retry_in_seconds") or 5)
        last_change = time.monotonic()

        while not pyfile.abort:
            self.sleep(min(max(wait, 2), 30))
            if pyfile.abort:
                break

            status = self.api_request(
                "download.php", get={"action": "cache", "id": result["id"]}
            )
            self.check_result(status)

            if status.get("ready"):
                pyfile.set_progress(100)
                return

            percentage = float(status.get("percentage") or 0)
            if percentage > progress:
                progress = percentage
                last_change = time.monotonic()

            elif time.monotonic() - last_change > self.STALL_TIMEOUT:
                self.retry(3, 60, self._("Caching makes no progress"))

            pyfile.set_progress(int(progress))
            wait = int(status.get("retry_in_seconds") or 5)

        self.abort()
