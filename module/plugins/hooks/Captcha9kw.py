# -*- coding: utf-8 -*-

from __future__ import with_statement

import time

from base64 import b64encode
from thread import start_new_thread

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL
from module.plugins.Hook import Hook


class Captcha9kw(Hook):
    __name__ = "Captcha9kw"
    __type__ = "hook"
    __version__ = "0.09"

    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force CT even if client is connected", True),
                  ("https", "bool", "Enable HTTPS", False),
                  ("confirm", "bool", "Confirm Captcha (Cost +6)", False),
                  ("captchaperhour", "int", "Captcha per hour (max. 9999)", 9999),
                  ("prio", "int", "Prio 1-10 (Cost +1-10)", 0),
                  ("selfsolve", "bool",
                   "If enabled and you have a 9kw client active only you will get your captcha to solve it (Selfsolve)",
                   False),
                  ("timeout", "int", "Timeout (max. 300)", 300),
                  ("passkey", "password", "API key", "")]

    __description__ = """Send captchas to 9kw.eu"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"

    API_URL = "://www.9kw.eu/index.cgi"


    def setup(self):
        self.API_URL = "https" + self.API_URL if self.getConfig("https") else "http" + self.API_URL
        self.info = {}

    def getCredits(self):
        response = getURL(self.API_URL, get={"apikey": self.getConfig("passkey"), "pyload": "1", "source": "pyload",
                                             "action": "usercaptchaguthaben"})

        if response.isdigit():
            self.logInfo(_("%s credits left") % response)
            self.info['credits'] = credits = int(response)
            return credits
        else:
            self.logError(response)
            return 0

    def processCaptcha(self, task):
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)
        self.logDebug("%s : %s" % (task.captchaFile, data))
        if task.isPositional():
            mouse = 1
        else:
            mouse = 0

        response = getURL(self.API_URL, post={
            "apikey": self.getConfig("passkey"),
            "prio": self.getConfig("prio"),
            "confirm": self.getConfig("confirm"),
            "captchaperhour": self.getConfig("captchaperhour"),
            "maxtimeout": self.getConfig("timeout"),
            "selfsolve": self.getConfig("selfsolve"),
            "pyload": "1",
            "source": "pyload",
            "base64": "1",
            "mouse": mouse,
            "file-upload-01": data,
            "action": "usercaptchaupload"})

        if response.isdigit():
            self.logInfo(_("New CaptchaID from upload: %s : %s") % (response, task.captchaFile))

            for _ in xrange(1, 100, 1):
                response2 = getURL(self.API_URL, get={"apikey": self.getConfig("passkey"), "id": response,
                                                      "pyload": "1", "source": "pyload",
                                                      "action": "usercaptchacorrectdata"})

                if response2 != "":
                    break

                time.sleep(3)

            result = response2
            task.data['ticket'] = response
            self.logInfo("result %s : %s" % (response, result))
            task.setResult(result)
        else:
            self.logError("Bad upload: %s" % response)
            return False

    def newCaptchaTask(self, task):
        if not task.isTextual() and not task.isPositional():
            return False

        if not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.setWaiting(self.getConfig("timeout"))
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logError(_("Your Captcha 9kw.eu Account has not enough credits"))

    def captchaCorrect(self, task):
        if "ticket" in task.data:

            try:
                response = getURL(self.API_URL,
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.getConfig("passkey"),
                                        "api_key": self.getConfig("passkey"),
                                        "correct": "1",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "id": task.data['ticket']})
                self.logInfo("Request correct: %s" % response)

            except BadHeader, e:
                self.logError("Could not send correct request.", str(e))
        else:
            self.logError("No CaptchaID for correct request (task %s) found." % task)

    def captchaInvalid(self, task):
        if "ticket" in task.data:

            try:
                response = getURL(self.API_URL,
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.getConfig("passkey"),
                                        "api_key": self.getConfig("passkey"),
                                        "correct": "2",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "id": task.data['ticket']})
                self.logInfo("Request refund: %s" % response)

            except BadHeader, e:
                self.logError("Could not send refund request.", str(e))
        else:
            self.logError("No CaptchaID for not correct request (task %s) found." % task)
