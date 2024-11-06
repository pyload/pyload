# -*- coding: utf-8 -*-

# TODO refactor with AntiCaptcha

import base64
import json
import time
import urllib.parse

from pyload.core.utils.convert import to_str

from ..base.addon import BaseAddon, threaded
from .AntiCaptcha import AntiCaptcha


# based on
# pyload/src/pyload/plugins/addons/AntiCaptcha.py
# jdownloader/src/org/jdownloader/captcha/v2/challenge/cutcaptcha/CutCaptchaChallenge.java

class TwoCaptcha(BaseAddon):
    __name__ = "TwoCaptcha"
    __type__ = "addon"
    __version__ = "0.1"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("check_client", "bool", "Don't use if client is connected", False),
        *map(lambda captcha_plugin: (
            f"solve_{captcha_plugin}",
            "bool",
            f"Solve {captcha_plugin}",
            True,
        #), TASK_TYPES.keys()), # FIXME make this work
        ), (
            #"ReCaptcha",
            #"HCaptcha",
            "CutCaptcha",
        )),
        (
            "refund",
            "bool",
            "Request refund if result incorrect",
            False,
        ),
        # example: 0123456789abcdef0123456789abcdef
        ("passkey", "password", "API key", ""),
        ("timeout", "int", "Timeout in seconds (min 60, max 3999)", "900"),
    ]

    __description__ = """Send captchas to 2captcha.com"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    TASK_TYPES = {
        "image": "ImageToTextTask",
        #"ReCaptcha": "RecaptchaV2TaskProxyless",
        #"HCaptcha": "HCaptchaTaskProxyless",
        "CutCaptcha": "CutCaptchaTaskProxyless",
    }

    # https://2captcha.com/api-docs
    API_URL = "https://api.2captcha.com/"

    # credit = price for 1000 captchas
    # https://2captcha.com/pricing
    MIN_CREDITS = 0.5

    def api_request(self, method, post):
        json_data = self.load(self.API_URL + method, post=json.dumps(post))
        return json.loads(json_data)

    def get_credits(self):
        credits = self.db.retrieve("credits", {"balance": 0, "time": 0})

        #: Docs says: "Please don't call this method more often than once in 30 seconds"
        if time.time() - credits["time"] >= 30:
            api_data = self.api_request(
                "getBalance", {"clientKey": self.config.get("passkey")}
            )
            if api_data["errorId"] != 0:
                self.log_error(self._("API error"), api_data["errorDescription"])
                return 0

            credits = {"balance": api_data["balance"], "time": time.time()}
            self.db.store("credits", credits)

        balance = credits["balance"]
        self.log_info(self._("Credits left: {:.2f}$").format(balance))

        # 1 credit = 0.001 usd
        # credit = price for 1000 captchas
        # https://2captcha.com/pricing
        credits = round(balance * 1000)

        return credits

    @threaded
    def _process_captcha(self, task):
        url_p = urllib.parse.urlparse(task.captcha_params["url"])
        #if not task.is_textual(): # TODO is this the same?
        if task.is_interactive():
            if url_p.scheme not in ("http", "https"):
                self.log_error(self._("Invalid url"))
                return
            task_args = dict(task.captcha_params)
            for key in ["url", "plugin", "captcha_plugin"]:
                del task_args[key]
            self.log_debug("TwoCaptcha: task_args = " + json.dumps(task_args, indent=2))
            api_data = self.api_request(
                "createTask",
                {
                    "clientKey": self.config.get("passkey"),
                    "task": {
                        "type": self.TASK_TYPES[task.captcha_params["captcha_plugin"]],
                        "websiteURL": r"{}://{}/".format(url_p.scheme, url_p.netloc),
                        #"isInvisible": task.is_invisible(),
                        **task_args,
                    },
                },
            )
        else:
            try:
                with open(task.captcha_params["file"], mode="rb") as fp:
                    data = fp.read()

            except IOError as exc:
                self.log_error(exc)
                return

            # https://2captcha.com/api-docs/normal-captcha
            api_data = self.api_request(
                "createTask",
                {
                    "clientKey": self.config.get("passkey"),
                    "task": {
                        "type": "ImageToTextTask",
                        "body": to_str(base64.b64encode(data)),
                        "case": True,
                        #"websiteURL": r"{}://{}/".format(url_p.scheme, url_p.netloc),
                    },
                },
            )
        if api_data["errorId"] != 0:
            task.error = api_data["errorDescription"]
            self.log_error(self._("API error"), api_data["errorDescription"])
            return

        ticket = api_data["taskId"]
        self.log_debug(
            f"NewCaptchaID ticket: {ticket}",
            task.captcha_params.get("file", ""),
        )

        task.data["ticket"] = ticket

        result = None
        for _ in range(int(self.config.get("timeout") // 5)):
            api_data = self.api_request(
                "getTaskResult",
                {"clientKey": self.config.get("passkey"), "taskId": ticket},
            )
            self.log_debug("api_data = " + json.dumps(api_data, indent=2))
            if api_data["errorId"] != 0:
                task.error = api_data["errorDescription"]
                self.log_error(self._("API error"), api_data["errorDescription"])
                break
            if api_data["status"] == "ready":
                #result = self._result_of_api_data(api_data, task)
                # FIXME result == None
                self.log_info(f"AntiCaptcha._result_of_api_data = {AntiCaptcha._result_of_api_data}")
                self.log_info(f"api_data = {api_data}")
                self.log_info(f"task = {task}")
                result = AntiCaptcha._result_of_api_data(self, api_data, task)
                self.log_info(f"result = {result}")
                break
            assert api_data["status"] == "processing"
            time.sleep(5)
        else:
            self.log_debug(f"Could not get result: {ticket}")
        self.log_info(self._("Captcha result for ticket {}: {}").format(ticket, result))
        task.set_result(result)

    def captcha_task(self, task):
        self.log_info(f"captcha_task {task}")
        if task.is_interactive():
            captcha_plugin = task.captcha_params["captcha_plugin"]
            if not self.config.get(f"solve_{captcha_plugin}"):
                self.log_debug(f"Not solving {captcha_plugin}")
                return
        else:
            if not task.is_textual():
                return
            elif not self.config.get("solve_image"):
                return

        if not self.config.get("passkey"):
            return

        if self.pyload.is_client_connected() and self.config.get("check_client"):
            return

        credits = self.get_credits()
        if credits < self.MIN_CREDITS:
            self.log_error(
                self._(f"Your captcha anti-captcha.com account has not enough credits: {credits}")
            )
            return

        timeout = min(max(self.config.get("timeout"), 300), 3999)
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

        if not self.config.get("refund", False) or correct:
            return

        if task.captcha_params["captcha_plugin"] == "ReCaptcha":
            method = "reportIncorrectRecaptcha"
        elif task.is_textual():
            method = "reportIncorrectImageCaptcha"
        else:
            return

        for _ in range(3):
            api_data = self.api_request(
                method,
                {
                    "clientKey": self.config.get("passkey"),
                    "taskId": task.data["ticket"],
                },
            )

            self.log_debug(f"Request {request_type}: {api_data}")
            if api_data["errorId"] == 0:
                break
            time.sleep(5)
        else:
            self.log_debug(
                "Could not send {} request: {}".format(
                    request_type, api_data["errorDescription"]
                )
            )

    def captcha_correct(self, task):
        self.log_info(f"captcha_correct {task}")
        self._captcha_response(task, True)

    def captcha_invalid(self, task):
        self.log_info(f"captcha_invalid {task}")
        self._captcha_response(task, False)
