# -*- coding: utf-8 -*-

import json
import re
import time

from ..anticaptchas.ReCaptcha import ReCaptcha
from ..base.simple_downloader import SimpleDownloader


class FilepostCom(SimpleDownloader):
    __name__ = "FilepostCom"
    __type__ = "downloader"
    __version__ = "0.41"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:filepost\.com/files|fp\.io)/(?P<ID>[^/]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Filepost.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]

    INFO_PATTERN = r'<input type="text" id="url" value=\'<a href.*?>(?P<N>.+?) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)</a>\' class="inp_text"/>'
    OFFLINE_PATTERN = r'class="error_msg_title"> Invalid or Deleted File. </div>|<div class="file_info file_info_deleted">'

    PREMIUM_ONLY_PATTERN = r"members only. Please upgrade to premium|a premium membership is required to download this file"
    RECAPTCHA_PATTERN = r"Captcha.init\({\s*key:\s*\'(.+?)\'"
    FLP_TOKEN_PATTERN = r"set_store_options\({token: \'(.+?)\'"

    def handle_free(self, pyfile):
        m = re.search(self.FLP_TOKEN_PATTERN, self.data)
        if m is None:
            self.error(self._("Token"))
        flp_token = m.group(1)

        m = re.search(self.RECAPTCHA_PATTERN, self.data)
        if m is None:
            self.error(self._("Captcha key"))
        captcha_key = m.group(1)

        #: Get wait time
        get_dict = {
            "SID": self.req.cj.get_cookie("SID"),
            "JsHttpRequest": str(int(time.time() * 10000)) + "-xml",
        }
        post_dict = {
            "action": "set_download",
            "token": flp_token,
            "code": self.info["pattern"]["ID"],
        }
        wait_time = int(self.get_json_response(get_dict, post_dict, "wait_time"))

        if wait_time > 0:
            self.wait(wait_time)

        post_dict = {
            "token": flp_token,
            "code": self.info["pattern"]["ID"],
            "file_pass": "",
        }

        if "var is_pass_exists = true;" in self.data:
            #: Solve password
            password = self.get_password()
            if password:
                self.log_info(self._("Password protected link, trying ") + password)

                get_dict["JsHttpRequest"] = str(int(time.time() * 10000)) + "-xml"
                post_dict["file_pass"] = password

                self.link = self.get_json_response(get_dict, post_dict, "link")

                if not self.link:
                    self.fail(self._("Wrong password"))
            else:
                self.fail(self._("No password found"))

        else:
            get_dict["JsHttpRequest"] = str(int(time.time() * 10000)) + "-xml"
            self.link = self.get_json_response(get_dict, post_dict, "link")

            if not self.link:
                #: Solve ReCaptcha
                self.captcha = ReCaptcha(pyfile)
                (
                    post_dict["recaptcha_response_field"],
                    post_dict["recaptcha_challenge_field"],
                ) = self.captcha.challenge(captcha_key)
                self.link = self.get_json_response(get_dict, post_dict, "link")

    def get_json_response(self, get_dict, post_dict, field):
        html = self.load(
            "https://filepost.com/files/get/", get=get_dict, post=post_dict
        )
        res = json.loads(html)

        self.log_debug(res)

        if "js" not in res:
            self.error(self._("JSON {} 1").format(field))

        #: I changed js_answer to res['js'] since js_answer is nowhere set.
        #: I don't know the JSON-HTTP specs in detail, but the previous author
        #: Accessed res['js']['error'] as well as js_answer['error'].
        #: See the two lines commented out with  "# ~?".
        if "error" in res["js"]:

            if res["js"]["error"] == "download_delay":
                self.retry(wait=res["js"]["params"]["next_download"])
                #: ~? self.retry(wait=js_answer['params']['next_download'])

            elif (
                "Wrong file password" in res["js"]["error"]
                or "You entered a wrong CAPTCHA code" in res["js"]["error"]
                or "CAPTCHA Code nicht korrekt" in res["js"]["error"]
            ):
                return None

            elif "CAPTCHA" in res["js"]["error"]:
                self.log_debug("Error response is unknown, but mentions CAPTCHA")
                return None

            else:
                self.fail(res["js"]["error"])

        if "answer" not in res["js"] or field not in res["js"]["answer"]:
            self.error(self._("JSON {} 2").format(field))

        return res["js"]["answer"][field]
