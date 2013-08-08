# -*- coding: utf-8 -*-

from pyload.Api import AccountInfo
from pyload.database import DatabaseMethods, queue, async


class AccountMethods(DatabaseMethods):
    @queue
    def loadAccounts(self):
        self.c.execute('SELECT plugin, loginname, owner, activated, shared, password, options FROM accounts')

        return [(AccountInfo(r[0], r[1], r[2], activated=r[3] is 1, shared=r[4] is 1), r[5], r[6]) for r in self.c]

    @async
    def saveAccounts(self, data):

        self.c.executemany(
            'INSERT INTO accounts(plugin, loginname, owner, activated, shared, password, options) VALUES(?,?,?,?,?,?,?)',
            data)

    @async
    def removeAccount(self, plugin, loginname):
        self.c.execute('DELETE FROM accounts WHERE plugin=? AND loginname=?', (plugin, loginname))

    @queue
    def purgeAccounts(self):
        self.c.execute('DELETE FROM accounts')

AccountMethods.register()