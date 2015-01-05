# -*- coding: utf-8 -*-

from __future__ import with_statement

from base64 import b64encode
from pycurl import LOW_SPEED_TIME
from uuid import uuid4

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL, getRequest
from module.plugins.Hook import Hook, threaded


class ExpertDecoders(Hook):
    __name__    = "ExpertDecoders"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Access key", "")]

    __description__ = """Send captchas to expertdecoders.com"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://www.fasttypers.org/imagepost.ashx"


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def getCredits(self):
        res = getURL(self.API_URL, post={"key": self.getConfig("passkey"), "action": "balance"})

        if res.isdigit():
            self.logInfo(_("%s credits left") % res)
            self.info['credits'] = credits = int(res)
            return credits
        else:
            self.logError(res)
            return 0


    @threaded
    def _processCaptcha(self, task):
        task.data['ticket'] = ticket = uuid4()
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)

        req = getRequest()
        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            result = req.load(self.API_URL, post={"action": "upload", "key": self.getConfig("passkey"),
                                                   "file": data, "gen_task_id": ticket})
        finally:
            req.close()

        self.logDebug("Result %s : %s" % (ticket, result))
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
            self._processCaptcha(task)

        else:
            self.logInfo(_("Your ExpertDecoders Account has not enough credits"))


    def captchaInvalid(self, task):
        if "ticket" in task.data:

            try:
                res = getURL(self.API_URL,
                             post={'action': "refund", 'key': self.getConfig("passkey"), 'gen_task_id': task.data['ticket']})
                self.logInfo(_("Request refund"), res)

            except BadHeader, e:
                self.logError(_("Could not send refund request"), e)
