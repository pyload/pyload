# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.core.manager import AccountManager
from tests.helper.stubs import Core, admin_user, normal_user
from unittest2 import TestCase

standard_library.install_aliases()


class TestAccountManager(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.core = Core()

    @classmethod
    def tearDownClass(cls):
        cls.core.db.shutdown()

    def setUp(self):
        self.db.purge_accounts()
        self.manager = AccountManager(self.pyload)

    def test_access(self):
        account = self.manager.create_account(
            "Http", "User", "somepw", admin_user.uid)

        assert account is self.manager.update_account(
            account.aid, "Http", "User", "newpw", admin_user)
        self.assertEqual(account.password, "newpw")

        assert self.manager.get_account(
            account.aid, "Http", admin_user) is account
        assert self.manager.get_account(
            account.aid, "Http", normal_user) is None

    def test_config(self):
        account = self.manager.create_account(
            "Http", "User", "somepw", admin_user.uid)
        info = account.to_info_data()

        self.assertEqual(info.config[0].name, "domain")
        self.assertEqual(info.config[0].value, "")
        self.assertEqual(account.get_config("domain"), "")

        account.set_config("domain", "df")

        info = account.to_info_data()
        self.assertEqual(info.config[0].value, "df")

        info.config[0].value = "new"

        account.update_config(info.config)
        self.assertEqual(account.get_config("domain"), "new")

    def test_shared(self):
        account = self.manager.create_account(
            "Http", "User", "somepw", admin_user.uid)

        assert self.manager.select_account("Http", admin_user) is account
        assert account.loginname == "User"

        assert self.manager.select_account("Something", admin_user) is None
        assert self.manager.select_account("Http", normal_user) is None

        account.shared = True

        assert self.manager.select_account("Http", normal_user) is account
        assert self.manager.select_account("sdf", normal_user) is None

        self.manager.remove_account(account.aid, "Http", admin_user.uid)

        assert self.manager.select_account("Http", admin_user) is None
