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

    @author: mkaay, RaNaN, zoidberg
"""
from __future__ import with_statement

from thread import start_new_thread
from base64 import b64encode
import cStringIO
import pycurl
import time

from module.network.RequestFactory import getURL, getRequest
from module.network.HTTPRequest import BadHeader

from module.plugins.Hook import Hook

class Captcha9kw(Hook):
    __name__ = "Captcha9kw"
    __version__ = "0.02"
    __description__ = """send captchas to 9kw.eu"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "API key", ""),]
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    API_URL = "http://www.9kw.eu/index.cgi"

    def setup(self):
        self.info = {}

    def getCredits(self):    
        response = getURL(self.API_URL, get = { "apikey": self.getConfig("passkey"), "pyload": "1", "action": "usercaptchaguthaben" })
        
        if response.isdigit():
            self.logInfo(_("%s credits left") % response)
            self.info["credits"] = credits = int(response)
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

        response = getURL(self.API_URL, post = { 
                        "apikey": self.getConfig("passkey"), 
                        "pyload": "1", 
                        "base64": "1", 
                        "file-upload-01": data, 
                        "action": "usercaptchaupload" })

        for i in range(1, 100, 2): 
            response2 = getURL(self.API_URL, get = { "apikey": self.getConfig("passkey"), "id": response,"pyload": "1", "action": "usercaptchacorrectdata" })

            if(response2 != ""):
                break;

            time.sleep(1)

        result = response2
        task.data["ticket"] = response
        self.logDebug("result %s : %s" % (response, result))
        task.setResult(result)

    def newCaptchaTask(self, task):
        if "service" in task.data: #captcha already beeing handled
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
            self.logInfo(_("Your Captcha 9kw.eu Account has not enough credits"))

    def captchaCorrect(self, task):
        if "ticket" in task.data:

            try:
                response = getURL(self.API_URL, 
                              post={ "action": "usercaptchacorrectback",
                                     "apikey": self.getConfig("passkey"),
                                     "api_key": self.getConfig("passkey"),
                                     "correct": "1",
                                     "pyload": "1",
                                     "id": task.data["ticket"] }
                              )
                self.logInfo("Request correct: %s" % response)

            except BadHeader, e:
                self.logError("Could not send correct request.", str(e))

    def captchaInvalid(self, task):
        if "ticket" in task.data:
            
            try:
                response = getURL(self.API_URL, 
                              post={ "action": "usercaptchacorrectback",
                                     "apikey": self.getConfig("passkey"),
                                     "api_key": self.getConfig("passkey"),
                                     "correct": "2",
                                     "pyload": "1",
                                     "id": task.data["ticket"] }
                              )
                self.logInfo("Request refund: %s" % response)

            except BadHeader, e:
                self.logError("Could not send refund request.", str(e))