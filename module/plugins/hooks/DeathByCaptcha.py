# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from base64 import b64encode
from pycurl import FORM_FILE, HTTPHEADER
from thread import start_new_thread
from time import sleep

from module.common.json_layer import json_loads
from module.network.HTTPRequest import BadHeader
from module.network.RequestFactory import getRequest
from module.plugins.Hook import Hook


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

    def getCode(self):
        return self.err

    def getDesc(self):
        if self.err in self.DBC_ERRORS.keys():
            return self.DBC_ERRORS[self.err]
        else:
            return self.err

    def __str__(self):
        return "<DeathByCaptchaException %s>" % self.err

    def __repr__(self):
        return "<DeathByCaptchaException %s>" % self.err


class DeathByCaptcha(Hook):
    __name__ = "DeathByCaptcha"
    __type__ = "hook"
    __version__ = "0.03"

    __config__ = [("activated", "bool", "Activated", False),
                  ("username", "str", "Username", ""),
                  ("passkey", "password", "Password", ""),
                  ("force", "bool", "Force DBC even if client is connected", False)]

    __description__ = """Send captchas to DeathByCaptcha.com"""
    __author_name__ = ("RaNaN", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "zoidberg@mujmail.cz")

    API_URL = "http://api.dbcapi.me/api/"


    def setup(self):
        self.info = {}

    def call_api(self, api="captcha", post=False, multipart=False):
        req = getRequest()
        req.c.setopt(HTTPHEADER, ["Accept: application/json", "User-Agent: pyLoad %s" % self.core.version])

        if post:
            if not isinstance(post, dict):
                post = {}
            post.update({"username": self.getConfig("username"),
                         "password": self.getConfig("passkey")})

        response = None
        try:
            json = req.load("%s%s" % (self.API_URL, api),
                            post=post,
                            multipart=multipart)
            self.logDebug(json)
            response = json_loads(json)

            if "error" in response:
                raise DeathByCaptchaException(response['error'])
            elif "status" not in response:
                raise DeathByCaptchaException(str(response))

        except BadHeader, e:
            if 403 == e.code:
                raise DeathByCaptchaException('not-logged-in')
            elif 413 == e.code:
                raise DeathByCaptchaException('invalid-captcha')
            elif 503 == e.code:
                raise DeathByCaptchaException('service-overload')
            elif e.code in (400, 405):
                raise DeathByCaptchaException('invalid-request')
            else:
                raise

        finally:
            req.close()

        return response

    def getCredits(self):
        response = self.call_api("user", True)

        if 'is_banned' in response and response['is_banned']:
            raise DeathByCaptchaException('banned')
        elif 'balance' in response and 'rate' in response:
            self.info.update(response)
        else:
            raise DeathByCaptchaException(response)

    def getStatus(self):
        response = self.call_api("status", False)

        if 'is_service_overloaded' in response and response['is_service_overloaded']:
            raise DeathByCaptchaException('service-overload')

    def submit(self, captcha, captchaType="file", match=None):
        #workaround multipart-post bug in HTTPRequest.py
        if re.match("^[A-Za-z0-9]*$", self.getConfig("passkey")):
            multipart = True
            data = (FORM_FILE, captcha)
        else:
            multipart = False
            with open(captcha, 'rb') as f:
                data = f.read()
            data = "base64:" + b64encode(data)

        response = self.call_api("captcha", {"captchafile": data}, multipart)

        if "captcha" not in response:
            raise DeathByCaptchaException(response)
        ticket = response['captcha']

        for _ in xrange(24):
            sleep(5)
            response = self.call_api("captcha/%d" % ticket, False)
            if response['text'] and response['is_correct']:
                break
        else:
            raise DeathByCaptchaException('timed-out')

        result = response['text']
        self.logDebug("result %s : %s" % (ticket, result))

        return ticket, result

    def newCaptchaTask(self, task):
        if "service" in task.data:
            return False

        if not task.isTextual():
            return False

        if not self.getConfig("username") or not self.getConfig("passkey"):
            return False

        if self.core.isClientConnected() and not self.getConfig("force"):
            return False

        try:
            self.getStatus()
            self.getCredits()
        except DeathByCaptchaException, e:
            self.logError(e.getDesc())
            return False

        balance, rate = self.info['balance'], self.info['rate']
        self.logInfo("Account balance: US$%.3f (%d captchas left at %.2f cents each)" % (balance / 100,
                                                                                         balance // rate, rate))

        if balance > rate:
            task.handler.append(self)
            task.data['service'] = self.__name__
            task.setWaiting(180)
            start_new_thread(self.processCaptcha, (task,))

    def captchaInvalid(self, task):
        if task.data['service'] == self.__name__ and "ticket" in task.data:
            try:
                response = self.call_api("captcha/%d/report" % task.data['ticket'], True)
            except DeathByCaptchaException, e:
                self.logError(e.getDesc())
            except Exception, e:
                self.logError(e)

    def processCaptcha(self, task):
        c = task.captchaFile
        try:
            ticket, result = self.submit(c)
        except DeathByCaptchaException, e:
            task.error = e.getCode()
            self.logError(e.getDesc())
            return

        task.data['ticket'] = ticket
        task.setResult(result)
