# -*- coding: utf-8 -*-
#@author: mkaay, RaNaN, zoidberg

from __future__ import with_statement
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from _thread import start_new_thread
from base64 import b64encode
import time

from pyload.network.requestfactory import get_url
from pyload.network.httprequest import BadHeader

from pyload.plugin.hook import Hook


class Captcha9kw(Hook):
    __name__ = "Captcha9kw"
    __version__ = "0.09"
    __description__ = """Send captchas to 9kw.eu"""
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
    __author_name__ = "RaNaN"
    __author_mail__ = "Mast3rRaNaN@hotmail.de"

    API_URL = "://www.9kw.eu/index.cgi"

    def setup(self):
        self.API_URL = "https" + self.API_URL if self.get_config("https") else "http" + self.API_URL
        self.info = {}

    def get_credits(self):
        response = get_url(self.API_URL, get={"apikey": self.get_config("passkey"), "pyload": "1", "source": "pyload",
                                             "action": "usercaptchaguthaben"})

        if response.isdigit():
            self.log_info(_("%s credits left") % response)
            self.info["credits"] = credits = int(response)
            return credits
        else:
            self.log_error(response)
            return 0

    def process_captcha(self, task):
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)
        self.log_debug("%s : %s" % (task.captchaFile, data))
        if task.isPositional():
            mouse = 1
        else:
            mouse = 0

        response = get_url(self.API_URL, post={
            "apikey": self.get_config("passkey"),
            "prio": self.get_config("prio"),
            "confirm": self.get_config("confirm"),
            "captchaperhour": self.get_config("captchaperhour"),
            "maxtimeout": self.get_config("timeout"),
            "selfsolve": self.get_config("selfsolve"),
            "pyload": "1",
            "source": "pyload",
            "base64": "1",
            "mouse": mouse,
            "file-upload-01": data,
            "action": "usercaptchaupload"})

        if response.isdigit():
            self.log_info(_("New CaptchaID from upload: %s : %s") % (response, task.captchaFile))

            for _ in range(1, 100, 1):
                response2 = get_url(self.API_URL, get={"apikey": self.get_config("passkey"), "id": response,
                                                      "pyload": "1", "source": "pyload",
                                                      "action": "usercaptchacorrectdata"})

                if response2 != "":
                    break

                time.sleep(3)

            result = response2
            task.data["ticket"] = response
            self.log_info("result %s : %s" % (response, result))
            task.setResult(result)
        else:
            self.log_error("Bad upload: %s" % response)
            return False

    def new_captcha_task(self, task):
        if not task.isTextual() and not task.isPositional():
            return False

        if not self.get_config("passkey"):
            return False

        if self.pyload.is_client_connected() and not self.get_config("force"):
            return False

        if self.get_credits() > 0:
            task.handler.append(self)
            task.setWaiting(self.get_config("timeout"))
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.log_error(_("Your Captcha 9kw.eu Account has not enough credits"))

    def captcha_correct(self, task):
        if "ticket" in task.data:

            try:
                response = get_url(self.API_URL,
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.get_config("passkey"),
                                        "api_key": self.get_config("passkey"),
                                        "correct": "1",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "id": task.data["ticket"]})
                self.log_info("Request correct: %s" % response)

            except BadHeader as e:
                self.log_error("Could not send correct request.", str(e))
        else:
            self.log_error("No CaptchaID for correct request (task %s) found." % task)

    def captcha_invalid(self, task):
        if "ticket" in task.data:

            try:
                response = get_url(self.API_URL,
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.get_config("passkey"),
                                        "api_key": self.get_config("passkey"),
                                        "correct": "2",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "id": task.data["ticket"]})
                self.log_info("Request refund: %s" % response)

            except BadHeader as e:
                self.log_error("Could not send refund request.", str(e))
        else:
            self.log_error("No CaptchaID for not correct request (task %s) found." % task)
