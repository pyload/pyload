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
import time

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

from module.network.RequestFactory import getURL
from module.network.HTTPRequest import BadHeader

from module.plugins.internal.Addon import Addon
from module.plugins.internal.misc import threaded
import re

class Captcha9Kw(Addon):
    __name__ = "Captcha9Kw"
    __type__ = "hook"
    __version__ = "0.44"
    __description__ = """Send captchas to 9kw.eu"""
    __config__ = [("activated", "bool", "Activated", True),
                  ("force", "bool", "Force captcha resolving even if client is connected", True),
                  ("https", "bool", "Use HTTPS (secure connection)", False),
                  ("confirm", "bool", "Confirm Captcha (cost +6 credits)", False),
                  ("captchaperhour", "int", "Captcha per hour", "9999"),
                  ("captchapermin", "int", "Captcha per minute", "9999"),
                  ("prio", "int", "Prio (max. 20, cost +1 -> +20 credits)", "0"),
                  ("queue", "int", "Max. Queue (min. 10, max. 999)", "0"),
                  ("hosteroptions", "string", "Hosteroptions (Format: pluginname:prio=1:selfsolve=1:confirm=1:timeout=900;)", "ShareonlineBiz:prio=0:timeout=999;UploadedTo:prio=0:timeout=999;SerienjunkiesOrg:prio=1:min=3;max=3;timeout=90"),
                  ("selfsolve", "bool", "Selfsolve (manually solve your captcha in your 9kw client if active)", "0"),
                  ("passkey", "password", "API key", ""),
                  ("timeout", "int", "Timeout in seconds (min. 60, max. 3999)", "999")
        ]
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"

    API_URL = "://www.9kw.eu/index.cgi"

    def setup(self):
        self.info = {}

    def getCredits(self):
        https = "https" if self.config.get("https") else "http"
        response = getURL(https + self.API_URL, get = { "apikey": self.config.get("passkey"), "pyload": "1", "source": "pyload", "action": "usercaptchaguthaben" })

        if response.isdigit():
            self.log_info("%s credits left" % response)
            self.info["credits"] = credits = int(response)
            return credits
        else:
            self.log_error(response)
            return 0

    @threaded
    def processCaptcha(self, task):
        result = None
        https = "https" if self.config.get("https") else "http"

        if task.isInteractive():
            pageurl = task.captchaImg['url']
            if not pageurl.startswith("http://") and not pageurl.startswith("https://"):
                self.error(_("Invalid url"))

            pageurl = "{0.scheme}://{0.netloc}/".format(urlsplit(pageurl))
            data = task.captchaImg['sitekey']
            self.log_debug("interactive captcha: sitekey = %s, pageurl = %s" % (data,pageurl))
            interactive = 1
            isBase64 = 0

        else:
            with open(task.captchaFile, 'rb') as f:
                data = f.read()
            data = b64encode(data)
            pageurl = ""
            interactive = 0
            isBase64 = 1
            self.log_debug("%s : %s" % (task.captchaFile, data))

        if task.isPositional():
            mouse = 1
        else:
            mouse = 0

        regex = re.compile("_([^_]*)_\d+.\w+")
        r = regex.search(task.captchaFile)
        pluginname = r.group(1)

        min_option = 1
        max_option = 50
        phrase_option = 0
        numeric_option = 0
        case_sensitive_option = 0
        math_option = 0
        prio_option = self.config.get("prio")
        confirm_option = self.config.get("confirm")
        timeout_option = self.config.get("timeout")
        selfsolve_option = self.config.get("selfsolve")
        cph_option = self.config.get("captchaperhour")
        cpm_option = self.config.get("captchapermin")
        hosteroptions_conf = self.config.get("hosteroptions")
        hosteroptions = hosteroptions_conf.split(";")

        if len(hosteroptions) > 0:
            for hosterthing in hosteroptions:
                hosterdetails = hosterthing.split(":");
                if len(hosterdetails) > 0 and hosterdetails[0].lower() == pluginname.lower():
                    for hosterdetail in hosterdetails:
                        hosteroption = hosterdetail.split("=");
                        if len(hosteroption) > 1:
                            if hosteroption[0].lower() == 'prio' and hosteroption[1].isdigit():
                                    prio_option = hosteroption[1]
                            elif hosteroption[0].lower() == 'timeout' and hosteroption[1].isdigit():
                                    timeout_option = hosteroption[1]
                            elif hosteroption[0].lower() == 'cph' and hosteroption[1].isdigit():
                                    cph_option = hosteroption[1]
                            elif hosteroption[0].lower() == 'cpm' and hosteroption[1].isdigit():
                                    cpm_option = hosteroption[1]
                            elif hosteroption[0].lower() == 'selfsolve' and hosteroption[1].isdigit():
                                    selfsolve_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'confirm' and hosteroption[1].isdigit():
                                    confirm_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'max' and hosteroption[1].isdigit():
                                    max_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'min' and hosteroption[1].isdigit():
                                    min_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'case-sensitive' and hosteroption[1].isdigit():
                                    case_sensitive_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'math' and hosteroption[1].isdigit():
                                    math_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'numeric' and hosteroption[1].isdigit():
                                    numeric_option = hosteroptions[1]
                            elif hosteroption[0].lower() == 'phrase' and hosteroption[1].isdigit():
                                    phrase_option = hosteroptions[1]

        for _ in xrange(1, 5, 1):
            try:
                response = getURL(https + self.API_URL, post = {
                    "apikey": self.config.get("passkey"),
                    "prio": prio_option,
                    "confirm": confirm_option,
                    "maxtimeout": timeout_option,
                    "selfsolve": selfsolve_option,
                    "captchaperhour": cph_option,
                    "captchapermin": cpm_option,
                    "case-sensitive": case_sensitive_option,
                    "min_len": min_option,
                    "max_len": max_option,
                    "phrase": phrase_option,
                    "numeric": numeric_option,
                    "math": math_option,
                    "oldsource": pluginname,
                    "pyload": "1",
                    "source": "pyload",
                    "version": self.__version__,
                    "name": self.__name__,
                    "base64": isBase64,
                    "mouse": mouse,
                    "file-upload-01": data,
                    "pageurl" : pageurl,
                    "interactive" : interactive,
                    "action": "usercaptchaupload" })
                time.sleep(2)

                if(response != ""):
                    break;

            except BadHeader, e:
                time.sleep(3)

        if response.isdigit():
            self.log_info("NewCaptchaID from upload: %s : %s" % (response,task.captchaFile))

            for _ in xrange(1, int(self.config.get("timeout") / 5), 1):
                response2 = getURL(https + self.API_URL, get = { "apikey": self.config.get("passkey"), "id": response,"pyload": "1", "info": "1", "source": "pyload", "version": self.__version__, "name": self.__name__, "action": "usercaptchacorrectdata" })

                if response2 == "" or response2 == "NO DATA":
                    time.sleep(5)
                else:
                    break;

            result = response2
            task.data["ticket"] = response
            self.log_info("result %s : %s" % (response, result))
            task.setResult(result)
        else:
            self.log_error("Bad upload: %s" % response)
            return False

    def newCaptchaTask(self, task):
        if not task.isTextual() and not task.isPositional() and not task.isInteractive():
            return False

        if not self.config.get("passkey"):
            return False

        if self.pyload.isClientConnected() and not self.config.get("force"):
            return False

        if self.getCredits() > 0:
            if self.config.get("queue") > 10 and self.config.get("queue") < 1000:
                https = "https" if self.config.get("https") else "http"
                servercheck = getURL(https + "://www.9kw.eu/grafik/servercheck.txt", get = {})

                for i in range(1, 3, 1):
                    regex = re.compile("queue=(\d+)")
                    r = regex.search(servercheck)
                    if(self.config.get("queue") < r.group(1)):
                        break;

                    time.sleep(10)

            regex = re.compile("_([^_]*)_\d+.\w+")
            r = regex.search(task.captchaFile)
            pluginname = r.group(1)

            if self.config.get("timeout") > 0:
                timeout_option = self.config.get("timeout")
            else:
                timeout_option = 300

            hosteroptions_conf = self.config.get("hosteroptions")
            hosteroptions = hosteroptions_conf.split(";")

            if len(hosteroptions) > 0:
                for hosterthing in hosteroptions:
                    hosterdetails = hosterthing.split(":");
                    if len(hosterdetails) > 0 and hosterdetails[0].lower() == pluginname.lower():
                        for hosterdetail in hosterdetails:
                            hosteroption = hosterdetail.split("=");
                            if len(hosteroption) > 1 and hosteroption[0].lower() == 'timeout' and hosteroption[1].isdigit():
                                timeout_option = hosteroption[1]

            task.handler.append(self)
            task.setWaiting(int(timeout_option))
            self.log_debug("Send captcha to function processCaptcha")
            start_new_thread(self.processCaptcha, (task,))
        else:
            self.log_error("Your Captcha 9kw.eu Account has not enough credits")

    def captchaCorrect(self, task):
        if "ticket" in task.data:
            https = "https" if self.config.get("https") else "http"

            for _ in xrange(1, 3, 1):
                response = getURL(https + self.API_URL, get={
                                        "action": "usercaptchacorrectback",
                                        "apikey": self.config.get("passkey"),
                                        "api_key": self.config.get("passkey"),
                                        "correct": "1",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "version": self.__version__,
                                        "name": self.__name__,
                                        "id": task.data["ticket"]})

                if response == "OK":
                    self.log_info("Request correct: %s" % response)
                    break;
                else:
                    self.log_error("Could not send correct request: %s" % response)
                    time.sleep(1)
        else:
            self.log_error("No CaptchaID for correct request (task %s) found." % task)

    def captchaInvalid(self, task):
        if "ticket" in task.data:
            https = "https" if self.config.get("https") else "http"

            for _ in xrange(1, 3, 1):
                response = getURL(https + self.API_URL, get={
                    "action": "usercaptchacorrectback",
                    "apikey": self.config.get("passkey"),
                    "api_key": self.config.get("passkey"),
                    "correct": "2",
                    "pyload": "1",
                    "source": "pyload",
                    "version": self.__version__,
                    "name": self.__name__,
                    "id": task.data["ticket"]})

                if response == "OK":
                    self.log_info("Request refund: %s" % response)
                    break;
                else:
                    self.log_error("Could not send refund request: %s" % response)
                    time.sleep(1)
        else:
            self.log_error("No CaptchaID for refund request (task %s) found." % task)
