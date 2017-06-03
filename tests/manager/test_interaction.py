# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from builtins import range

from future import standard_library

from pyload.core.datatype import InputType, Interaction
from pyload.core.manager import ExchangeManager
from tests.helper.stubs import Core
from unittest2 import TestCase

standard_library.install_aliases()


class TestExchangeManager(TestCase):
    ADMIN = None
    USER = 1

    def assert_empty(self, list1):
        return self.assert_list_equal(list1, [])

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    def setUp(self):
        self.exm = ExchangeManager(self.pyload)

        self.assert_false(self.exm.is_client_connected(self.ADMIN))
        self.assert_false(self.exm.is_task_waiting(self.ADMIN))
        self.assert_empty(self.exm.get_tasks(self.ADMIN))

    def test_notifications(self):
        n = self.exm.create_notification("test", "notify")

        self.assert_true(self.exm.is_task_waiting(self.ADMIN))
        self.assert_list_equal(self.exm.get_tasks(self.ADMIN), [n])

        n.seen = True
        self.assert_false(self.exm.is_task_waiting(self.ADMIN))

        for i in range(10):
            self.exm.create_notification("title", "test")

        self.assertEqual(len(self.exm.get_tasks(self.ADMIN)), 11)
        self.assert_false(self.exm.get_tasks(self.USER))
        self.assert_false(self.exm.get_tasks(self.ADMIN, Interaction.Query))

    def test_captcha(self):
        tsk = self.exm.create_captcha_task("1", "png", "", owner=self.ADMIN)

        self.assertEqual(tsk.type, Interaction.Captcha)
        self.assert_list_equal(self.exm.get_tasks(self.ADMIN), [tsk])
        self.assert_empty(self.exm.get_tasks(self.USER))
        tsk.set_shared()
        self.assert_list_equal(self.exm.get_tasks(self.USER), [tsk])

        t2 = self.exm.create_captcha_task("2", "png", "", owner=self.USER)
        self.assert_true(self.exm.is_task_waiting(self.USER))
        self.assert_empty(self.exm.get_tasks(self.USER, Interaction.Query))
        self.exm.remove_task(tsk)

        self.assert_list_equal(self.exm.get_tasks(self.ADMIN), [t2])
        self.assert_is(self.exm.get_task_by_id(t2.iid), t2)

    def test_query(self):
        tsk = self.exm.create_query_task(
            InputType.Text, "text", owner=self.ADMIN)

        self.assertEqual(tsk.description, "text")
        self.assert_list_equal(self.exm.get_tasks(
            self.ADMIN, Interaction.Query), [tsk])
        self.assert_empty(self.exm.get_tasks(Interaction.Captcha))

    def test_clients(self):
        self.exm.get_tasks(self.ADMIN, Interaction.Captcha)

        self.assert_true(self.exm.is_client_connected(self.ADMIN))
        self.assert_false(self.exm.is_client_connected(self.USER))

    def test_users(self):
        tsk = self.exm.create_captcha_task("1", "png", "", owner=self.USER)
        self.assert_list_equal(self.exm.get_tasks(self.ADMIN), [tsk])
