# -*- coding: utf-8 -*-
#@author: mkaay, RaNaN, zoidberg

from __future__ import with_statement
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()
from builtins import str
from _thread import start_new_thread
from pycurl import LOW_SPEED_TIME
from uuid import uuid4
from base64 import b64encode

from pyload.network.request import get_url, get_request
from pyload.network.httprequest import BadHeader

from pyload.plugin.hook import Hook


class ExpertDecoders(Hook):
    __name__ = "ExpertDecoders"
    __version__ = "0.01"
    __description__ = """Send captchas to expertdecoders.com"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force CT even if client is connected", False),
                  ("passkey", "password", "Access key", "")]
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("Mast3rRaNaN@hotmail.de", "zoidberg@mujmail.cz")

    API_URL = "http://www.fasttypers.org/imagepost.ashx"

    def setup(self):
        self.info = {}

    def get_credits(self):
        response = get_url(self.API_URL, post={"key": self.get_config("passkey"), "action": "balance"})

        if response.isdigit():
            self.log_info(_("%s credits left") % response)
            self.info["credits"] = credits = int(response)
            return credits
        else:
            self.log_error(response)
            return 0

    def process_captcha(self, task):
        task.data["ticket"] = ticket = uuid4()
        result = None

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)
        #self.log_debug("%s: %s : %s" % (ticket, task.captchaFile, data))

        req = get_request()
        #raise timeout threshold
        req.c.setopt(LOW_SPEED_TIME, 80)

        try:
            result = req.load(self.API_URL,  post={"action": "upload", "key": self.get_config("passkey"),
                                                   "file": data, "gen_task_id": ticket})
        finally:
            req.close()

        self.log_debug("result %s : %s" % (ticket, result))
        task.setResult(result)

    def new_captcha_task(self, task):
        if not task.isTextual():
            return False

        if not self.get_config("passkey"):
            return False

        if self.pyload.is_client_connected() and not self.get_config("force"):
            return False

        if self.get_credits() > 0:
            task.handler.append(self)
            task.setWaiting(100)
            start_new_thread(self.processCaptcha, (task,))

        else:
            self.log_info(_("Your ExpertDecoders Account has not enough credits"))

    def captcha_invalid(self, task):
        if "ticket" in task.data:

            try:
                response = get_url(self.API_URL, post={"action": "refund", "key": self.get_config("passkey"),
                                                      "gen_task_id": task.data["ticket"]})
                self.log_info("Request refund: %s" % response)

            except BadHeader as e:
                self.log_error("Could not send refund request.", str(e))
