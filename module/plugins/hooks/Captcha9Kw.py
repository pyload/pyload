# -*- coding: utf-8 -*-

from __future__ import with_statement

import base64
import re
import time
import urlparse

from module.network.HTTPRequest import BadHeader

from ..internal.Addon import Addon
from ..internal.misc import threaded, fs_encode


class Captcha9Kw(Addon):
    __name__ = "Captcha9Kw"
    __type__ = "hook"
    __version__ = "0.44"
    __status__ = "testing"

    __config__ = [("activated", "bool", "Activated", False),
                  ("check_client", "bool", "Don't use if client is connected", True),
                  ("confirm", "bool", "Confirm Captcha (cost +6 credits)", False),
                  ("captchaperhour", "int", "Captcha per hour", "9999"),
                  ("captchapermin", "int", "Captcha per minute", "9999"),
                  ("prio", "int", "Priority (max 10)(cost +0 -> +10 credits)", "0"),
                  ("queue", "int", "Max. Queue (max 999)", "50"),
                  ("hoster_options", "str", "Hoster options (format pluginname;prio 1;selfsolve 1;confirm 1;timeout 900|...)", ""),
                  ("selfsolve", "bool", "Selfsolve (manually solve your captcha in your 9kw client if active)", False),
                  ("solve_interactive", "bool", "Solve ReCaptcha Interactive (cost 30 credits)", True),
                  ("passkey", "password", "API key", ""),
                  ("timeout", "int", "Timeout in seconds (min 60, max 3999)", "900")]

    __description__ = """Send captchas to 9kw.eu"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.net"),
                   ("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahho[DOT]com")]

    API_URL = "https://www.9kw.eu/index.cgi"

    INTERACTIVE_TYPES = {'ReCaptcha': "recaptchav2",
                         'HCaptcha': "hcaptcha"}

    def get_credits(self):
        res = self.load(self.API_URL,
                        get={'apikey': self.config.get('passkey'),
                             'pyload': "1",
                             'source': "pyload",
                             'action': "usercaptchaguthaben"})

        if res.isdigit():
            self.log_info(_("%s credits left") % res)
            credits = self.info['credits'] = int(res)
            return credits
        else:
            self.log_error(res)
            return 0

    @threaded
    def _process_captcha(self, task):
        pluginname = task.captchaParams['plugin']
        if task.isInteractive() or task.isInvisible():
            url_p = urlparse.urlparse(task.captchaParams['url'])
            if  url_p.scheme not in ("http", "https"):
                self.log_error(_("Invalid url"))
                return

            post_data = {'pageurl': "%s://%s/" % (url_p.scheme, url_p.netloc),
                         'oldsource': self.INTERACTIVE_TYPES[task.captchaParams['captcha_plugin']],
                         'captchachoice': self.INTERACTIVE_TYPES[task.captchaParams['captcha_plugin']],
                         "isInvisible": "INVISIBLE" if task.isInvisible() else "NORMAL",
                         'data-sitekey': task.captchaParams['sitekey'],
                         'securetoken': task.captchaParams.get('securetoken', "")}

        else:
            try:
                with open(fs_encode(task.captchaParams['file']), 'rb') as f:
                    data = f.read()

            except IOError, e:
                self.log_error(e)
                return

            post_data = {'file-upload-01': base64.b64encode(data),
                         'oldsource': pluginname}

        option = {'min': 2,
                  'max': 50,
                  'phrase': 0,
                  'numeric': 0,
                  'case_sensitive': 0,
                  'math': 0,
                  'prio': min(max(self.config.get('prio'), 0), 10),
                  'confirm': self.config.get('confirm'),
                  'timeout': min(max(self.config.get('timeout'), 300), 3999),
                  'selfsolve': self.config.get('selfsolve'),
                  'cph': self.config.get('captchaperhour'),
                  'cpm': self.config.get('captchapermin')}

        for opt in [x for x in self.config.get('hoster_options', "").split('|') if x]:
            details = map(str.strip, opt.split(';'))

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split(" ")

                if len(hosteroption) < 2 or not hosteroption[1].isdigit():
                    continue

                o = hosteroption[0].lower()
                if o in option:
                    option[o] = hosteroption[1]

            break

        post_data.update({'apikey': self.config.get('passkey'),
                          'prio': option['prio'],
                          'confirm': option['confirm'],
                          'maxtimeout': option['timeout'],
                          'selfsolve': option['selfsolve'],
                          'captchaperhour': option['cph'],
                          'captchapermin': option['cpm'],
                          'case-sensitive': option['case_sensitive'],
                          'min_len': option['min'],
                          'max_len': option['max'],
                          'phrase': option['phrase'],
                          'numeric': option['numeric'],
                          'math': option['math'],
                          'pyload': 1,
                          'source': "pyload",
                          'base64': 0 if task.isInteractive() else 1,
                          'mouse': 1 if task.isPositional() else 0,
                          "interactive": 1 if task.isInteractive() else 0,
                          'action': "usercaptchaupload"})

        for _i in range(5):
            try:
                res = self.load(self.API_URL, post=post_data)

            except BadHeader, e:
                res = e.content
                time.sleep(3)

            else:
                if res and res.isdigit():
                    break

        else:
            self.log_error(_("Bad request: %s") % res)
            return

        self.log_debug("NewCaptchaID ticket: %s" % res, task.captchaParams.get('file', ""))

        task.data['ticket'] = res

        for _i in range(int(self.config.get('timeout') / 5)):
            result = self.load(self.API_URL,
                               get={'apikey': self.config.get('passkey'),
                                    'id': res,
                                    'pyload': "1",
                                    'info': "1",
                                    'source': "pyload",
                                    'action': "usercaptchacorrectdata"})

            if not result or result == "NO DATA":
                time.sleep(5)
            else:
                break

        else:
            self.log_debug("Could not send request: %s" % res)
            result = None

        self.log_info(_("Captcha result for ticket %s: %s") % (res, result))

        task.setResult(result)

    def captcha_task(self, task):
        if not hasattr(task, "isInvisible"):
            self.log_error(_("Please update pyLoad's core to support invisible captcha"))
            task.isInvisible = lambda : False

        if task.isInteractive() or task.isInvisible():
            if task.captchaParams['captcha_plugin'] not in self.INTERACTIVE_TYPES.keys() or self.config.get('solve_interactive') is False:
                return
        else:
            if not task.isTextual() and not task.isPositional():
                return

        if not self.config.get('passkey'):
            return

        if self.pyload.isClientConnected() and self.config.get('check_client'):
            return

        credits = self.get_credits()

        if credits <= 0:
            self.log_error(_("Your captcha 9kw.eu account has not enough credits"))
            return

        max_queue = min(self.config.get('queue'), 999)
        timeout = min(max(self.config.get('timeout'), 300), 3999)
        pluginname = task.captchaParams['plugin']

        for _i in range(5):
            servercheck = self.load("http://www.9kw.eu/grafik/servercheck.txt")
            if max_queue > int(re.search(r'queue=(\d+)', servercheck).group(1)):
                break

            time.sleep(10)

        else:
            self.log_error(_("Too many captchas in queue"))
            return

        for opt in [x for x in self.config.get('hoster_options', "").split('|') if x]:
            details = map(str.strip, opt.split(':'))

            if not details or details[0].lower() != pluginname.lower():
                continue

            for d in details:
                hosteroption = d.split("=")

                if len(hosteroption) > 1 and \
                   hosteroption[0].lower() == "timeout" and \
                   hosteroption[1].isdigit():
                    timeout = int(hosteroption[1])

            break

        task.handler.append(self)

        task.setWaiting(timeout)

        self._process_captcha(task)

    def _captcha_response(self, task, correct):
        request_type = "correct" if correct else "refund"

        if 'ticket' not in task.data:
            self.log_debug("No CaptchaID for %s request (task: %s)" % (request_type, task))
            return

        passkey = self.config.get('passkey')

        for _i in range(3):
            res = self.load(self.API_URL,
                            get={'action': "usercaptchacorrectback",
                                 'apikey': passkey,
                                 'api_key': passkey,
                                 'correct': "1" if correct else "2",
                                 'pyload': "1",
                                 'source': "pyload",
                                 'id': task.data['ticket']})

            self.log_debug("Request %s: %s" % (request_type, res))

            if res == "OK":
                break

            time.sleep(5)
        else:
            self.log_debug("Could not send %s request: %s" % (request_type, res))

    def captcha_correct(self, task):
        self._captcha_response(task, True)

    def captcha_invalid(self, task):
        self._captcha_response(task, False)
