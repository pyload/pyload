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
import re

class Captcha9kw(Hook):
    __name__ = "Captcha9kw"
    __version__ = "0.10"
    __description__ = """Send captchas to 9kw.eu"""
    __config__ = [("activated", "bool", "Activated", False),
                  ("force", "bool", "Force CT even if client is connected", True),
                  ("https", "bool", "Enable HTTPS", False),
                  ("confirm", "bool", "Confirm Captcha (Cost +6)", False),
                  ("captchaperhour", "int", "Captcha per hour", "9999"),
                  ("prio", "int", "Prio 1-20 (Cost +1-20)", "0"),
                  ("queue", "int", "Max. Queue (min. 10, max. 999)", "0"),
                  ("hosteroptions", "string", "Hosteroptions (Format: pluginname:prio=1:selfsolfe=1:confirm=1:timeout=900;)", "ShareonlineBiz:prio=0:timeout=999;UploadedTo:prio=0:timeout=999;SerienjunkiesOrg:prio=1:min=3;max=3;timeout=90"),
                  ("selfsolve", "bool", "If enabled and you have a 9kw client active only you will get your captcha to solve it (Selfsolve)", "0"),
                  ("passkey", "password", "API key", ""),
                  ("timeout", "int", "Timeout (min. 60s, max. 3999s)", "300")
		]
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"

    API_URL = "://www.9kw.eu/index.cgi"

    def setup(self):
        self.info = {}

    def getCredits(self):
        https = "https" if self.getConfig("https") else "http"
        response = getURL(https + self.API_URL, get = { "apikey": self.getConfig("passkey"), "pyload": "1", "source": "pyload", "action": "usercaptchaguthaben" })

        if response.isdigit():
            self.logInfo("%s credits left" % response)
            self.info["credits"] = credits = int(response)
            return credits
        else:
            self.logError(response)
            return 0

    def processCaptcha(self, task):
        result = None
        https = "https" if self.getConfig("https") else "http"

        with open(task.captchaFile, 'rb') as f:
            data = f.read()
        data = b64encode(data)
        self.logDebug("%s : %s" % (task.captchaFile, data))
        if task.isPositional():
            mouse = 1
        else:
            mouse = 0

	regex = re.compile("_([^_]*)_\d+.\w+")
	r = regex.search(task.captchaFile)
	pluginname = r.group(1)

	min_option = 2
	max_option = 50
	phrase_option = 0
	numeric_option = 0
	case_sensitive_option = 0
	math_option = 0
	prio_option = self.getConfig("prio")
	confirm_option = self.getConfig("confirm")
	timeout_option = self.getConfig("timeout")
	selfsolve_option = self.getConfig("selfsolve")
	cph_option = self.getConfig("captchaperhour")
	hosteroptions_conf = self.getConfig("hosteroptions")
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
	                                                captchaperhour_option = hosteroption[1]
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
			"apikey": self.getConfig("passkey"), 
			"prio": prio_option,
			"confirm": confirm_option,
			"maxtimeout": timeout_option,
			"selfsolve": selfsolve_option,
			"captchaperhour": cph_option,
			"case-sensitive": case_sensitive_option,
			"min_len": min_option,
			"max_len": max_option,
			"phrase": phrase_option,
			"numeric": numeric_option,
			"math": math_option,
			"oldsource": pluginname,
			"pyload": "1", 
			"source": "pyload", 
			"base64": "1", 
			"mouse": mouse,
			"file-upload-01": data, 
			"action": "usercaptchaupload" })

		if(response != ""):
			break;

            except BadHeader, e:
		time.sleep(3)

	if response.isdigit():
		self.logInfo("NewCaptchaID from upload: %s : %s" % (response,task.captchaFile))

		for _ in xrange(1, int(self.getConfig("timeout") / 5), 1): 
		        response2 = getURL(https + self.API_URL, get = { "apikey": self.getConfig("passkey"), "id": response,"pyload": "1", "info": "1", "source": "pyload", "action": "usercaptchacorrectdata" })

			if response2 == "" or response2 == "NO DATA":
				time.sleep(5)
			else:
				break;

		result = response2
		task.data["ticket"] = response
		self.logInfo("result %s : %s" % (response, result))
		task.setResult(result)
	else:
		self.logError("Bad upload: %s" % response)
		return False

    def newCaptchaTask(self, task):
        if not task.isTextual() and not task.isPositional():
            return False

        if not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        if self.getCredits() > 0:
	    if self.getConfig("queue") > 10 and self.getConfig("queue") < 1000:
	 	    https = "https" if self.getConfig("https") else "http"
	 	    servercheck = getURL(https + "://www.9kw.eu/grafik/servercheck.txt", get = {})

		    for i in range(1, 3, 1): 
		        regex = re.compile("queue=(\d+)")
		        r = regex.search(servercheck)
			if(self.getConfig("queue") < r.group(1)):
				break;

			time.sleep(10)

            regex = re.compile("_([^_]*)_\d+.\w+")
            r = regex.search(task.captchaFile)
            pluginname = r.group(1)

	    if self.getConfig("timeout") > 0:
	    	timeout_option = self.getConfig("timeout")
	    else:
	        timeout_option = 300

            hosteroptions_conf = self.getConfig("hosteroptions")
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
	    self.logDebug("Send captcha to function processCaptcha")
            start_new_thread(self.processCaptcha, (task,))
        else:
            self.logError("Your Captcha 9kw.eu Account has not enough credits")

    def captchaCorrect(self, task):
        if "ticket" in task.data:
            https = "https" if self.getConfig("https") else "http"

            try:
                response = getURL(https + self.API_URL, 
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.getConfig("passkey"),
	                                "api_key": self.getConfig("passkey"),
	                                "correct": "1",
	                                "pyload": "1",
	                                "source": "pyload", 
	                                "id": task.data["ticket"]})
                self.logInfo("Request correct: %s" % response)

            except BadHeader, e:
                self.logError("Could not send correct request.", str(e))
        else:
            self.logError("No CaptchaID for correct request (task %s) found." % task)

    def captchaInvalid(self, task):
        if "ticket" in task.data:
            https = "https" if self.getConfig("https") else "http"

            try:
                response = getURL(https + self.API_URL, 
                                  post={"action": "usercaptchacorrectback",
                                        "apikey": self.getConfig("passkey"),
                                        "api_key": self.getConfig("passkey"),
                                        "correct": "2",
                                        "pyload": "1",
                                        "source": "pyload",
                                        "id": task.data["ticket"]})
                self.logInfo("Request refund: %s" % response)

            except BadHeader, e:
                self.logError("Could not send refund request.", str(e))
        else:
            self.logError("No CaptchaID for not correct request (task %s) found." % task)
