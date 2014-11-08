# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from base64 import b64encode
from thread import start_new_thread
from time import sleep

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL

from module.plugins.Hook import Hook


class Captcha9kw(Hook):
    __name__    = "Captcha9kw"
    __type__    = "hook"
    __version__ = "0.13"

    __config__ = [("activated", "bool", "Activated", True),
                  ("force", "bool", "Force captcha resolving even if client is connected", True),
                  ("confirm", "bool", "Confirm Captcha (Cost +6)", False),
                  ("captchaperhour", "int", "Captcha per hour", "9999"),
                  ("prio", "int", "Priority (max. 20)(Cost +0 -> +20)", "0"),
                  ("queue", "int", "Max. Queue (max. 999)", "0"),
                  ("hoster_options", "string", "Hoster options (Format: pluginname:prio=1:selfsolfe=1:confirm=1:timeout=900;)", "ShareonlineBiz:prio=0:timeout=999;UploadedTo:prio=0:timeout=999;SerienjunkiesOrg:prio=1:min=3;max=3;timeout=90"),
                  ("selfsolve", "bool", "If enabled and you have a 9kw client active only you will get your captcha to solve it (Selfsolve)", "0"),
                  ("passkey", "password", "API key", ""),
                  ("timeout", "int", "Timeout (min. 60s, max. 3999s)", "900")]

    __description__ = """Send captchas to 9kw.eu"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL = "http://www.9kw.eu/index.cgi"


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10


    def getCredits(self):
        res = getURL(self.API_URL,
                     get={'apikey': self.getConfig("passkey"),
                          'pyload': "1",
                          'source': "pyload",
                          'action': "usercaptchaguthaben"})

        if res.isdigit():
            self.logInfo(_("%d credits left") % res)
            credits = self.info["credits"] = int(res)
            return credits
        else:
            self.logError(res)
            return 0


    def _processCaptcha(self, task):
        try:
            with open(task.captchaFile, 'rb') as f:
                data = f.read()
        except IOError, e:
            self.logError(str(e))
            return

        data = b64encode(data)
        mouse = 1 if task.isPositional() else 0
        pluginname = re.search(r'_([^_]*)_\d+.\w+', task.captchaFile).group(1)

        self.logDebug("%s: %s" % (task.captchaFile, data))

        option = {'min'            : 2
                  'max'            : 50
                  'phrase'         : 0
                  'numeric'        : 0
                  'case_sensitive' : 0
                  'math'           : 0
                  'prio'           : self.getConfig("prio")
                  'confirm'        : self.getConfig("confirm")
                  'timeout'        : min(max(self.getConfig("timeout") * 60, 300), 3999)
                  'selfsolve'      : self.getConfig("selfsolve")
                  'cph'            : self.getConfig("captchaperhour")
                  'hoster_options' : self.getConfig("hoster_options").split(";")}

        for opt in hoster_options:
            details = opt.split(":")

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if len(hosteroption) <= 1 or not hosteroption[1].isdigit():
                    continue

                o = hosteroption[0].lower()
                if o in option:
                    option[o] = hosteroption[1]

        for _ in xrange(5):
            post_data = {'apikey'        : self.getConfig("passkey"),
                         'prio'          : prio_option,
                         'confirm'       : confirm_option,
                         'maxtimeout'    : timeout_option,
                         'selfsolve'     : selfsolve_option,
                         'captchaperhour': cph_option,
                         'case-sensitive': case_sensitive_option,
                         'min_len'       : min_option,
                         'max_len'       : max_option,
                         'phrase'        : phrase_option,
                         'numeric'       : numeric_option,
                         'math'          : math_option,
                         'oldsource'     : pluginname,
                         'pyload'        : "1",
                         'source'        : "pyload",
                         'base64'        : "1",
                         'mouse'         : mouse,
                         'file-upload-01': data,
                         'action'        : "usercaptchaupload"}
            try:
                res = getURL(self.API_URL, post=post_data)
                if res:
                    break
            except BadHeader, e:
                sleep(3)

        if not res.isdigit():
            self.logError(_("Bad upload: %s") % res)
            return

        self.logInfo(_("NewCaptchaID from upload: %s : %s") % (res, task.captchaFile))

        task.data["ticket"] = res
        self.logInfo("result %s : %s" % (res, result))

        for _ in xrange(int(self.getConfig("timeout") / 5)):
            res2 = getURL(self.API_URL,
                          get={'apikey': self.getConfig("passkey"),
                               'id'    : res,
                               'pyload': "1",
                               'info'  : "1",
                               'source': "pyload",
                               'action': "usercaptchacorrectdata"})

            if not res2 or res2 == "NO DATA":
                sleep(5)
            else:
                break

        task.setResult(res2 or None)


    def newCaptchaTask(self, task):
        if not task.isTextual() and not task.isPositional():
            return

        elif not self.getConfig("passkey"):
            return

        elif self.core.isClientConnected() and not self.getConfig("force"):
            return

        credits = self.getCredits()

        if not credits:
            self.logError(_("Your Captcha 9kw.eu Account has not enough credits"))
            return

        queue = self.getConfig("queue")
        timeout = min(max(self.getConfig("timeout") * 60, 300), 3999)
        hoster_options = self.getConfig("hoster_options").split(";")
        pluginname = re.search(r'_([^_]*)_\d+.\w+', task.captchaFile).group(1)

	    if 1000 > queue > 10:
	 	    servercheck = getURL("http://www.9kw.eu/grafik/servercheck.txt")
            regex = re.compile("queue=(\d+)")

		    for _ in xrange(3):
		        if queue < regex.search(servercheck).group(1):
                    break

                sleep(10)

        for opt in hoster_options:
            details = opt.split(":")

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if (len(hosteroption) > 1
                    and hosteroption[0].lower() == 'timeout'
                    and hosteroption[1].isdigit()):
                    timeout = int(hosteroption[1])

        task.handler.append(self)
	
        task.setWaiting(timeout)
	
        start_new_thread(self._processCaptcha, (task,))


    def _captchaResponse(self, task, correct):
        if "ticket" not in task.data:
            return

        type = "correct" if correct else "refund"
        passkey = self.getConfig("passkey")

        for _ in xrange(3):
            res = getURL(self.API_URL,
                         get={'action' : "usercaptchacorrectback",
                              'apikey' : passkey,
                              'api_key': passkey,
                              'correct': "1" if correct else "2",
                              'pyload' : "1",
                              'source' : "pyload",
                              'id'     : task.data["ticket"]})

            if res is "OK":
                self.logInfo(_("Request %s: %s" % type) % res)
                return
            else:
                self.logDebug(_("Could not send %s request: %s" % type) % res)
                sleep(1)
            else:
                self.logDebug(_("No CaptchaID for %s request (task: %s)" % type) % task)


    def captchaCorrect(self, task):
        self._captchaResponse(self, task, True)


    def captchaInvalid(self, task):
        self._captchaResponse(self, task, False)
