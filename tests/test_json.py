#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import urllib
import urllib2


url = "http://localhost:8001/api/%s"


class TestJson(object):

    def call(self, name, post=None):
        if not post: post = {}
        post['session'] = self.key
        u = urllib2.urlopen(url % name, data=urlencode(post))
        return json.loads(u.read())


    def setUp(self):
        u = urllib2.urlopen(url % "login", data=urlencode({"username": "TestUser", "password": "pwhere"}))
        self.key = json.loads(u.read())
        assert self.key is not False


    def test_wronglogin(self):
        u = urllib2.urlopen(url % "login", data=urlencode({"username": "crap", "password": "wrongpw"}))
        assert json.loads(u.read()) is False


    def test_access(self):
        try:
            urllib2.urlopen(url % "getServerVersion")
        except urllib2.HTTPError, e:
            assert e.code == 403
        else:
            assert False


    def test_status(self):
        ret = self.call("statusServer")
        logging.log(1, str(ret))
        assert "pause" in ret
        assert "queue" in ret


    def test_unknown_method(self):
        try:
            self.call("notExisting")
        except urllib2.HTTPError, e:
            assert e.code == 404
        else:
            assert False
