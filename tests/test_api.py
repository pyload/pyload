# -*- coding: utf-8 -*-

from builtins import object, range

from nose.tools import nottest
from pyload.common import APIExerciser


class TestApi(object):

    def __init__(self):
        self.api = APIExerciser.APIExerciser(None, True, "TestUser", "pwhere")

    def test_login(self):
        assert self.api.api.login("crapp", "wrong pw") is False

    # takes really long, only test when needed
    @nottest
    def test_random(self):

        for i in range(0, 100):
            self.api.testAPI()
