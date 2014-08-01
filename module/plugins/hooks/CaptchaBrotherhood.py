# -*- coding: utf-8 -*-

from __future__ import with_statement

import StringIO
import pycurl

from PIL import Image
from thread import start_new_thread
from time import sleep
from urllib import urlencode

from module.network.RequestFactory import getURL, getRequest
from module.plugins.Hook import Hook


class CaptchaBrotherhoodException(Exception):

    def __init__(self, err):
        self.err = err

    def getCode(self):
        return self.err

    def __str__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err

    def __repr__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err


class CaptchaBrotherhood(Hook):
    __name__ = "CaptchaBrotherhood"
    __type__ = "hook"
    __version__ = "0.05"

    __config__ = [("activated", "bool", "Activated", False),
                  ("username", "str", "Username", ""),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Password", "")]

    __description__ = """Send captchas to CaptchaBrotherhood.com"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    API_URL = "http://www.captchabrotherhood.com/"


    def setup(self):
        self.info = {}

    def getCredits(self):
        response = getURL(self.API_URL + "askCredits.aspx",
                          get={"username": self.getConfig("username"), "password": self.getConfig("passkey")})
        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException(response)
        else:
            credits = int(response[3:])
            self.logInfo(_("%d credits left") % credits)
            self.info['credits'] = credits
            return credits

    def submit(self, captcha, captchaType="file", match=None):
        try:
            img = Image.open(captcha)
            output = StringIO.StringIO()
            self.logDebug("CAPTCHA IMAGE", img, img.format, img.mode)
            if img.format in ("GIF", "JPEG"):
                img.save(output, img.format)
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output, "JPEG")
            data = output.getvalue()
            output.close()
        except Exception, e:
            raise CaptchaBrotherhoodException("Reading or converting captcha image failed: %s" % e)

        req = getRequest()

        url = "%ssendNewCaptcha.aspx?%s" % (self.API_URL,
                                            urlencode({"username": self.getConfig("username"),
                                                       "password": self.getConfig("passkey"),
                                                       "captchaSource": "pyLoad",
                                                       "timeout": "80"}))

        req.c.setopt(pycurl.URL, url)
        req.c.setopt(pycurl.POST, 1)
        req.c.setopt(pycurl.POSTFIELDS, data)
        req.c.setopt(pycurl.HTTPHEADER, ["Content-Type: text/html"])

        try:
            req.c.perform()
            response = req.getResponse()
        except Exception, e:
            raise CaptchaBrotherhoodException("Submit captcha image failed")

        req.close()

        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException(response[1])

        ticket = response[3:]

        for _ in xrange(15):
            sleep(5)
            response = self.get_api("askCaptchaResult", ticket)
            if response.startswith("OK-answered"):
                return ticket, response[12:]

        raise CaptchaBrotherhoodException("No solution received in time")

    def get_api(self, api, ticket):
        response = getURL("%s%s.aspx" % (self.API_URL, api),
                          get={"username": self.getConfig("username"),
                               "password": self.getConfig("passkey"),
                               "captchaID": ticket})
        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException("Unknown response: %s" % response)

        return response

    def newCaptchaTask(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.getConfig("username") or not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 10:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))
        else:
            self.logInfo("Your CaptchaBrotherhood Account has not enough credits")

    def captchaInvalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            response = self.get_api("complainCaptcha", task.data['ticket'])

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaBrotherhoodException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
