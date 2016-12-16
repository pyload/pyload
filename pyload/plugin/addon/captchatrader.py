# -*- coding: utf-8 -*-
#@author: mkaay, RaNaN

from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str
from _thread import start_new_thread
from pycurl import FORM_FILE, LOW_SPEED_TIME

from pyload.common.json_layer import json_loads
from pyload.network.requestfactory import get_url, get_request
from pyload.network.httprequest import BadHeader
from pyload.plugin.hook import Hook

PYLOAD_KEY = "9f65e7f381c3af2b076ea680ae96b0b7"


class CaptchaTraderException(Exception):
    def __init__(self, err):
        self.err = err

    def get_code(self):
        return self.err

    def __str__(self):
        return "<CaptchaTraderException %s>" % self.err

    def __repr__(self):
        return "<CaptchaTraderException %s>" % self.err


class CaptchaTrader(Hook):
    __name__ = "CaptchaTrader"
    __version__ = "0.16"
    __description__ = """Send captchas to captchatrader.com"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("username", "str", "Username", ""),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Password", "")]
    __author_name__ = "RaNaN"
    __author_mail__ = "Mast3rRaNaN@hotmail.de"

    SUBMIT_URL = "http://api.captchatrader.com/submit"
    RESPOND_URL = "http://api.captchatrader.com/respond"
    GETCREDITS_URL = "http://api.captchatrader.com/get_credits/username:%(user)s/password:%(password)s/"

    def setup(self):
        self.info = {}

    def get_credits(self):
        json = get_url(CaptchaTrader.GETCREDITS_URL % {"user": self.get_config("username"),
                                                      "password": self.get_config("passkey")})
        response = json_loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])
        else:
            self.log_info(_("%s credits left") % response[1])
            self.info["credits"] = response[1]
            return response[1]

    def submit(self, captcha, captchaType="file", match=None):
        if not PYLOAD_KEY:
            raise CaptchaTraderException("No API Key Specified!")

        #if type(captcha) == str and captchaType == "file":
        #    raise CaptchaTraderException("Invalid Type")
        assert captchaType in ("file", "url-jpg", "url-jpeg", "url-png", "url-bmp")

        req = get_request()

        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            json = req.load(CaptchaTrader.SUBMIT_URL, post={"api_key": PYLOAD_KEY,
                                                            "username": self.get_config("username"),
                                                            "password": self.get_config("passkey"),
                                                            "value": (FORM_FILE, captcha),
                                                            "type": captchaType}, multipart=True)
        finally:
            req.close()

        response = json_loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])

        ticket = response[0]
        result = response[1]
        self.log_debug("result %s : %s" % (ticket, result))

        return ticket, result

    def respond(self, ticket, success):
        try:
            json = get_url(CaptchaTrader.RESPOND_URL, post={"is_correct": 1 if success else 0,
                                                           "username": self.get_config("username"),
                                                           "password": self.get_config("passkey"),
                                                           "ticket": ticket})

            response = json_loads(json)
            if response[0] < 0:
                raise CaptchaTraderException(response[1])

        except BadHeader as e:
            self.log_error(_("Could not send response."), str(e))

    def new_captcha_task(self, task):
        if not task.isTextual():
            return False

        if not self.get_config("username") or not self.get_config("passkey"):
            return False

        if self.pyload.is_client_connected() and not self.get_config("force"):
            return False

        if self.get_credits() > 10:
            task.handler.append(self)
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.log_info(_("Your CaptchaTrader Account has not enough credits"))

    def captcha_correct(self, task):
        if "ticket" in task.data:
            ticket = task.data["ticket"]
            self.respond(ticket, True)

    def captcha_invalid(self, task):
        if "ticket" in task.data:
            ticket = task.data["ticket"]
            self.respond(ticket, False)

    def process_captcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaTraderException as e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)
