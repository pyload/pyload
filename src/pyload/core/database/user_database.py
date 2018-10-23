# -*- coding: utf-8 -*-
# @author: mkaay

import random
from builtins import object, range, str
from functools import reduce
from hashlib import sha1

from .database_thread import DatabaseThread, style


class UserMethods(object):
    @style.queue
    def checkAuth(self, user, password):
        self.c.execute(
            'SELECT id, name, password, role, permission, template, email FROM "users" WHERE name=?',
            (user,),
        )
        r = self.c.fetchone()
        if not r:
            return {}

        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return {
                "id": r[0],
                "name": r[1],
                "role": r[3],
                "permission": r[4],
                "template": r[5],
                "email": r[6],
            }
        else:
            return {}

    @style.queue
    def addUser(self, user, password):
        salt = reduce(
            lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(0, 5)]
        )
        h = sha1(salt + password)
        password = salt + h.hexdigest()

        self.c.execute("SELECT name FROM users WHERE name=?", (user,))
        if self.c.fetchone() is not None:
            self.c.execute("UPDATE users SET password=? WHERE name=?", (password, user))
        else:
            self.c.execute(
                "INSERT INTO users (name, password) VALUES (?, ?)", (user, password)
            )

    @style.queue
    def changePassword(self, user, oldpw, newpw):
        self.c.execute("SELECT id, name, password FROM users WHERE name=?", (user,))
        r = self.c.fetchone()
        if not r:
            return False

        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + oldpw)
        if h.hexdigest() == pw:
            salt = reduce(
                lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(0, 5)]
            )
            h = sha1(salt + newpw)
            password = salt + h.hexdigest()

            self.c.execute("UPDATE users SET password=? WHERE name=?", (password, user))
            return True

        return False

    @style.async_
    def setPermission(self, user, perms):
        self.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, user))

    @style.async_
    def setRole(self, user, role):
        self.c.execute("UPDATE users SET role=? WHERE name=?", (role, user))

    @style.queue
    def listUsers(self):
        self.c.execute("SELECT name FROM users")
        users = []
        for row in self.c:
            users.append(row[0])
        return users

    @style.queue
    def getAllUserData(self):
        self.c.execute("SELECT name, permission, role, template, email FROM users")
        user = {}
        for r in self.c:
            user[r[0]] = {
                "permission": r[1],
                "role": r[2],
                "template": r[3],
                "email": r[4],
            }

        return user

    @style.queue
    def removeUser(self, user):
        self.c.execute("DELETE FROM users WHERE name=?", (user,))


DatabaseThread.registerSub(UserMethods)
