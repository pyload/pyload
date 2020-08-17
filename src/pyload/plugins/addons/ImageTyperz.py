# -*- coding: utf-8 -*-
import base64
import re

import pycurl
from pyload.core.network.request_factory import get_request

from ..base.addon import BaseAddon, threaded


class ImageTyperzException(Exception):
    def __init__(self, err):
        self.err = err

    def get_code(self):
        return self.err

    def __str__(self):
        return "<ImageTyperzException {}>".format(self.err)

    def __repr__(self):
        return "<ImageTyperzException {}>".format(self.err)


class ImageTyperz(BaseAddon):
    __name__ = "ImageTyperz"
    __type__ = "addon"
    __version__ = "0.15"
    __status__ = "testing"

    __config__ = [
        ("enabled", "bool", "Activated", False),
        ("username", "str", "Username", ""),
        ("password", "password", "Password", ""),
        ("check_client", "bool", "Don't use if client is connected", True),
    ]

    __description__ = """Send captchas to ImageTyperz.com"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"), ("zoidberg", "zoidberg@mujmail.cz")]

    SUBMIT_URL = "http://captchatypers.com/Forms/UploadFileAndGetTextNEW.ashx"
    RESPOND_URL = "http://captchatypers.com/Forms/SetBadImage.ashx"
    GETCREDITS_URL = "http://captchatypers.com/Forms/RequestBalance.ashx"

    def get_credits(self):
        res = self.load(
            self.GETCREDITS_URL,
            post={
                "action": "REQUESTBALANCE",
                "username": self.config.get("username"),
                "password": self.config.get("password"),
            },
        )

        if res.startswith("ERROR"):
            raise ImageTyperzException(res)

        try:
            balance = float(res)

        except Exception:
            raise ImageTyperzException("Invalid response")

        self.log_info(self._("Account balance: ${} left").format(res))
        return balance

    def submit(self, captcha, captcha_type="file", match=None):
        with get_request() as req:
            #: Raise timeout threshold
            req.c.setopt(pycurl.LOW_SPEED_TIME, 80)

            # NOTE: Workaround multipart-post bug in HTTPRequest.py
            if re.match(r"^\w*$", self.config.get("password")):
                multipart = True
                data = (pycurl.FORM_FILE, captcha)
            else:
                multipart = False
                with open(captcha, mode="rb") as fp:
                    data = fp.read()
                data = base64.b64encode(data)

            res = self.load(
                self.SUBMIT_URL,
                post={
                    "action": "UPLOADCAPTCHA",
                    "username": self.config.get("username"),
                    "password": self.config.get("password"),
                    "file": data,
                },
                multipart=multipart,
                req=req,
            )

        if res.startswith("ERROR"):
            raise ImageTyperzException(res)
        else:
            data = res.split("|")
            if len(data) == 2:
                ticket, result = data
            else:
                raise ImageTyperzException("Unknown response: {}".format(res))

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

        if self.get_credits() > 0:
            task.handler.append(self)
            task.data["service"] = self.classname
            task.set_waiting(100)
            self._process_captcha(task)

        else:
            self.log_info(self._("Your account has not enough credits"))

    def captcha_invalid(self, task):
        if task.data["service"] == self.classname and "ticket" in task.data:
            res = self.load(
                self.RESPOND_URL,
                post={
                    "action": "SETBADIMAGE",
                    "username": self.config.get("username"),
                    "password": self.config.get("password"),
                    "imageid": task.data["ticket"],
                },
            )

            if res == "SUCCESS":
                self.log_info(self._("Bad captcha solution received, requested refund"))
            else:
                self.log_error(
                    self._("Bad captcha solution received, refund request failed"), res
                )

    @threaded
    def _process_captcha(self, task):
        c = task.captcha_params["file"]
        try:
            ticket, result = self.submit(c)
        except ImageTyperzException as exc:
            task.error = exc.get_code()
            return

        task.data["ticket"] = ticket
        task.set_result(result)
