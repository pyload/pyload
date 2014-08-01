# -*- coding: utf-8 -*-

from __future__ import with_statement

from base64 import b64encode
from pycurl import LOW_SPEED_TIME
from thread import start_new_thread
from uuid import uuid4

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL, getRequest
from module.plugins.Hook import Hook


class ExpertDecoders(Hook):
    __name__ = "ExpertDecoders"
    __type__ = "hook"
    __version__ = "0.01"

    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Access key", "")]

    __description__ = """Send captchas to expertdecoders.com"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    API_URL = "http://www.fasttypers.org/imagepost.ashx"


    def setup(self):
        self.info = {}

    def getCredits(self):
        response = getURL(self.API_URL, post={"key": self.getConfig("passkey"), "action": "balance"})

        if response.isdigit():
            self.logInfo(_("%s credits left") % response)
            self.info['credits'] = credits = int(response)
            return credits
        else:
            self.logError(response)
            return 0

    def processCaptcha(self, task):
        task.data['ticket'] = ticket = uuid4()
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)
        #self.logDebug("%s: %s : %s" % (ticket, task.captchaFile, data))

        req = getRequest()
        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            result = req.load(self.API_URL,  post={"action": "upload", "key": self.getConfig("passkey"),
                                                   "file": data, "gen_task_id": ticket})
        finally:
            req.close()

        self.logDebug("result %s : %s" % (ticket, result))
        task.setResult(result)

    def newCaptchaTask(self, task):
        if not task.isTextual():
            return False

        if not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logInfo(_("Your ExpertDecoders Account has not enough credits"))

    def captchaInvalid(self, task):
        if "ticket" in task.data:

            try:
                response = getURL(self.API_URL, post={"action": "refund", "key": self.getConfig("passkey"),
                                                      "gen_task_id": task.data['ticket']})
                self.logInfo("Request refund: %s" % response)

            except BadHeader, e:
                self.logError("Could not send refund request.", str(e))
