# -*- coding: utf-8 -*-
# @author: mkaay, RaNaN

from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str
from _thread import start_new_thread
from pycurl import FORM_FILE, LOW_SPEED_TIME

from pyload.common.json_layer import json_loads
from pyload.network.RequestFactory import getURL, getRequest
from pyload.network.HTTPRequest import BadHeader
from pyload.plugins.Hook import Hook

PYLOAD_KEY = "9f65e7f381c3af2b076ea680ae96b0b7"


class CaptchaTraderException(Exception):
    def __init__(self, err):
        self.err = err

    def getCode(self):
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

    def getCredits(self):
        json = getURL(CaptchaTrader.GETCREDITS_URL % {"user": self.getConfig("username"),
                                                      "password": self.getConfig("passkey")})
        response = json_loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])
        else:
            self.logInfo(_("%s credits left") % response[1])
            self.info["credits"] = response[1]
            return response[1]

    def submit(self, captcha, captchaType="file", match=None):
        if not PYLOAD_KEY:
            raise CaptchaTraderException("No API Key Specified!")

        #if type(captcha) == str and captchaType == "file":
        #    raise CaptchaTraderException("Invalid Type")
        assert captchaType in ("file", "url-jpg", "url-jpeg", "url-png", "url-bmp")

        req = getRequest()

        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            json = req.load(CaptchaTrader.SUBMIT_URL, post={"api_key": PYLOAD_KEY,
                                                            "username": self.getConfig("username"),
                                                            "password": self.getConfig("passkey"),
                                                            "value": (FORM_FILE, captcha),
                                                            "type": captchaType}, multipart=True)
        finally:
            req.close()

        response = json_loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])

        ticket = response[0]
        result = response[1]
        self.logDebug("result %s : %s" % (ticket, result))

        return ticket, result

    def respond(self, ticket, success):
        try:
            json = getURL(CaptchaTrader.RESPOND_URL, post={"is_correct": 1 if success else 0,
                                                           "username": self.getConfig("username"),
                                                           "password": self.getConfig("passkey"),
                                                           "ticket": ticket})

            response = json_loads(json)
            if response[0] < 0:
                raise CaptchaTraderException(response[1])

        except BadHeader as e:
            self.logError(_("Could not send response."), str(e))

    def newCaptchaTask(self, task):
        if not task.isTextual():
            return False

        if not self.getConfig("username") or not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 10:
            task.handler.append(self)
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logInfo(_("Your CaptchaTrader Account has not enough credits"))

    def captchaCorrect(self, task):
        if "ticket" in task.data:
            ticket = task.data["ticket"]
            self.respond(ticket, True)

    def captchaInvalid(self, task):
        if "ticket" in task.data:
            ticket = task.data["ticket"]
            self.respond(ticket, False)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaTraderException as e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)
