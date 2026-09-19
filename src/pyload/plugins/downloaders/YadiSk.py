import json
import re

from ..base.simple_downloader import SimpleDownloader


class YadiSk(SimpleDownloader):
    __name__ = "YadiSk"
    __type__ = "downloader"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r"https?://(?:yadi\.sk|disk\.yandex\.[ru|com])/d/[\w\-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Yadi.sk downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", None)]

    OFFLINE_PATTERN = r"Nothing found"

    API_URL = "https://disk.yandex.ru/public/api/"

    def api_request(self, method, **kwargs):
        post_data = json.dumps(kwargs)
        post_data = re.sub(r'[{":/= ,}]', lambda m: f"%{ord(m.group(0)):2X}", post_data)
        self.req.http.set_header("X-Requested-With", "XMLHttpRequest")
        self.req.http.set_header("Content-Type", "text/plain")
        data = self.load(self.API_URL + method, post=post_data)
        return json.loads(data)

    def get_info(self, url="", html=""):
        info = super(SimpleDownloader, self).get_info(url, html)

        if html:
            m = re.search(
                r'<script type="application/json" id="store-prefetch">(.+?)</script>',
                html,
                re.DOTALL
            )
            if m is not None:
                try:
                    api_data = json.loads(m.group(1))
                    info["sk"] = api_data.get("environment", {}).get("sk")
                    folder_path = [v for k,v in api_data.get("resources", {}).items() if not v.get("children")][0].get("path", "")
                    if folder_path:
                        folder_info = self.api_request("fetch-list", hash=folder_path, offset=0, withSizes=True, sk=info["sk"])
                        files = [f for f in folder_info.get("resources", []) if f.get("type", "") == "file"]
                        info["name"] = files[0]["name"]
                        info["size"] = files[0]["meta"]["size"]
                        info["path"] = files[0]["path"]

                except Exception as exc:
                    info["status"] = 8
                    info["error"] = "Unexpected server response: {}".format(exc)

            else:
                info["status"] = 8
                info["error"] = "could not find required json data"

        return info

    def setup(self):
        self.resume_download = False
        self.multi_dl = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        if any(True for k in ["path", "sk"] if k not in self.info):
            self.error(self._("Missing JSON data"))

        api_data = self.api_request("download-url", inline=False, hash=self.info["path"], sk=self.info["sk"])
        self.link = api_data.get("data", {}).get("url")
