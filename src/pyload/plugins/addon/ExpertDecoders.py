# -*- coding: utf-8 -*-
import base64
import uuid
from builtins import _

import pycurl
from pyload.network.http_request import BadHeader
from pyload.network.request_factory import getRequest as get_request
from pyload.plugins.internal.addon import Addon
from pyload.plugins.utils import threaded


class ExpertDecoders(Addon):
    __name__ = "ExpertDecoders"
    __type__ = "addon"
    __version__ = "0.12"
    __pyload_version__ = "0.5"
    __status__ = "testing"

    __config__ = [
        ("activated", "bool", "Activated", False),
        ("passkey", "password", "Access key", ""),
        ("check_client", "bool", "Don't use if client is connected", True),
    ]

    __description__ = """Send captchas to expertdecoders.com"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"), ("zoidberg", "zoidberg@mujmail.cz")]

    API_URL = "http://www.fasttypers.org/imagepost.ashx"

    def get_credits(self):
        res = self.load(
            self.API_URL, post={"key": self.config.get("passkey"), "action": "balance"}
        )

        if res.isdigit():
            self.log_info(_("{} credits left").format(res))
            self.info["credits"] = credits = int(res)
            return credits
        else:
            self.log_error(res)
            return 0

    @threaded
    def _process_captcha(self, task):
        task.data["ticket"] = ticket = uuid.uuid4()
        result = None

        with open(task.captchaParams["file"], "rb") as f:
            data = f.read()

        with get_request() as req:
            #: Raise timeout threshold
            req.c.setopt(pycurl.LOW_SPEED_TIME, 80)

            result = self.load(
                self.API_URL,
                post={
                    "action": "upload",
                    "key": self.config.get("passkey"),
                    "file": base64.b64encode(data),
                    "gen_task_id": ticket,
                },
                req=req,
            )

        self.log_debug("Result {} : {}".format(ticket, result))
        task.setResult(result)

    def captcha_task(self, task):
        if not task.isTextual():
            return False

        if not self.config.get("passkey"):
            return False

        if self.pyload.isClientConnected() and self.config.get("check_client"):
            return False

        if self.get_credits() > 0:
            task.handler.append(self)
            task.setWaiting(100)
            self._process_captcha(task)

        else:
            self.log_info(_("Your ExpertDecoders Account has not enough credits"))

    def captcha_invalid(self, task):
        if "ticket" in task.data:

            try:
                res = self.load(
                    self.API_URL,
                    post={
                        "action": "refund",
                        "key": self.config.get("passkey"),
                        "gen_task_id": task.data["ticket"],
                    },
                )
                self.log_info(_("Request refund"), res)

            except BadHeader as e:
                self.log_error(_("Could not send refund request"), e)
