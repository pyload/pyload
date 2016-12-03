# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.Api import AccountInfo
from pyload.database import DatabaseMethods, queue, async


class AccountMethods(DatabaseMethods):
    @queue
    def loadAccounts(self):
        self.c.execute('SELECT aid, plugin, loginname, owner, activated, shared, password, options FROM accounts')

        return [(AccountInfo(r[0], r[1], r[2], r[3], activated=r[4] is 1, shared=r[5] is 1), r[6], r[7]) for r in
                self.c]

    @queue
    def createAccount(self, plugin, loginname, password, owner):
        self.c.execute('INSERT INTO accounts(plugin, loginname, password, owner) VALUES(?,?,?,?)',
                       (plugin, loginname, password, owner))

        return self.c.lastrowid

    @async
    def saveAccounts(self, data):
        self.c.executemany(
            'UPDATE accounts SET '
            'loginname=?, activated=?, shared=?, password=?, options=? '
            'WHERE aid=?',
            data)

    @async
    def removeAccount(self, aid):
        self.c.execute('DELETE FROM accounts WHERE aid=?', (aid,))

    @queue
    def purgeAccounts(self):
        self.c.execute('DELETE FROM accounts')


AccountMethods.register()
