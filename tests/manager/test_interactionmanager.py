# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from builtins import range
from unittest import TestCase

from tests.helper.stubs import Core

from pyload.Api import InputType, Interaction
from pyload.interaction.interactionmanager import InteractionManager


class TestInteractionManager(TestCase):
    ADMIN = None
    USER = 1

    def assertEmpty(self, list1):
        return self.assertListEqual(list1, [])

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def setUp(self):
        self.im = InteractionManager(self.pyload)

        self.assertFalse(self.im.isClientConnected(self.ADMIN))
        self.assertFalse(self.im.isTaskWaiting(self.ADMIN))
        self.assertEmpty(self.im.getTasks(self.ADMIN))

    def test_notifications(self):
        n = self.im.createNotification("test", "notify")

        self.assertTrue(self.im.isTaskWaiting(self.ADMIN))
        self.assertListEqual(self.im.getTasks(self.ADMIN), [n])

        n.seen = True
        self.assertFalse(self.im.isTaskWaiting(self.ADMIN))

        for i in range(10):
            self.im.createNotification("title", "test")

        self.assertEqual(len(self.im.getTasks(self.ADMIN)), 11)
        self.assertFalse(self.im.getTasks(self.USER))
        self.assertFalse(self.im.getTasks(self.ADMIN, Interaction.Query))


    def test_captcha(self):
        t = self.im.createCaptchaTask("1", "png", "", owner=self.ADMIN)

        self.assertEqual(t.type, Interaction.Captcha)
        self.assertListEqual(self.im.getTasks(self.ADMIN), [t])
        self.assertEmpty(self.im.getTasks(self.USER))
        t.setShared()
        self.assertListEqual(self.im.getTasks(self.USER), [t])

        t2 = self.im.createCaptchaTask("2", "png", "", owner=self.USER)
        self.assertTrue(self.im.isTaskWaiting(self.USER))
        self.assertEmpty(self.im.getTasks(self.USER, Interaction.Query))
        self.im.removeTask(t)

        self.assertListEqual(self.im.getTasks(self.ADMIN), [t2])
        self.assertIs(self.im.getTaskByID(t2.iid), t2)


    def test_query(self):
        t = self.im.createQueryTask(InputType.Text, "text", owner=self.ADMIN)

        self.assertEqual(t.description, "text")
        self.assertListEqual(self.im.getTasks(self.ADMIN, Interaction.Query), [t])
        self.assertEmpty(self.im.getTasks(Interaction.Captcha))


    def test_clients(self):
        self.im.getTasks(self.ADMIN, Interaction.Captcha)

        self.assertTrue(self.im.isClientConnected(self.ADMIN))
        self.assertFalse(self.im.isClientConnected(self.USER))


    def test_users(self):
        t = self.im.createCaptchaTask("1", "png", "", owner=self.USER)
        self.assertListEqual(self.im.getTasks(self.ADMIN), [t])
