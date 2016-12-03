# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from unittest import TestCase

from tests.helper.Stubs import Core, adminUser, normalUser

from pyload.AccountManager import AccountManager


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
        self.manager = AccountManager(self.core)

    def test_access(self):
        account = self.manager.createAccount("Http", "User", "somepw", adminUser.uid)

        assert account is self.manager.updateAccount(account.aid, "Http", "User", "newpw", adminUser)
        self.assertEqual(account.password, "newpw")

        assert self.manager.getAccount(account.aid, "Http", adminUser) is account
        assert self.manager.getAccount(account.aid, "Http", normalUser) is None


    def test_config(self):
        account = self.manager.createAccount("Http", "User", "somepw", adminUser.uid)
        info = account.toInfoData()

        self.assertEqual(info.config[0].name, "domain")
        self.assertEqual(info.config[0].value, "")
        self.assertEqual(account.getConfig("domain"), "")

        account.setConfig("domain", "df")

        info = account.toInfoData()
        self.assertEqual(info.config[0].value, "df")

        info.config[0].value = "new"

        account.updateConfig(info.config)
        self.assertEqual(account.getConfig("domain"), "new")


    def test_shared(self):
        account = self.manager.createAccount("Http", "User", "somepw", adminUser.uid)

        assert self.manager.selectAccount("Http", adminUser) is account
        assert account.loginname == "User"

        assert self.manager.selectAccount("Something", adminUser) is None
        assert self.manager.selectAccount("Http", normalUser) is None

        account.shared = True

        assert self.manager.selectAccount("Http", normalUser) is account
        assert self.manager.selectAccount("sdf", normalUser) is None

        self.manager.removeAccount(account.aid, "Http", adminUser.uid)

        assert self.manager.selectAccount("Http", adminUser) is None
