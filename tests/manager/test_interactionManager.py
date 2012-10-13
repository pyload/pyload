# -*- coding: utf-8 -*-

from unittest import TestCase
from tests.helper.Stubs import Core

from module.Api import Input, Output
from module.interaction.InteractionManager import InteractionManager

class TestInteractionManager(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def setUp(self):
        self.im = InteractionManager(self.core)


    def test_notifications(self):

        n = self.im.createNotification("test", "notify")
        assert self.im.getNotifications() == [n]

        for i in range(10):
            self.im.createNotification("title", "test")

        assert len(self.im.getNotifications()) == 11


    def test_captcha(self):
        assert self.im.getTask() is None

        t = self.im.newCaptchaTask("1", "", "")
        assert t.output == Output.Captcha
        self.im.handleTask(t)
        assert t is self.im.getTask()

        t2 = self.im.newCaptchaTask("2", "", "")
        self.im.handleTask(t2)

        assert self.im.getTask(Output.Query) is None
        assert self.im.getTask() is t

        self.im.removeTask(t)
        assert self.im.getTask() is t2

        self.im.getTaskByID(t2.iid)
        assert self.im.getTask() is None


    def test_query(self):
        assert self.im.getTask() is None
        t = self.im.newQueryTask(Input.Text, None, "text")
        assert t.description == "text"
        self.im.handleTask(t)

        assert self.im.getTask(Output.Query) is t
        assert self.im.getTask(Output.Captcha) is None