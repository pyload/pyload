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

    @author: RaNaN
"""

import base64

try:
    from json import loads
except ImportError:
    from simplejson import loads

from thread import start_new_thread
from pycurl import FORM_FILE, LOW_SPEED_TIME

from module.network.RequestFactory import getURL, getRequest
from module.network.HTTPRequest import BadHeader

from module.plugins.Addon import Addon

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
    __name__ = "BypassCaptcha"
    __version__ = "0.02"
    __description__ = """send captchas to bypasscaptcha.com"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("key", "str", "Key", ""),
                  ("force", "bool", "Force CT even if client is connected", False),]
    __author_name__ = ("Godofdream")
    __author_mail__ = ("soilfcition@gmail.com")

    SUBMIT_URL = "http://bypasscaptcha.com/upload.php"
    RESPOND_URL = "http://bypasscaptcha.com/check_value.php"
    GETCREDITS_URL = "http://bypasscaptcha.com/ex_left.php"

    def setup(self):
        self.info = {}

    def getCredits(self):
        json = getURL(BypassCaptcha.GETCREDITS_URL % {"key": self.getConfig("key")})
        response = loads(json)
        if response[0] < 0:
            raise BypassCaptchaException(response[1])
        else:
            self.logInfo(_("%s credits left") % response['Left'])
            self.info["credits"] = response['Left']
            return response['Left']

    def submit(self, captcha, captchaType="file", match=None):
        #if type(captcha) == str and captchaType == "file":
        #    raise BypassCaptchaException("Invalid Type")
        assert captchaType in ("file", "url-jpg", "url-jpeg", "url-png", "url-bmp")

		self.logInfo(_("submitting %s, type %s") % (captcha, captchaType))

        req = getRequest()

        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

		try:
			img = Image.open(captcha)
			self.logDebug("CAPTCHA IMAGE", img, img.format)
			output = StringIO.StringIO()
			img.save(output, "JPEG")
			data = base64.b64encode(output.getvalue())
			output.close()
		except Exception, e:
			raise BypassCaptchaException("Reading or converting captcha image failed: %s" % e)

        try:
            json = req.load(BypassCaptcha.SUBMIT_URL, post={"key": self.getConfig("key"),
                                                           "password": self.getConfig("passkey"),
                                                           "file": data,
                                                           "submit": "Submit",
														   "gen_task_id": 1,
														   "base64_code": 1})
        finally:
            req.close()

        response = loads(json)
        if response[0] < 0:
            raise BypassCaptchaException(response[1])

        ticket = response['TaskId']
        result = response['Value']
        self.logDebug("result %s : %s" % (ticket,result))

        return ticket, result

    def respond(self, ticket, success):
        try:
            json = getURL(BypassCaptcha.RESPOND_URL, post={ "key": self.getConfig("key"),
															"task_id": ticket,
															"cv": 1 if success else 0,
															"submit": "Submit" })

            response = loads(json)
            if response[0] < 0:
                raise BypassCaptchaException(response[1])

        except BadHeader, e:
            self.logError(_("Could not send response."), str(e))

    def newCaptchaTask(self, task):
        if not task.isTextual():
            return False

        if not self.getConfig("key"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
            task.handler.append(self)
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.logInfo(_("Your BypassCaptcha Account has not enough credits"))

    def captchaCorrect(self, task):
        if "TaskId" in task.data:
            ticket = task.data["TaskId"]
            self.respond(ticket, True)

    def captchaInvalid(self, task):
        if "TaskId" in task.data:
            ticket = task.data["TaskId"]
            self.respond(ticket, False)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except BypassCaptchaException, e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)
