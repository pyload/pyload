# -*- coding: utf-8 -*-
#@author: mkaay, RaNaN, zoidberg

from __future__ import with_statement
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import range
from _thread import start_new_thread

import pycurl
import io
from urllib.parse import urlencode
from time import sleep
import Image

from pyload.network.request import get_url, get_request
from pyload.plugin.hook import Hook


class CaptchaBrotherhoodException(Exception):
    def __init__(self, err):
        self.err = err

    def get_code(self):
        return self.err

    def __str__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err

    def __repr__(self):
        return "<CaptchaBrotherhoodException %s>" % self.err


class CaptchaBrotherhood(Hook):
    __name__ = "CaptchaBrotherhood"
    __version__ = "0.04"
    __description__ = """Send captchas to CaptchaBrotherhood.com"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("username", "str", "Username", ""),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Password", "")]
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("Mast3rRaNaN@hotmail.de", "zoidberg@mujmail.cz")

    API_URL = "http://www.captchabrotherhood.com/"

    def setup(self):
        self.info = {}

    def get_credits(self):
        response = get_url(self.API_URL + "askCredits.aspx",
                          get={"username": self.get_config("username"), "password": self.get_config("passkey")})
        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException(response)
        else:
            credits = int(response[3:])
            self.log_info(_("%d credits left") % credits)
            self.info["credits"] = credits
            return credits

    def submit(self, captcha, captchaType="file", match=None):
        try:
            img = Image.open(captcha)
            output = io.StringIO()
            self.log_debug("CAPTCHA IMAGE", img, img.format, img.mode)
            if img.format in ("GIF", "JPEG"):
                img.save(output, img.format)
            else:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output, "JPEG")
            data = output.getvalue()
            output.close()
        except Exception as e:
            raise CaptchaBrotherhoodException("Reading or converting captcha image failed: %s" % e)

        req = get_request()

        url = "%ssendNewCaptcha.aspx?%s" % (self.API_URL,
                                            urlencode({"username": self.get_config("username"),
                                                       "password": self.get_config("passkey"),
                                                       "captchaSource": "pyLoad",
                                                       "timeout": "80"}))

        req.c.setopt(pycurl.URL, url)
        req.c.setopt(pycurl.POST, 1)
        req.c.setopt(pycurl.POSTFIELDS, data)
        req.c.setopt(pycurl.HTTPHEADER, ["Content-Type: text/html"])

        try:
            req.c.perform()
            response = req.get_response()
        except Exception as e:
            raise CaptchaBrotherhoodException("Submit captcha image failed")

        req.close()

        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException(response[1])

        ticket = response[3:]

        for _ in range(15):
            sleep(5)
            response = self.get_api("askCaptchaResult", ticket)
            if response.startswith("OK-answered"):
                return ticket, response[12:]

        raise CaptchaBrotherhoodException("No solution received in time")

    def get_api(self, api, ticket):
        response = get_url("%s%s.aspx" % (self.API_URL, api),
                          get={"username": self.get_config("username"),
                               "password": self.get_config("passkey"),
                               "captchaID": ticket})
        if not response.startswith("OK"):
            raise CaptchaBrotherhoodException("Unknown response: %s" % response)

        return response

    def new_captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.get_config("username") or not self.get_config("passkey"):
            return False

        if self.pyload.is_client_connected() and not self.get_config("force"):
            return False

        if self.get_credits() > 10:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))
        else:
            self.log_info("Your CaptchaBrotherhood Account has not enough credits")

    def captcha_invalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            response = self.get_api("complainCaptcha", task.data['ticket'])

    def process_captcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except CaptchaBrotherhoodException as e:
            task.error = e.getCode()
            return

        task.data["ticket"] = ticket
        task.setResult(result)
