# -*- coding: utf-8 -*-

###############################################################################
#   Copyright(c) 2008-2012 pyLoad Team
#   http://www.pyload.org
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from hashlib import sha1
from string import letters, digits
from random import choice

alphnum = letters+digits

from module.Api import UserData

from DatabaseBackend import DatabaseMethods, queue, async

def random_salt():
    return "".join(choice(alphnum) for x in range(0,5))

class UserMethods(DatabaseMethods):

    @queue
    def addUser(self, user, password):
        salt = random_salt()
        h = sha1(salt + password)
        password = salt + h.hexdigest()

        self.c.execute('SELECT name FROM users WHERE name=?', (user, ))
        if self.c.fetchone() is not None:
            self.c.execute('UPDATE users SET password=? WHERE name=?', (password, user))
        else:
            self.c.execute('INSERT INTO users (name, password) VALUES (?, ?)', (user, password))

    @queue
    def getUserData(self, name=None, uid=None):
        qry = ('SELECT uid, name, email, role, permission, folder, traffic, dllimit, dlquota, '
               'hddquota, user, template FROM "users" WHERE ')

        if name is not None:
            self.c.execute(qry + "name=?", (name,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        elif uid is not None:
            self.c.execute(qry + "uid=?", (uid,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        return None

    @queue
    def getAllUserData(self):
        self.c.execute('SELECT uid, name, email, role, permission, folder, traffic, dllimit, dlquota, '
                       'hddquota, user, template FROM "users"')
        user = {}
        for r in self.c:
            user[r[0]] = UserData(*r)

        return user


    @queue
    def checkAuth(self, user, password):
        self.c.execute('SELECT uid, name, email, role, permission, folder, traffic, dllimit, dlquota, '
                       'hddquota, user, template, password FROM "users" WHERE name=?', (user, ))
        r = self.c.fetchone()
        if not r:
            return None
        salt = r[-1][:5]
        pw = r[-1][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return UserData(*r[:-1])
        else:
            return None

    @queue #TODO
    def changePassword(self, user, oldpw, newpw):
        self.c.execute('SELECT rowid, name, password FROM users WHERE name=?', (user, ))
        r = self.c.fetchone()
        if not r:
            return False

        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + oldpw)
        if h.hexdigest() == pw:
            salt = random_salt()
            h = sha1(salt + newpw)
            password = salt + h.hexdigest()

            self.c.execute("UPDATE users SET password=? WHERE name=?", (password, user))
            return True

        return False

    @async
    def setPermission(self, user, perms):
        self.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, user))

    @async
    def setRole(self, user, role):
        self.c.execute("UPDATE users SET role=? WHERE name=?", (role, user))

    # TODO update methods

    @async
    def removeUser(self, uid=None):
        # deletes user and all associated accounts
        self.c.execute('DELETE FROM users WHERE user=?', (uid, ))

UserMethods.register()
