#!/usr/bin/env python
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
    
    @author: mkaay
"""

from json import loads
from urllib2 import build_opener
from MultipartPostHandler import MultipartPostHandler

PYLOAD_KEY = "9f65e7f381c3af2b076ea680ae96b0b7"

opener = build_opener(MultipartPostHandler)

class CaptchaTraderException(Exception):
    def __init__(self, err):
        self.err = err
    
    def getCode(self):
        return self.err
    
    def __str__(self):
        return "<CaptchaTraderException %s>" % self.err
    
    def __repr__(self):
        return "<CaptchaTraderException %s>" % self.err

class CaptchaTrader():
    SUBMIT_URL = "http://captchatrader.com/api/submit"
    RESPOND_URL = "http://captchatrader.com/api/respond"
    GETCREDITS_URL = "http://captchatrader.com/api/get_credits/username:%(user)s/password:%(password)s/"
    
    def __init__(self, user, password, api_key=PYLOAD_KEY):
        self.api_key = api_key
        self.user = user
        self.password = password
    
    def getCredits(self):
        json = opener.open(CaptchaTrader.GETCREDITS_URL % {"user":self.user, "password":self.password}).read()
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])
        else:
            return response[1]
    
    def submit(self, captcha, captchaType="file", match=None):
        if not self.api_key:
            raise CaptchaTraderException("No API Key Specified!")
        if type(captcha) == str and captchaType == "file":
            raise CaptchaTraderException("Invalid Type")
        assert captchaType in ("file", "url-jpg", "url-jpeg", "url-png", "url-bmp")
        json = opener.open(CaptchaTrader.SUBMIT_URL, data={"api_key":self.api_key,
                                                       "username":self.user,
                                                       "password":self.password,
                                                       "value":captcha,
                                                       "type":captchaType}).read()
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])
        
        class Result():
            def __init__(self, api, ticket, result):
                self.api = api
                self.ticket = ticket
                self.result = result
            
            def getTicketID(self):
                return self.ticket
            
            def getResult(self):
                return self.result
            
            def success(self):
                self.sendResponse(True)
            
            def fail(self):
                self.sendResponse(False)
            
            def sendResponse(self, success):
                self.api.respond(self.ticket, success)
        
        return Result(self, response[0], response[1])
    
    def respond(self, ticket, success):
        json = opener.open(CaptchaTrader.RESPOND_URL, data={"is_correct":1 if success else 0,
                                                       "username":self.user,
                                                       "password":self.password,
                                                       "ticket":ticket}).read()
        response = loads(json)
        if response[0] < 0:
            raise CaptchaTraderException(response[1])

if __name__ == "__main__":
    ct = CaptchaTrader("<user>", "<password>")
    print "credits", ct.getCredits()
    
    print "testing..."
    
    result = ct.submit(open("test_captcha.jpg", "rb"))
    print "result", result.getResult()
    if result.getResult() == "bettand trifting":
        result.success()
        print "captcha recognized"
    else:
        result.fail()
        print "captcha not recognized"
