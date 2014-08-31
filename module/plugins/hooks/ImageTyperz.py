# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from base64 import b64encode
from pycurl import FORM_FILE, LOW_SPEED_TIME
from thread import start_new_thread

from module.network.RequestFactory import getURL, getRequest
from module.plugins.Hook import Hook


class ImageTyperzException(Exception):

    def __init__(self, err):
        self.err = err

    def getCode(self):
        return self.err

    def __str__(self):
        return "<ImageTyperzException %s>" % self.err

    def __repr__(self):
        return "<ImageTyperzException %s>" % self.err


class ImageTyperz(Hook):
    __name__ = "ImageTyperz"
    __type__ = "hook"
    __version__ = "0.04"

    __config__ = [("activated", "bool", "Activated", False),
                  ("username", "str", "Username", ""),
                  ("passkey", "password", "Password", ""),
                  ("force", "bool", "Force IT even if client is connected", False)]

    __description__ = """Send captchas to ImageTyperz.com"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    SUBMIT_URL = "http://captchatypers.com/Forms/UploadFileAndGetTextNEW.ashx"
    RESPOND_URL = "http://captchatypers.com/Forms/SetBadImage.ashx"
    GETCREDITS_URL = "http://captchatypers.com/Forms/RequestBalance.ashx"


    def setup(self):
        self.info = {}

    def getCredits(self):
        response = getURL(self.GETCREDITS_URL, post={"action": "REQUESTBALANCE", "username": self.getConfig("username"),
                                                     "password": self.getConfig("passkey")})

        if response.startswith('ERROR'):
            raise ImageTyperzException(response)

        try:
            balance = float(response)
        except:
            raise ImageTyperzException("invalid response")

        self.logInfo("Account balance: $%s left" % response)
        return balance

    def submit(self, captcha, captchaType="file", match=None):
        req = getRequest()
        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            #workaround multipart-post bug in HTTPRequest.py
            if re.match("^[A-Za-z0-9]*$", self.getConfig("passkey")):
                multipart = True
                data = (FORM_FILE, captcha)
            else:
                multipart = False
                with open(captcha, 'rb') as f:
                    data = f.read()
                data = b64encode(data)

            response = req.load(self.SUBMIT_URL, post={"action": "UPLOADCAPTCHA",
                                                       "username": self.getConfig("username"),
                                                       "password": self.getConfig("passkey"), "file": data},
                                                       multipart=multipart)
        finally:
            req.close()

        if response.startswith("ERROR"):
            raise ImageTyperzException(response)
        else:
            data = response.split('|')
            if len(data) == 2:
                ticket, result = data
            else:
                raise ImageTyperzException("Unknown response %s" % response)

        return ticket, result

    def newCaptchaTask(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.getConfig("username") or not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logInfo("Your %s account has not enough credits" % self.__name__)

    def captchaInvalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            response = getURL(self.RESPOND_URL, post={"action": "SETBADIMAGE", "username": self.getConfig("username"),
                                                      "password": self.getConfig("passkey"),
                                                      "imageid": task.data['ticket']})

            if response == "SUCCESS":
                self.logInfo("Bad captcha solution received, requested refund")
            else:
                self.logError("Bad captcha solution received, refund request failed", response)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except ImageTyperzException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
