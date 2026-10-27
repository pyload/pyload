import base64
import json
import time

from pyload.core.utils.convert import to_str

from ..base.addon import BaseAddon, threaded


class Solvecha(BaseAddon):
    __name__ = "Solvecha"
    __type__ = "addon"
    __version__ = "0.01"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("check_client", "bool", "Don't use if client is connected", True),
        ("passkey", "password", "API key", ""),
        ("timeout", "int", "Timeout in seconds (min 60, max 3999)", "900"),
    ]

    __description__ = """Send image captchas to solvecha.com"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Marin Solutions", "support[AT]solvecha[DOT]com"),
    ]

    #: Only image (text) captchas are supported, no token based captchas
    # See https://solvecha.com/docs
    API_URL = "https://api.solvecha.com/"

    POLL_INTERVAL = 2

    def api_request(self, method, post):
        json_data = self.load(self.API_URL + method, post=json.dumps(post))
        return json.loads(json_data)

    def get_credits(self):
        credits = self.db.retrieve("credits", {"balance": 0, "time": 0})

        if time.monotonic() - credits["time"] >= 30:
            api_data = self.api_request(
                "getBalance", {"clientKey": self.config.get("passkey")}
            )
            if api_data["errorId"] != 0:
                self.log_error(self._("API error"), api_data["errorDescription"])
                return 0

            credits = {"balance": api_data["balance"], "time": time.monotonic()}
            self.db.store("credits", credits)

        balance = credits["balance"]
        self.log_info(self._("Credits left: {:.2f}$").format(balance))

        return balance

    @threaded
    def _process_captcha(self, task, timeout):
        try:
            with open(task.captcha_params["file"], mode="rb") as fp:
                data = fp.read()

        except IOError as exc:
            self.log_error(exc)
            return

        api_data = self.api_request(
            "createTask",
            {
                "clientKey": self.config.get("passkey"),
                "task": {
                    "type": "ImageToTextTask",
                    "body": to_str(base64.b64encode(data)),
                },
            },
        )
        if api_data["errorId"] != 0:
            task.error = api_data["errorDescription"]
            self.log_error(self._("API error"), api_data["errorDescription"])
            return

        ticket = api_data["taskId"]
        self.log_debug(f"NewCaptchaID ticket: {ticket}", task.captcha_params["file"])

        task.data["ticket"] = ticket

        result = None
        deadline = time.monotonic() + timeout
        #: createTask may already return the finished solution
        while True:
            if api_data["errorId"] != 0:
                task.error = api_data["errorDescription"]
                self.log_error(self._("API error"), api_data["errorDescription"])
                break

            if api_data.get("status") != "processing":
                result = api_data["solution"]["text"]
                break

            if time.monotonic() >= deadline:
                self.log_debug(f"Could not get result: {ticket}")
                break

            time.sleep(self.POLL_INTERVAL)
            api_data = self.api_request(
                "getTaskResult",
                {"clientKey": self.config.get("passkey"), "taskId": ticket},
            )

        self.log_info(self._("Captcha result for ticket {}: {}").format(ticket, result))

        task.set_result(result)

    def captcha_task(self, task):
        if task.is_interactive() or not task.is_textual():
            return

        if not self.config.get("passkey"):
            return

        if self.pyload.is_client_connected() and self.config.get("check_client"):
            return

        credits = self.get_credits()
        if credits <= 0:
            self.log_error(
                self._("Your captcha solvecha.com account has not enough credits")
            )
            return

        timeout = min(max(int(self.config.get("timeout")), 60), 3999)
        task.handler.append(self)
        task.set_waiting(timeout)

        self._process_captcha(task, timeout)
