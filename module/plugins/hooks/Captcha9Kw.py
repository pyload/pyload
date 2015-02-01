# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from base64 import b64encode
from time import sleep

from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getURL

from module.plugins.Hook import Hook, threaded


class Captcha9Kw(Hook):
    __name__    = "Captcha9Kw"
    __type__    = "hook"
    __version__ = "0.28"

    __config__ = [("ssl"           , "bool"    , "Use HTTPS"                                                                       , True                                                               ),
                  ("force"         , "bool"    , "Force captcha resolving even if client is connected"                             , True                                                               ),
                  ("confirm"       , "bool"    , "Confirm Captcha (cost +6 credits)"                                               , False                                                              ),
                  ("captchaperhour", "int"     , "Captcha per hour"                                                                , "9999"                                                             ),
                  ("captchapermin" , "int"     , "Captcha per minute"                                                              , "9999"                                                             ),
                  ("prio"          , "int"     , "Priority (max 10)(cost +0 -> +10 credits)"                                       , "0"                                                                ),
                  ("queue"         , "int"     , "Max. Queue (max 999)"                                                            , "50"                                                               ),
                  ("hoster_options", "string"  , "Hoster options (format: pluginname:prio=1:selfsolfe=1:confirm=1:timeout=900|...)", "ShareonlineBiz:prio=0:timeout=999 | UploadedTo:prio=0:timeout=999"),
                  ("selfsolve"     , "bool"    , "Selfsolve (manually solve your captcha in your 9kw client if active)"            , "0"                                                                ),
                  ("passkey"       , "password", "API key"                                                                         , ""                                                                 ),
                  ("timeout"       , "int"     , "Timeout in seconds (min 60, max 3999)"                                           , "900"                                                              )]

    __description__ = """Send captchas to 9kw.eu"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    API_URL = "http://www.9kw.eu/index.cgi"


    #@TODO: Remove in 0.4.10
    def initPeriodical(self):
        pass


    def setup(self):
        self.info = {}  #@TODO: Remove in 0.4.10
        if self.getConfig("ssl"):
            self.API_URL = self.API_URL.replace("http://", "https://")


    def getCredits(self):
        res = getURL(self.API_URL,
                     get={'apikey': self.getConfig("passkey"),
                          'pyload': "1",
                          'source': "pyload",
                          'action': "usercaptchaguthaben"})

        if res.isdigit():
            self.logInfo(_("%s credits left") % res)
            credits = self.info['credits'] = int(res)
            return credits
        else:
            self.logError(res)
            return 0


    @threaded
    def _processCaptcha(self, task):
        try:
            with open(task.captchaFile, 'rb') as f:
                data = f.read()

        except IOError, e:
            self.logError(e)
            return

        pluginname = re.search(r'_([^_]*)_\d+.\w+', task.captchaFile).group(1)
        option     = {'min'           : 2,
                      'max'           : 50,
                      'phrase'        : 0,
                      'numeric'       : 0,
                      'case_sensitive': 0,
                      'math'          : 0,
                      'prio'          : min(max(self.getConfig("prio"), 0), 10),
                      'confirm'       : self.getConfig("confirm"),
                      'timeout'       : min(max(self.getConfig("timeout"), 300), 3999),
                      'selfsolve'     : self.getConfig("selfsolve"),
                      'cph'           : self.getConfig("captchaperhour"),
                      'cpm'           : self.getConfig("captchapermin")}

        for opt in str(self.getConfig("hoster_options").split('|')):

            details = map(str.strip, opt.split(':'))

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if len(hosteroption) < 2 or not hosteroption[1].isdigit():
                    continue

                o = hosteroption[0].lower()
                if o in option:
                    option[o] = hosteroption[1]

            break

        post_data = {'apikey'        : self.getConfig("passkey"),
                     'prio'          : option['prio'],
                     'confirm'       : option['confirm'],
                     'maxtimeout'    : option['timeout'],
                     'selfsolve'     : option['selfsolve'],
                     'captchaperhour': option['cph'],
                     'captchapermin' : option['cpm'],
                     'case-sensitive': option['case_sensitive'],
                     'min_len'       : option['min'],
                     'max_len'       : option['max'],
                     'phrase'        : option['phrase'],
                     'numeric'       : option['numeric'],
                     'math'          : option['math'],
                     'oldsource'     : pluginname,
                     'pyload'        : "1",
                     'source'        : "pyload",
                     'base64'        : "1",
                     'mouse'         : 1 if task.isPositional() else 0,
                     'file-upload-01': b64encode(data),
                     'action'        : "usercaptchaupload"}

        for _i in xrange(5):
            try:
                res = getURL(self.API_URL, post=post_data)
            except BadHeader, e:
                sleep(3)
            else:
                if res and res.isdigit():
                    break
        else:
            self.logError(_("Bad upload: %s") % res)
            return

        self.logDebug(_("NewCaptchaID ticket: %s") % res, task.captchaFile)

        task.data["ticket"] = res

        for _i in xrange(int(self.getConfig("timeout") / 5)):
            result = getURL(self.API_URL,
                            get={'apikey': self.getConfig("passkey"),
                                 'id'    : res,
                                 'pyload': "1",
                                 'info'  : "1",
                                 'source': "pyload",
                                 'action': "usercaptchacorrectdata"})

            if not result or result == "NO DATA":
                sleep(5)
            else:
                break
        else:
            self.logDebug("Could not send request: %s" % res)
            result = None

        self.logInfo(_("Captcha result for ticket %s: %s") % (res, result))

        task.setResult(result)


    def newCaptchaTask(self, task):
        if not task.isTextual() and not task.isPositional():
            return

        if not self.getConfig("passkey"):
            return

        if self.core.isClientConnected() and not self.getConfig("force"):
            return

        credits = self.getCredits()

        if not credits:
            self.logError(_("Your captcha 9kw.eu account has not enough credits"))
            return

        queue = min(self.getConfig("queue"), 999)
        timeout = min(max(self.getConfig("timeout"), 300), 3999)
        pluginname = re.search(r'_([^_]*)_\d+.\w+', task.captchaFile).group(1)

        for _i in xrange(5):
            servercheck = getURL("http://www.9kw.eu/grafik/servercheck.txt")
            if queue < re.search(r'queue=(\d+)', servercheck).group(1):
                break

            sleep(10)
        else:
            self.fail(_("Too many captchas in queue"))

        for opt in str(self.getConfig("hoster_options").split('|')):
            details = map(str.strip, opt.split(':'))

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if (len(hosteroption) > 1
                    and hosteroption[0].lower() == 'timeout'
                    and hosteroption[1].isdigit()):
                    timeout = int(hosteroption[1])

            break

        task.handler.append(self)

        task.setWaiting(timeout)

        self._processCaptcha(task)


    def _captchaResponse(self, task, correct):
        type = "correct" if correct else "refund"

        if 'ticket' not in task.data:
            self.logDebug("No CaptchaID for %s request (task: %s)" % (type, task))
            return

        passkey = self.getConfig("passkey")

        for _i in xrange(3):
            res = getURL(self.API_URL,
                         get={'action' : "usercaptchacorrectback",
                              'apikey' : passkey,
                              'api_key': passkey,
                              'correct': "1" if correct else "2",
                              'pyload' : "1",
                              'source' : "pyload",
                              'id'     : task.data["ticket"]})

            self.logDebug("Request %s: %s" % (type, res))

            if res == "OK":
                break

            sleep(5)
        else:
            self.logDebug("Could not send %s request: %s" % (type, res))


    def captchaCorrect(self, task):
        self._captchaResponse(task, True)


    def captchaInvalid(self, task):
        self._captchaResponse(task, False)
