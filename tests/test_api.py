# -*- coding: utf-8 -*-

from builtins import object, range

from nose.tools import nottest

# from pyload.core.api import APIExerciser


class TestApi:
    def __init__(self):
        self.apiex = APIExerciser.APIExerciser(None, True, "TestUser", "pwhere")

    def test_login(self):
        assert self.apiex.api.login("crapp", "wrong pw") is False

    # takes really long, only test when needed
    @nottest
    def test_random(self):

        for i in range(0, 100):
            self.apiex.testAPI()
