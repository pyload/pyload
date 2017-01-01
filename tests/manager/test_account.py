# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from unittest import TestCase

from tests.helper.stubs import Core, adminUser, normalUser

from pyload.manager.account import AccountManager


class TestAccountManager(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = Core()
        cls.db = cls.core.db

    @classmethod
    def tearDownClass(cls):
        cls.db.shutdown()

    def setUp(self):
        self.db.purgeAccounts()
        self.manager = AccountManager(self.pyload)

    def test_access(self):
        account = self.manager.create_account("Http", "User", "somepw", adminUser.uid)

        assert account is self.manager.update_account(account.aid, "Http", "User", "newpw", adminUser)
        self.assert_equal(account.password, "newpw")

        assert self.manager.get_account(account.aid, "Http", adminUser) is account
        assert self.manager.get_account(account.aid, "Http", normalUser) is None


    def test_config(self):
        account = self.manager.create_account("Http", "User", "somepw", adminUser.uid)
        info = account.toInfoData()

        self.assert_equal(info.config[0].name, "domain")
        self.assert_equal(info.config[0].value, "")
        self.assert_equal(account.getConfig("domain"), "")

        account.setConfig("domain", "df")

        info = account.toInfoData()
        self.assert_equal(info.config[0].value, "df")

        info.config[0].value = "new"

        account.updateConfig(info.config)
        self.assert_equal(account.getConfig("domain"), "new")


    def test_shared(self):
        account = self.manager.create_account("Http", "User", "somepw", adminUser.uid)

        assert self.manager.select_account("Http", adminUser) is account
        assert account.loginname == "User"

        assert self.manager.select_account("Something", adminUser) is None
        assert self.manager.select_account("Http", normalUser) is None

        account.shared = True

        assert self.manager.select_account("Http", normalUser) is account
        assert self.manager.select_account("sdf", normalUser) is None

        self.manager.remove_account(account.aid, "Http", adminUser.uid)

        assert self.manager.select_account("Http", adminUser) is None
