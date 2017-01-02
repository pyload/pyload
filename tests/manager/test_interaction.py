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

        self.assert_false(self.im.is_client_connected(self.ADMIN))
        self.assert_false(self.im.is_task_waiting(self.ADMIN))
        self.assert_empty(self.im.get_tasks(self.ADMIN))

    def test_notifications(self):
        n = self.im.create_notification("test", "notify")

        self.assert_true(self.im.is_task_waiting(self.ADMIN))
        self.assert_list_equal(self.im.get_tasks(self.ADMIN), [n])

        n.seen = True
        self.assert_false(self.im.is_task_waiting(self.ADMIN))

        for i in range(10):
            self.im.create_notification("title", "test")

        self.assert_equal(len(self.im.get_tasks(self.ADMIN)), 11)
        self.assert_false(self.im.get_tasks(self.USER))
        self.assert_false(self.im.get_tasks(self.ADMIN, Interaction.Query))


    def test_captcha(self):
        t = self.im.create_captcha_task("1", "png", "", owner=self.ADMIN)

        self.assert_equal(t.type, Interaction.Captcha)
        self.assert_list_equal(self.im.get_tasks(self.ADMIN), [t])
        self.assert_empty(self.im.get_tasks(self.USER))
        t.set_shared()
        self.assert_list_equal(self.im.get_tasks(self.USER), [t])

        t2 = self.im.create_captcha_task("2", "png", "", owner=self.USER)
        self.assert_true(self.im.is_task_waiting(self.USER))
        self.assert_empty(self.im.get_tasks(self.USER, Interaction.Query))
        self.im.remove_task(t)

        self.assert_list_equal(self.im.get_tasks(self.ADMIN), [t2])
        self.assert_is(self.im.get_task_by_id(t2.iid), t2)


    def test_query(self):
        t = self.im.create_query_task(InputType.Text, "text", owner=self.ADMIN)

        self.assert_equal(t.description, "text")
        self.assert_list_equal(self.im.get_tasks(self.ADMIN, Interaction.Query), [t])
        self.assert_empty(self.im.get_tasks(Interaction.Captcha))


    def test_clients(self):
        self.im.get_tasks(self.ADMIN, Interaction.Captcha)

        self.assert_true(self.im.is_client_connected(self.ADMIN))
        self.assert_false(self.im.is_client_connected(self.USER))


    def test_users(self):
        t = self.im.create_captcha_task("1", "png", "", owner=self.USER)
        self.assert_list_equal(self.im.get_tasks(self.ADMIN), [t])
