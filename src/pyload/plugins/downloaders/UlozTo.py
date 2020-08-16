# -*- coding: utf-8 -*-

import json
import os
import re
from datetime import timedelta

import pycurl
from pyload.core.utils import parse

from ..base.simple_downloader import SimpleDownloader
from ..helpers import timestamp


def convert_decimal_prefix(m):
    #: Decimal prefixes used in filesize and traffic
    return (
        "%%.%df" % {"k": 3, "M": 6, "G": 9}[m.group(2)] % float(m.group(1))
    ).replace(".", "")


class UlozTo(SimpleDownloader):
    __name__ = "UlozTo"
    __type__ = "downloader"
    __version__ = "1.42"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz)/(?:live/)?(?P<ID>[!\w]+/[^/?]*)"

    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("captcha", "Image;Sound", "Captcha recognition", "Image"),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Uloz.to downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("ondrej", "git@ondrej.it"),
        ("astran", "martin.hromadko@gmail.com"),
    ]

    NAME_PATTERN = r"(<p>File <strong>|<title>)(?P<N>.+?)(<| \|)"
    SIZE_PATTERN = r'<span id="fileSize">.*?(?P<S>[\d.,]+\s[kMG]?B)</span>'
    OFFLINE_PATTERN = r'<title>404 - Page not found</title>|<h1 class="h1">File (has been deleted|was banned)</h1>'

    URL_REPLACEMENTS = [
        ("http://", "https://"),
        (
            r"(uloz\.to|ulozto\.(cz|sk|net)|bagruj\.cz|zachowajto\.pl|pornfile\.cz)",
            "ulozto.net",
        ),
    ]

    SIZE_REPLACEMENTS = [(r"([\d.]+)\s([kMG])B", convert_decimal_prefix)]

    CHECK_TRAFFIC = True

    ADULT_PATTERN = r"PORNfile.cz"
    PASSWD_PATTERN = r'<div class="passwordProtectedFile">'
    VIPLINK_PATTERN = r'<a href=".+?\?disclaimer=1" class="linkVip">'
    TOKEN_PATTERN = r'<input type="hidden" name="_token_" .*?value="(.+?)"'

    def setup(self):
        self.chunk_limit = 16 if self.premium else 1
        self.multi_dl = True
        self.resume_download = True

    def adult_confirmation(self, pyfile):
        if re.search(self.ADULT_PATTERN, self.data):
            adult = True
            self.log_info(self._("Adult content confirmation needed"))

            url = pyfile.url.replace("ulozto.net", "pornfile.cz")
            self.load(
                "https://pornfile.cz/porn-disclaimer",
                post={"agree": "Confirm", "_do": "pornDisclaimer-submit"},
            )

            html = self.load(url)
            name = re.search(self.NAME_PATTERN, html).group(2)

            self.pyfile.name = parse.name(name)
            self.data = html

        else:
            adult = False

        return adult

    def handle_free(self, pyfile):
        is_adult = self.adult_confirmation(pyfile)

        action, inputs = self.parse_html_form(
            'id="frm-download-freeDownloadTab-freeDownloadForm"'
        )
        if not action or not inputs:
            self.error(self._("Free download form not found"))

        input_keys = list(inputs.keys())
        self.log_debug(f"inputs.keys = {input_keys}")
        #: Get and decrypt captcha
        if all(key in inputs for key in ("captcha_value", "captcha_id", "captcha_key")):
            #: Old version - last seen 9.12.2013
            self.log_debug('Using "old" version')

            captcha_id = inputs["captcha_id"]
            captcha_value = self.captcha.decrypt(
                f"https://img.uloz.to/captcha/{captcha_id}.png"
            )
            self.log_debug(f"CAPTCHA ID: {captcha_id}, CAPTCHA VALUE: {captcha_value}")

            inputs.update(
                {
                    "captcha_id": inputs["captcha_id"],
                    "captcha_key": inputs["captcha_key"],
                    "captcha_value": captcha_value,
                }
            )

        elif all(
            key in inputs for key in ("captcha_value", "timestamp", "salt", "hash")
        ):
            #: New version - better to get new parameters (like captcha reload) because of image url - since 6.12.2013
            self.log_debug('Using "new" version')

            xapca = self.load(
                "https://ulozto.net/reloadXapca.php", get={"rnd": timestamp()}
            )

            xapca = xapca.replace('sound":"', 'sound":"https:').replace(
                'image":"', 'image":"https:'
            )
            self.log_debug(f"xapca: {xapca}")

            data = json.loads(xapca)
            if self.config.get("captcha") == "Sound":
                captcha_value = self.captcha.decrypt(
                    str(data["sound"]),
                    input_type=os.path.splitext(data["sound"])[1],
                    ocr="UlozTo",
                )
            else:
                captcha_value = self.captcha.decrypt(data["image"])
            self.log_debug(
                "CAPTCHA HASH: " + data["hash"],
                "CAPTCHA SALT: " + data["salt"],
                "CAPTCHA VALUE: " + captcha_value,
            )

            inputs.update(
                {
                    "timestamp": data["timestamp"],
                    "salt": data["salt"],
                    "hash": data["hash"],
                    "captcha_value": captcha_value,
                }
            )

        elif all(
            key in inputs
            for key in ("do", "cid", "ts", "sign", "_token_", "sign_a", "adi")
        ):
            # New version 1.4.2016
            self.log_debug('Using "new" > 1.4.2016')

            inputs.update(
                {
                    "do": inputs["do"],
                    "_token_": inputs["_token_"],
                    "ts": inputs["ts"],
                    "cid": inputs["cid"],
                    "adi": inputs["adi"],
                    "sign_a": inputs["sign_a"],
                    "sign": inputs["sign"],
                }
            )

        else:
            self.error(self._("CAPTCHA form changed"))

        domain = "https://pornfile.cz" if is_adult else "https://ulozto.net"
        jsvars = self.get_json_response(domain + action, inputs)
        self.download(jsvars["url"])

    def handle_premium(self, pyfile):
        self.adult_confirmation(pyfile)
        self.download(pyfile.url, get={"do": "directDownload"})

    def check_errors(self):
        if self.PASSWD_PATTERN in self.data:
            password = self.get_password()

            if password:
                self.log_info(self._("Password protected link, trying ") + password)
                self.data = self.load(
                    self.pyfile.url,
                    get={"do": "passwordProtectedForm-submit"},
                    post={"password": password, "password_send": "Send"},
                )

                if self.PASSWD_PATTERN in self.data:
                    self.fail(self._("Wrong password"))
            else:
                self.fail(self._("No password found"))

        if re.search(self.VIPLINK_PATTERN, self.data):
            self.data = self.load(self.pyfile.url, get={"disclaimer": "1"})

        return SimpleDownloader.check_errors(self)

    def check_download(self):
        check = self.scan_download(
            {
                "wrong_captcha": ">An error ocurred while verifying the user",
                "offline": re.compile(self.OFFLINE_PATTERN),
                "passwd": self.PASSWD_PATTERN,
                #: Paralell dl, server overload etc.
                "server_error": "<h1>Z Tvého počítače se již stahuje",
                "not_found": "<title>Ulož.to</title>",
            }
        )

        if check == "wrong_captcha":
            self.captcha.invalid()
            self.retry(msg=self._("Wrong captcha code"))

        elif check == "offline":
            self.offline()

        elif check == "passwd":
            self.fail(self._("Wrong password"))

        elif check == "server_error":
            self.log_error(self._("Server error, try downloading later"))
            self.multi_dl = False
            self.wait(timedelta(hours=1).seconds, True)
            self.retry()

        elif check == "not_found":
            self.fail(self._("Server error, file not downloadable"))

        return SimpleDownloader.check_download(self)

    def get_json_response(self, url, inputs):
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])

        res = self.load(url, post=inputs, ref=self.pyfile.url)
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With:"])

        if not res.startswith("{"):
            self.retry(msg=self._("Something went wrong"))

        jsonres = json.loads(res)
        if jsonres["status"] == "error" and "new_captcha_data" in jsonres:
            self.captcha.invalid()
            self.retry(msg=self._("Wrong captcha code"))

        self.log_debug(url, res)
        return jsonres
