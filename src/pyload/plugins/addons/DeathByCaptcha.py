# -*- coding: utf-8 -*-

import base64
import json
import re
import time

import pycurl
from pyload.core.network.http.exceptions import BadHeader
from pyload.core.network.request_factory import get_request

from ..base.addon import BaseAddon, threaded


class DeathByCaptchaException(Exception):
    DBC_ERRORS = {
        "not-logged-in": "Access denied, check your credentials",
        "invalid-credentials": "Access denied, check your credentials",
        "banned": "Access denied, account is suspended",
        "insufficient-funds": "Insufficient account balance to decrypt CAPTCHA",
        "invalid-captcha": "CAPTCHA is not a valid image",
        "service-overload": "CAPTCHA was rejected due to service overload, try again later",
        "invalid-request": "Invalid request",
        "timed-out": "No CAPTCHA solution received in time",
    }

    def __init__(self, err):
        self.err = err

    def get_code(self):
        return self.err

    def get_desc(self):
        if self.err in self.DBC_ERRORS.keys():
            return self.DBC_ERRORS[self.err]
        else:
            return self.err

    def __str__(self):
        return "<DeathByCaptchaException {}>".format(self.err)

    def __repr__(self):
        return "<DeathByCaptchaException {}>".format(self.err)


class DeathByCaptcha(BaseAddon):
    __name__ = "DeathByCaptcha"
    __type__ = "addon"
    __version__ = "0.16"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("username", "str", "Username", ""),
        ("password", "password", "Password", ""),
        ("check_client", "bool", "Don't use if client is connected", True),
    ]

    __description__ = """Send captchas to DeathByCaptcha.com"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"), ("zoidberg", "zoidberg@mujmail.cz")]

    API_URL = "http://api.dbcapi.me/api/"

    def api_response(self, api="captcha", post=False, multipart=False):
        with get_request() as req:
            req.c.setopt(
                pycurl.HTTPHEADER,
                [
                    "Accept: application/json",
                    f"User-Agent: pyLoad {self.pyload.version}",
                ],
            )

            if post:
                if not isinstance(post, dict):
                    post = {}
                post.update(
                    {
                        "username": self.config.get("username"),
                        "password": self.config.get("password"),
                    }
                )

            res = None
            try:
                html = self.load(
                    "{}{}".format(self.API_URL, api),
                    post=post,
                    multipart=multipart,
                    req=req,
                )

                self.log_debug(html)
                res = json.loads(html)

                if "error" in res:
                    raise DeathByCaptchaException(res["error"])
                elif "status" not in res:
                    raise DeathByCaptchaException(str(res))

            except BadHeader as exc:
                if exc.code == 403:
                    raise DeathByCaptchaException("not-logged-in")

                elif exc.code == 413:
                    raise DeathByCaptchaException("invalid-captcha")

                elif exc.code == 503:
                    raise DeathByCaptchaException("service-overload")

                elif exc.code in (400, 405):
                    raise DeathByCaptchaException("invalid-request")

                else:
                    raise

        return res

    def get_credits(self):
        res = self.api_response("user", True)

        if "is_banned" in res and res["is_banned"]:
            raise DeathByCaptchaException("banned")
        elif "balance" in res and "rate" in res:
            self.info.update(res)
        else:
            raise DeathByCaptchaException(res)

    def get_status(self):
        res = self.api_response("status", False)

        if "is_service_overloaded" in res and res["is_service_overloaded"]:
            raise DeathByCaptchaException("service-overload")

    def submit(self, captcha, captcha_type="file", match=None):
        # NOTE: Workaround multipart-post bug in HTTPRequest.py
        if re.match(r"^\w*$", self.config.get("password")):
            multipart = True
            data = (pycurl.FORM_FILE, captcha)
        else:
            multipart = False
            with open(captcha, mode="rb") as fp:
                data = fp.read()
            data = "base64:" + base64.b64encode(data)

        res = self.api_response("captcha", {"captchafile": data}, multipart)

        if "captcha" not in res:
            raise DeathByCaptchaException(res)
        ticket = res["captcha"]

        for _ in range(24):
            time.sleep(5)
            res = self.api_response("captcha/{}".format(ticket), False)
            if res["text"] and res["is_correct"]:
                break
        else:
            raise DeathByCaptchaException("timed-out")

        result = res["text"]
        self.log_debug(f"Result {ticket}: {result}")

        return ticket, result

    def captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.is_textual():
            return False

        if not self.config.get("username") or not self.config.get("password"):
            return False

        if self.pyload.is_client_connected() and self.config.get("check_client"):
            return False

        try:
            self.get_status()
            self.get_credits()
        except DeathByCaptchaException as exc:
            self.log_error(exc)
            return False

        balance, rate = self.info["balance"], self.info["rate"]
        self.log_info(
            self._("Account balance"),
            self._("US${:.3f} ({} captchas left at {:.2f} cents each)").format(
                balance // 100, balance // rate, rate
            ),
        )

        if balance > rate:
            task.handler.append(self)
            task.data["service"] = self.classname
            task.set_waiting(180)
            self._process_captcha(task)

    def captcha_invalid(self, task):
        if task.data["service"] == self.classname and "ticket" in task.data:
            try:
                res = self.api_response(
                    "captcha/{}/report".format(task.data["ticket"]), True
                )

            except DeathByCaptchaException as exc:
                self.log_error(exc)

            except Exception as exc:
                self.log_error(
                    exc,
                    exc_info=self.pyload.debug > 1,
                    stack_info=self.pyload.debug > 2,
                )

    @threaded
    def _process_captcha(self, task):
        c = task.captcha_params["file"]
        try:
            ticket, result = self.submit(c)
        except DeathByCaptchaException as exc:
            task.error = exc.get_code()
            self.log_error(exc)
            return

        task.data["ticket"] = ticket
        task.set_result(result)
