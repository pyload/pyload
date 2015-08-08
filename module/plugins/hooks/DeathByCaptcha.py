# -*- coding: utf-8 -*-

from __future__ import with_statement

import pycurl
import re
import time

from base64 import b64encode

from module.common.json_layer import json_loads
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest as get_request
from module.plugins.internal.Hook import Hook, threaded


class DeathByCaptchaException(Exception):
    DBC_ERRORS = {'not-logged-in': 'Access denied, check your credentials',
                  'invalid-credentials': 'Access denied, check your credentials',
                  'banned': 'Access denied, account is suspended',
                  'insufficient-funds': 'Insufficient account balance to decrypt CAPTCHA',
                  'invalid-captcha': 'CAPTCHA is not a valid image',
                  'service-overload': 'CAPTCHA was rejected due to service overload, try again later',
                  'invalid-request': 'Invalid request',
                  'timed-out': 'No CAPTCHA solution received in time'}


    def __init__(self, err):
        self.err = err


    def get_code(self):
        return self.err


    def get_desc(self):
        if self.err in self.DBC_ERRORS.keys():
            return self.DBC_ERRORS[self.err]
        else:
            return self.err


    def __str__(self):
        return "<DeathByCaptchaException %s>" % self.err


    def __repr__(self):
        return "<DeathByCaptchaException %s>" % self.err


class DeathByCaptcha(Hook):
    __name__    = "DeathByCaptcha"
    __type__    = "hook"
    __version__ = "0.08"
    __status__  = "testing"

    __config__ = [("username"    , "str"     , "Username"                        , ""  ),
                  ("password"    , "password", "Password"                        , ""  ),
                  ("check_client", "bool"    , "Don't use if client is connected", True)]

    __description__ = """Send captchas to DeathByCaptcha.com"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN"   , "RaNaN@pyload.org"   ),
                       ("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://api.dbcapi.me/api/"


    def api_response(self, api="captcha", post=False, multipart=False):
        req = get_request()
        req.c.setopt(pycurl.HTTPHEADER, ["Accept: application/json", "User-Agent: pyLoad %s" % self.pyload.version])

        if post:
            if not isinstance(post, dict):
                post = {}
            post.update({'username': self.get_config('username'),
                         'password': self.get_config('password')})

        res = None
        try:
            json = self.load("%s%s" % (self.API_URL, api),
                             post=post,
                             multipart=multipart,
                             req=req)

            self.log_debug(json)
            res = json_loads(json)

            if "error" in res:
                raise DeathByCaptchaException(res['error'])
            elif "status" not in res:
                raise DeathByCaptchaException(str(res))

        except BadHeader, e:
            if 403 is e.code:
                raise DeathByCaptchaException('not-logged-in')
            elif 413 is e.code:
                raise DeathByCaptchaException('invalid-captcha')
            elif 503 is e.code:
                raise DeathByCaptchaException('service-overload')
            elif e.code in (400, 405):
                raise DeathByCaptchaException('invalid-request')
            else:
                raise

        finally:
            req.close()

        return res


    def get_credits(self):
        res = self.api_response("user", True)

        if 'is_banned' in res and res['is_banned']:
            raise DeathByCaptchaException('banned')
        elif 'balance' in res and 'rate' in res:
            self.info.update(res)
        else:
            raise DeathByCaptchaException(res)


    def get_status(self):
        res = self.api_response("status", False)

        if 'is_service_overloaded' in res and res['is_service_overloaded']:
            raise DeathByCaptchaException('service-overload')


    def submit(self, captcha, captchaType="file", match=None):
        #@NOTE: Workaround multipart-post bug in HTTPRequest.py
        if re.match("^\w*$", self.get_config('password')):
            multipart = True
            data = (pycurl.FORM_FILE, captcha)
        else:
            multipart = False
            with open(captcha, 'rb') as f:
                data = f.read()
            data = "base64:" + b64encode(data)

        res = self.api_response("captcha", {'captchafile': data}, multipart)

        if "captcha" not in res:
            raise DeathByCaptchaException(res)
        ticket = res['captcha']

        for _i in xrange(24):
            time.sleep(5)
            res = self.api_response("captcha/%d" % ticket, False)
            if res['text'] and res['is_correct']:
                break
        else:
            raise DeathByCaptchaException('timed-out')

        result = res['text']
        self.log_debug("Result %s : %s" % (ticket, result))

        return ticket, result


    def captcha_task(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.get_config('username') or not self.get_config('password'):
            return False

        if self.pyload.isClientConnected() and self.get_config('check_client'):
            return False

        try:
            self.get_status()
            self.get_credits()
        except DeathByCaptchaException, e:
            self.log_error(e.getDesc())
            return False

        balance, rate = self.info['balance'], self.info['rate']
        self.log_info(_("Account balance"),
                     _("US$%.3f (%d captchas left at %.2f cents each)") % (balance / 100,
                                                                           balance // rate, rate))

        if balance > rate:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(180)
            self._process_captcha(task)


    def captcha_invalid(self, task):
        if task.data['service'] is self.__name__ and "ticket" in task.data:
            try:
                res = self.api_response("captcha/%d/report" % task.data['ticket'], True)

            except DeathByCaptchaException, e:
                self.log_error(e.getDesc())

            except Exception, e:
                self.log_error(e)


    @threaded
    def _process_captcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except DeathByCaptchaException, e:
            task.error = e.get_code()
            self.log_error(e.getDesc())
            return

        task.data['ticket'] = ticket
        task.setResult(result)
