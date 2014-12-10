# -*- coding: utf-8 -*-

from pycurl import FORM_FILE, LOW_SPEED_TIME

from pyload.network.HTTPRequest import BadHeader
from pyload.network.RequestFactory import getURL, getRequest
from pyload.plugins.Addon import Addon


class BypassCaptchaException(Exception):

    def __init__(self, err):
        self.err = err


    def getCode(self):
        return self.err


    def __str__(self):
        return "<BypassCaptchaException %s>" % self.err


    def __repr__(self):
        return "<BypassCaptchaException %s>" % self.err


class BypassCaptcha(Addon):
    __name    = "BypassCaptcha"
    __type    = "hook"
    __version = "0.05"

    __config = [("force", "bool", "Force BC even if client is connected", False),
                ("passkey", "password", "Passkey", "")]

    __description = """Send captchas to BypassCaptcha.com"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Godofdream", "soilfcition@gmail.com"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    PYLOAD_KEY = "4f771155b640970d5607f919a615bdefc67e7d32"

    SUBMIT_URL = "http://bypasscaptcha.com/upload.php"
    RESPOND_URL = "http://bypasscaptcha.com/check_value.php"
    GETCREDITS_URL = "http://bypasscaptcha.com/ex_left.php"


    def getCredits(self):
        res = getURL(self.GETCREDITS_URL, post={"key": self.getConfig("passkey")})

        data = dict(x.split(' ', 1) for x in res.splitlines())
        return int(data['Left'])


    def submit(self, captcha, captchaType="file", match=None):
        req = getRequest()

        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            res = req.load(self.SUBMIT_URL,
                           post={'vendor_key': self.PYLOAD_KEY,
                                 'key': self.getConfig("passkey"),
                                 'gen_task_id': "1",
                                 'file': (FORM_FILE, captcha)},
                           multipart=True)
        finally:
            req.close()

        data = dict(x.split(' ', 1) for x in res.splitlines())
        if not data or "Value" not in data:
            raise BypassCaptchaException(res)

        result = data['Value']
        ticket = data['TaskId']
        self.logDebug("Result %s : %s" % (ticket, result))

        return ticket, result


    def respond(self, ticket, success):
        try:
            res = getURL(self.RESPOND_URL, post={"task_id": ticket, "key": self.getConfig("passkey"),
                                                      "cv": 1 if success else 0})
        except BadHeader, e:
            self.logError(_("Could not send response"), e)


    def newCaptchaTask(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.data['service'] = self.__name
            task.setWaiting(100)
            self.processCaptcha(task)
        else:
            self.logInfo(_("Your %s account has not enough credits") % self.__name)


    def captchaCorrect(self, task):
        if task.data['service'] == self.__name and "ticket" in task.data:
            self.respond(task.data['ticket'], True)


    def captchaInvalid(self, task):
        if task.data['service'] == self.__name and "ticket" in task.data:
            self.respond(task.data['ticket'], False)


    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except BypassCaptchaException, e:
            task.error = e.getCode()
            return

        task.data['ticket'] = ticket
        task.setResult(result)
