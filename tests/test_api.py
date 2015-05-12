#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nose

import APIExerciser


class TestApi(object):

    def __init__(self):
        self.api = APIExerciser.APIExerciser(None, True, "TestUser", "pwhere")


    def test_login(self):
        assert self.api.api.login("crapp", "wrong pw") is False

    # takes really long, only test when needed


    @nose.tools.nottest
    def test_random(self):
        for _i in xrange(0, 100):
            self.api.testAPI()
