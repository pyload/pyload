# -*- coding: utf-8 -*-

import base64
import re
import time
import urllib.parse

from pyload.core.network.http.exceptions import BadHeader

from ..base.addon import BaseAddon, threaded


class Captcha9Kw(BaseAddon):
    __name__ = "Captcha9Kw"
    __type__ = "addon"
    __version__ = "0.46"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("check_client", "bool", "Don't use if client is connected", True),
        ("confirm", "bool", "Confirm Captcha (cost +6 credits)", False),
        ("captchaperhour", "int", "Captcha per hour", "9999"),
        ("captchapermin", "int", "Captcha per minute", "9999"),
        ("prio", "int", "Priority (max 10)(cost +0 -> +10 credits)", "0"),
        ("queue", "int", "Max. Queue (max 999)", "50"),
        (
            "hoster_options",
            "str",
            "Hoster options (format pluginname;prio 1;selfsolve 1;confirm 1;timeout 900|...)",
            "",
        ),
        (
            "selfsolve",
            "bool",
            "Selfsolve (manually solve your captcha in your 9kw client if active)",
            False,
        ),
        (
            "solve_interactive",
            "bool",
            "Solve interactive captcha (cost 30 credits)",
            True,
        ),
        ("passkey", "password", "API key", ""),
        ("timeout", "int", "Timeout in seconds (min 60, max 3999)", "900"),
    ]

    __description__ = """Send captchas to 9kw.eu"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.net"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahho[DOT]com"),
    ]

    API_URL = "https://www.9kw.eu/index.cgi"

    INTERACTIVE_TYPES = {
        "ReCaptcha": "recaptchav2",
        "HCaptcha": "hcaptcha"
    }

    def get_credits(self):
        res = self.load(
            self.API_URL,
            get={
                "apikey": self.config.get("passkey"),
                "pyload": "1",
                "source": "pyload",
                "action": "usercaptchaguthaben",
            },
        )

        if res.isdigit():
            self.log_info(self._("{} credits left").format(res))
            credits = self.info["credits"] = int(res)
            return credits
        else:
            self.log_error(res)
            return 0

    @threaded
    def _process_captcha(self, task):
        pluginname = task.captcha_params["plugin"]
        if task.is_interactive() or task.is_invisible():
            url_p = urllib.parse.urlparse(task.captcha_params["url"])
            if url_p.scheme not in ("http", "https"):
                self.log_error(self._("Invalid url"))
                return

            post_data = {
                "pageurl": "{}://{}/".format(url_p.scheme, url_p.netloc),
                "oldsource": self.INTERACTIVE_TYPES[
                    task.captcha_params["captcha_plugin"]
                ],
                "captchachoice": self.INTERACTIVE_TYPES[
                    task.captcha_params["captcha_plugin"]
                ],
                "isInvisible": "INVISIBLE" if task.is_invisible() else "NORMAL",
                "data-sitekey": task.captcha_params["sitekey"],
                "securetoken": task.captcha_params.get("securetoken", ""),
            }

        else:
            try:
                with open(task.captcha_params["file"], mode="rb") as fp:
                    data = fp.read()

            except IOError as exc:
                self.log_error(exc)
                return

            post_data = {
                "file-upload-01": base64.b64encode(data),
                "oldsource": pluginname,
            }

        option = {
            "min": 2,
            "max": 50,
            "phrase": 0,
            "numeric": 0,
            "case_sensitive": 0,
            "math": 0,
            "prio": min(max(self.config.get("prio"), 0), 10),
            "confirm": self.config.get("confirm"),
            "timeout": min(max(self.config.get("timeout"), 300), 3999),
            "selfsolve": self.config.get("selfsolve"),
            "cph": self.config.get("captchaperhour"),
            "cpm": self.config.get("captchapermin"),
        }

        for opt in self.config.get("hoster_options", "").split("|"):
            if not opt:
                continue

            details = (x.strip() for x in opt.split(";"))

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split(" ")

                if len(hosteroption) < 2 or not hosteroption[1].isdigit():
                    continue

                o = hosteroption[0].lower()
                if o in option:
                    option[o] = hosteroption[1]

            break

        post_data.update(
            {
                "apikey": self.config.get("passkey"),
                "prio": option["prio"],
                "confirm": option["confirm"],
                "maxtimeout": option["timeout"],
                "selfsolve": option["selfsolve"],
                "captchaperhour": option["cph"],
                "captchapermin": option["cpm"],
                "case-sensitive": option["case_sensitive"],
                "min_len": option["min"],
                "max_len": option["max"],
                "phrase": option["phrase"],
                "numeric": option["numeric"],
                "math": option["math"],
                "pyload": 1,
                "source": "pyload",
                "base64": 0 if task.is_interactive() or task.is_invisible() else 1,
                "mouse": 1 if task.is_positional() else 0,
                "interactive": 1 if task.is_interactive() or task.is_invisible() else 0,
                "action": "usercaptchaupload",
            }
        )

        for _ in range(5):
            try:
                res = self.load(self.API_URL, post=post_data)

            except BadHeader as exc:
                res = exc.content
                time.sleep(3)

            else:
                if res and res.isdigit():
                    break

        else:
            self.log_error(self._("Bad request: {}").format(res))
            return

        self.log_debug(
            "NewCaptchaID ticket: {}".format(res), task.captcha_params.get("file", "")
        )

        task.data["ticket"] = res

        for _ in range(int(self.config.get("timeout") // 5)):
            result = self.load(
                self.API_URL,
                get={
                    "apikey": self.config.get("passkey"),
                    "id": res,
                    "pyload": "1",
                    "info": "1",
                    "source": "pyload",
                    "action": "usercaptchacorrectdata",
                },
            )

            if not result or result == "NO DATA":
                time.sleep(5)
            else:
                break

        else:
            self.log_debug(f"Could not send request: {res}")
            result = None

        self.log_info(self._("Captcha result for ticket {}: {}").format(res, result))

        task.set_result(result)

    def captcha_task(self, task):
        if task.is_interactive() or task.is_invisible():
            if task.captcha_params[
                "captcha_plugin"
            ] not in self.INTERACTIVE_TYPES.keys() or not self.config.get(
                "solve_interactive"
            ):
                return
        else:
            if not task.is_textual() and not task.is_positional():
                return

        if not self.config.get("passkey"):
            return

        if self.pyload.is_client_connected() and self.config.get("check_client"):
            return

        credits = self.get_credits()

        if credits <= 0:
            self.log_error(self._("Your captcha 9kw.eu account has not enough credits"))
            return

        max_queue = min(self.config.get("queue"), 999)
        timeout = min(max(self.config.get("timeout"), 300), 3999)
        pluginname = task.captcha_params["plugin"]

        for _ in range(5):
            servercheck = self.load("http://www.9kw.eu/grafik/servercheck.txt")
            if max_queue > int(re.search(r"queue=(\d+)", servercheck).group(1)):
                break

            time.sleep(10)

        else:
            self.log_error(self._("Too many captchas in queue"))
            return

        for opt in self.config.get("hoster_options", "").split("|"):
            if not opt:
                continue

            details = [x.strip() for x in opt.split(":")]

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if (
                    len(hosteroption) > 1
                    and hosteroption[0].lower() == "timeout"
                    and hosteroption[1].isdigit()
                ):
                    timeout = int(hosteroption[1])

            break

        task.handler.append(self)

        task.set_waiting(timeout)

        self._process_captcha(task)

    def _captcha_response(self, task, correct):
        request_type = "correct" if correct else "refund"

        if "ticket" not in task.data:
            self.log_debug(
                "No CaptchaID for {} request (task: {})".format(request_type, task)
            )
            return

        passkey = self.config.get("passkey")

        for _ in range(3):
            res = self.load(
                self.API_URL,
                get={
                    "action": "usercaptchacorrectback",
                    "apikey": passkey,
                    "api_key": passkey,
                    "correct": "1" if correct else "2",
                    "pyload": "1",
                    "source": "pyload",
                    "id": task.data["ticket"],
                },
            )

            self.log_debug(f"Request {request_type}: {res}")

            if res == "OK":
                break

            time.sleep(5)
        else:
            self.log_debug(f"Could not send {request_type} request: {res}")

    def captcha_correct(self, task):
        self._captcha_response(task, True)

    def captcha_invalid(self, task):
        self._captcha_response(task, False)
