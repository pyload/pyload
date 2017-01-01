# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import range
from unittest import TestCase

from tests.helper.stubs import Core

from pyload.api import InputType, Interaction
from pyload.interaction.interactionmanager import InteractionManager


class TestInteractionManager(TestCase):
    ADMIN = None
    USER = 1

    def assertEmpty(self, list1):
        return self.assert_list_equal(list1, [])

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def setUp(self):
        self.im = InteractionManager(self.pyload)

        self.assert_false(self.im.isClientConnected(self.ADMIN))
        self.assert_false(self.im.isTaskWaiting(self.ADMIN))
        self.assert_empty(self.im.getTasks(self.ADMIN))

    def test_notifications(self):
        n = self.im.createNotification("test", "notify")

        self.assert_true(self.im.isTaskWaiting(self.ADMIN))
        self.assert_list_equal(self.im.getTasks(self.ADMIN), [n])

        n.seen = True
        self.assert_false(self.im.isTaskWaiting(self.ADMIN))

        for i in range(10):
            self.im.createNotification("title", "test")

        self.assert_equal(len(self.im.getTasks(self.ADMIN)), 11)
        self.assert_false(self.im.getTasks(self.USER))
        self.assert_false(self.im.getTasks(self.ADMIN, Interaction.Query))


    def test_captcha(self):
        t = self.im.createCaptchaTask("1", "png", "", owner=self.ADMIN)

        self.assert_equal(t.type, Interaction.Captcha)
        self.assert_list_equal(self.im.getTasks(self.ADMIN), [t])
        self.assert_empty(self.im.getTasks(self.USER))
        t.setShared()
        self.assert_list_equal(self.im.getTasks(self.USER), [t])

        t2 = self.im.createCaptchaTask("2", "png", "", owner=self.USER)
        self.assert_true(self.im.isTaskWaiting(self.USER))
        self.assert_empty(self.im.getTasks(self.USER, Interaction.Query))
        self.im.removeTask(t)

        self.assert_list_equal(self.im.getTasks(self.ADMIN), [t2])
        self.assert_is(self.im.getTaskByID(t2.iid), t2)


    def test_query(self):
        t = self.im.createQueryTask(InputType.Text, "text", owner=self.ADMIN)

        self.assert_equal(t.description, "text")
        self.assert_list_equal(self.im.getTasks(self.ADMIN, Interaction.Query), [t])
        self.assert_empty(self.im.getTasks(Interaction.Captcha))


    def test_clients(self):
        self.im.getTasks(self.ADMIN, Interaction.Captcha)

        self.assert_true(self.im.isClientConnected(self.ADMIN))
        self.assert_false(self.im.isClientConnected(self.USER))


    def test_users(self):
        t = self.im.createCaptchaTask("1", "png", "", owner=self.USER)
        self.assert_list_equal(self.im.getTasks(self.ADMIN), [t])
