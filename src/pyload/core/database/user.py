# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

import random
from builtins import range
from hashlib import sha1
from string import digits, letters

from future import standard_library

from ..datatype.user import UserData
from .backend import DatabaseMethods, async, queue

standard_library.install_aliases()


alphnum = letters + digits


def random_salt():
    return "".join(random.choice(alphnum) for _i in range(0, 5))


class UserMethods(DatabaseMethods):

    @queue
    def add_user(self, user, password, role, permission):
        salt = random_salt()
        h = sha1(salt + password)
        password = salt + h.hexdigest()

        self.c.execute('SELECT name FROM users WHERE name=?', (user,))
        if self.c.fetchone() is not None:
            self.c.execute(
                'UPDATE users SET password=?, role=?, permission=? '
                'WHERE name=?', (password, role, permission, user))
        else:
            self.c.execute(
                'INSERT INTO users (name, role, permission, password) '
                'VALUES (?, ?, ?, ?)', (user, role, permission, password))

    @queue
    def add_debug_user(self, uid):
        # just add a user with uid to db
        try:
            self.c.execute(
                'INSERT INTO users (uid, name, password) VALUES (?, ?, ?)',
                (uid, "debugUser", random_salt()))
        except Exception:
            pass

    @queue
    def get_user_data(self, name=None, uid=None, role=None):
        qry = (
            'SELECT uid, name, email, role, permission, folder, traffic, '
            'dllimit, dlquota, hddquota, user, template FROM "users" WHERE ')

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

        elif role is not None:
            self.c.execute(qry + "role=?", (role,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        return None

    @queue
    def get_all_user_data(self):
        self.c.execute(
            'SELECT uid, name, email, role, permission, folder, traffic, '
            'dllimit, dlquota, hddquota, user, template FROM "users"')
        user = {}
        for r in self.c.fetchall():
            user[r[0]] = UserData(*r)

        return user

    @queue
    def check_auth(self, user, password):
        self.c.execute(
            'SELECT uid, name, email, role, permission, folder, traffic, '
            'dllimit, dlquota, hddquota, user, template, password '
            'FROM "users" WHERE name=?', (user,))
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

    @queue
    def change_password(self, user, oldpw, newpw):
        self.c.execute(
            'SELECT rowid, name, password FROM users WHERE name=?', (user,))
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

            self.c.execute(
                "UPDATE users SET password=? WHERE name=?", (password, user))
            return True

        return False

    # TODO: update methods
    @async
    def remove_user_by_name(self, name):
        self.c.execute("SELECT uid FROM users WHERE name=?", (name,))
        uid = self.c.fetchone()
        if uid:
            # deletes user and all associated accounts
            self.c.execute('DELETE FROM users WHERE user=?', (uid[0],))


UserMethods.register()
