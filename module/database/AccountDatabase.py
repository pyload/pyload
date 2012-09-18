# -*- coding: utf-8 -*-

from module.database import queue, async
from module.database import DatabaseBackend

class AccountMethods:

    @queue
    def loadAccounts(db):
        db.c.execute('SELECT plugin, loginname, activated, password, options FROM accounts;')
        return db.c.fetchall()

    @async
    def saveAccounts(db, data):
        db.c.executemany('INSERT INTO accounts(plugin, loginname, activated, password, options) VALUES(?,?,?,?,?)', data)

    @async
    def removeAccount(db, plugin, loginname):
        db.c.execute('DELETE FROM accounts WHERE plugin=? AND loginname=?', (plugin, loginname))

DatabaseBackend.registerSub(AccountMethods)