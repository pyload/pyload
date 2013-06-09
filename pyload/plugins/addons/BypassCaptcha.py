# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN, Godofdream, zoidberg
"""

from thread import start_new_thread
from pycurl import FORM_FILE, LOW_SPEED_TIME

from module.network.RequestFactory import getURL, getRequest
from module.network.HTTPRequest import BadHeader

from module.plugins.Hook import Hook

PYLOAD_KEY = "4f771155b640970d5607f919a615bdefc67e7d32"

class BypassCaptchaException(Exception):
    def __init__(self, err):
        self.err = err

    def getCode(self):
        return self.err

    def __str__(self):
        return "<BypassCaptchaException %s>" % self.err

    def __repr__(self):
        return "<BypassCaptchaException %s>" % self.err

class BypassCaptcha(Hook):
    __name__ = "BypassCaptcha"
    __version__ = "0.03"
    __description__ = """send captchas to BypassCaptcha.com"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("force", "bool", "Force BC even if client is connected", False),
                  ("passkey", "password", "Passkey", "")]
    __author_name__ = ("RaNaN", "Godofdream", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "soilfcition@gmail.com", "zoidberg@mujmail.cz")

    SUBMIT_URL = "http://bypasscaptcha.com/upload.php"
    RESPOND_URL = "http://bypasscaptcha.com/check_value.php"
    GETCREDITS_URL = "http://bypasscaptcha.com/ex_left.php"

    def setup(self):
        self.info = {}

    def getCredits(self):
        response = getURL(self.GETCREDITS_URL,
                      post = {"key": self.getConfig("passkey")}
                      )
                                                                         
        data = dict([x.split(' ',1) for x in response.splitlines()])
        return int(data['Left'])
        

    def submit(self, captcha, captchaType="file", match=None):
        req = getRequest()

        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            response = req.load(self.SUBMIT_URL, 
                            post={"vendor_key": PYLOAD_KEY,
                                  "key": self.getConfig("passkey"),
                                  "gen_task_id": "1",
                                  "file": (FORM_FILE, captcha)},
                            multipart=True)
        finally:
            req.close()

        data = dict([x.split(' ',1) for x in response.splitlines()])
        if not data or "Value" not in data:
            raise BypassCaptchaException(response)
            
        result = data['Value']
        ticket = data['TaskId']
        self.logDebug("result %s : %s" % (ticket,result))

        return ticket, result

    def respond(self, ticket, success):
        try:
            response = getURL(self.RESPOND_URL, 
                              post={"task_id": ticket,
                                    "key": self.getConfig("passkey"),
                                    "cv": 1 if success else 0}
                              )
        except BadHeader, e:
            self.logError("Could not send response.", str(e))

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
            task.data['service'] = self.__name__
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logInfo("Your %s account has not enough credits" % self.__name__)

    def captchaCorrect(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            self.respond(task.data["ticket"], True)

    def captchaInvalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            self.respond(task.data["ticket"], False)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except BypassCaptchaException, e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)