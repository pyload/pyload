import base64
import time
import urllib.parse

from pyload.core.utils.convert import to_str

from ..base.addon import BaseAddon, threaded


class CaptchaAIException(Exception):

    def init(self, err):
        self.err = err

    def get_code(self):
        return self.err

    def str(self):
        return "<CaptchaAIException {}>".format(self.err)

    def repr(self):
        return "<CaptchaAIException {}>".format(self.err)


class CaptchaAI(BaseAddon):

    name = "CaptchaAI"
    type = "addon"
    version = "0.01"
    status = "testing"

    config = [
        ("enabled", "bool", "Activated", False),
        ("check_client", "bool", "Don't use if client is connected", True),
        ("solve_image", "bool", "Solve image captcha", True),
        ("solve_recaptcha", "bool", "Solve ReCaptcha", True),
        ("solve_turnstile", "bool", "Solve Turnstile", True),
        ("refund", "bool", "Report bad result (refund) if result incorrect", False),
        ("api_url", "str", "API base URL", "https://ocr.captchaai.com"),
        ("passkey", "password", "API key", ""),
        ("timeout", "int", "Timeout in seconds (min 60, max 3999)", "900"),
    ]

    description = """Send captchas to captchaai.com"""
    license = "GPLv3"
    authors = [
        ("CaptchaAI", "support@captchaai.com"),
    ]

    #: Maps pyLoad's captcha plugin name to the in.php method parameter.
    #: See https://docs.captchaai.com/ (2Captcha-compatible in.php/res.php API)
    CAPTCHA_METHODS = {
        "ReCaptcha": "userrecaptcha",
        "Turnstile": "turnstile",
    }

    API_URL = "https://ocr.captchaai.com"

    def api_response(self, res):
        """
        Parse a plaintext in.phpres.php response and raise on
        any ERROR_* / CAPCHA_* status returned by the service.
        """
        res = res.strip()
        if res.startswith("OK|"):
            return res[3:]
        elif res in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
            return None
        else:
            raise CaptchaAIException(res)

    def api_request(self, endpoint, get):
        api_url = self.config.get("api_url") or self.API_URL
        api_url = api_url.rstrip("/")
        res = self.load("{}/{}".format(api_url, endpoint), get=get)
        return self.api_response(res)

    def get_credits(self):
        try:
            res = self.api_request(
                "res.php",
                {"key": self.config.get("passkey"), "action": "getbalance"},
            )
            balance = float(res)
        except (CaptchaAIException, TypeError, ValueError) as exc:
            self.log_error(self._("Could not retrieve balance"), exc)
            return 0
        self.log_info(self._("Credits left: {:.2f}$").format(balance))
        return balance

    @threaded
    def processcaptcha(self, task):
        captcha_plugin = task.captcha_params["captcha_plugin"]

        if task.is_interactive():
            url_p = urllib.parse.urlparse(task.captcha_params["url"])
            if url_p.scheme not in ("http", "https"):
                self.log_error(self._("Invalid url"))
                return

            get = {
                "key": self.config.get("passkey"),
                "method": self.CAPTCHA_METHODS[captcha_plugin],
                "pageurl": r"{}://{}/".format(url_p.scheme, url_p.netloc),
                "soft_id": 5403,
            }

            if captcha_plugin == "ReCaptcha":
                get["googlekey"] = task.captcha_params["sitekey"]
                if task.is_invisible():
                    get["invisible"] = 1
            elif captcha_plugin == "Turnstile":
                get["sitekey"] = task.captcha_params["sitekey"]

        else:
            try:
                with open(task.captcha_params["file"], mode="rb") as fp:
                    data = fp.read()
            except IOError as exc:
                self.log_error(exc)
                return

            get = {
                "key": self.config.get("passkey"),
                "method": "base64",
                "body": to_str(base64.b64encode(data)),
                "soft_id": 5403,
            }

        try:
            ticket = self.api_request("in.php", get)
        except CaptchaAIException as exc:
            task.error = exc.get_code()
            self.log_error(self._("API error"), exc)
            return

        self.log_debug(
            f"NewCaptchaID ticket: {ticket}",
            task.captcha_params.get("file", ""),
        )

        task.data["ticket"] = ticket

        result = None
        for _ in range(int(self.config.get("timeout") // 5)):
            time.sleep(5)
            try:
                result = self.api_request(
                    "res.php",
                    {
                        "key": self.config.get("passkey"),
                        "action": "get",
                        "id": ticket,
                    },
                )
            except CaptchaAIException as exc:
                task.error = exc.get_code()
                self.log_error(self._("API error"), exc)
                break

            if result is not None:
                break
        else:
            self.log_debug(f"Could not get result: {ticket}")

        self.log_info(self._("Captcha result for ticket {}: {}").format(ticket, result))
        task.set_result(result)

    def captcha_task(self, task):
        if task.is_interactive():
            captcha_plugin = task.captcha_params["captcha_plugin"]

            if captcha_plugin not in self.CAPTCHA_METHODS:
                return
            elif captcha_plugin == "ReCaptcha" and not self.config.get(
                "solve_recaptcha"
            ):
                return
            elif captcha_plugin == "Turnstile" and not self.config.get(
                "solve_turnstile"
            ):
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
        if credits < 0.05:
            self.log_error(self._("Your captchaai.com account has not enough credits"))
            return

        timeout = min(max(self.config.get("timeout"), 300), 3999)
        task.handler.append(self)
        task.set_waiting(timeout)
        self._process_captcha(task)

    def captcharesponse(self, task, correct):
        request_type = "correct" if correct else "refund"
        if "ticket" not in task.data:
            self.log_debug(
                "No CaptchaID for {} request (task: {})".format(request_type, task)
            )
            return

        if not self.config.get("refund", False) or correct:
            return

        try:
            self.api_request(
                "res.php",
                {
                    "key": self.config.get("passkey"),
                    "action": "reportbad",
                    "id": task.data["ticket"],
                },
            )
        except CaptchaAIException as exc:
            self.log_debug("Could not send {} request: {}".format(request_type, exc))

    def captcha_correct(self, task):
        self._captcha_response(task, True)

    def captcha_invalid(self, task):
        self._captcha_response(task, False)
