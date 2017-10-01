# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from hashlib import sha1

import bcrypt
from future import standard_library

from pyload.core.database.backend import DatabaseMethods, async, queue
from pyload.core.datatype.user import UserData
from pyload.utils.convert import to_bytes

standard_library.install_aliases()


class UserMethods(DatabaseMethods):

    @queue
    def add_user(self, user, password, role, permission):
        hashed_pw = bcrypt.hashpw(to_bytes(password), bcrypt.gensalt())

        self.c.execute('SELECT name FROM users WHERE name=?', (user,))
        if self.c.fetchone() is not None:
            self.c.execute(
                'UPDATE users SET password=?, role=?, permission=? '
                'WHERE name=?', (hashed_pw, role, permission, user))
        else:
            self.c.execute(
                'INSERT INTO users (name, role, permission, password) '
                'VALUES (?, ?, ?, ?)', (user, role, permission, hashed_pw))

    @queue
    def add_debug_user(self, uid):
        # just add a user with uid to db
        try:
            self.c.execute(
                'INSERT INTO users (uid, name, password) VALUES (?, ?, ?)',
                (uid, 'debugUser', bcrypt.gensalt()))
        except Exception:
            pass

    @queue
    def get_user_data(self, name=None, uid=None, role=None):
        qry = (
            'SELECT uid, name, email, role, permission, folder, traffic, '
            'dllimit, dlquota, hddquota, user, template FROM "users" WHERE ')

        if name is not None:
            self.c.execute(qry + 'name=?', (name,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        elif uid is not None:
            self.c.execute(qry + 'uid=?', (uid,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        elif role is not None:
            self.c.execute(qry + 'role=?', (role,))
            r = self.c.fetchone()
            if r:
                return UserData(*r)

        return

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
            return
        salt = r[-1][:5]
        pw = r[-1][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return UserData(*r[:-1])
        else:
            return

    @queue
    def change_password(self, user, oldpw, newpw):
        self.c.execute(
            'SELECT rowid, name, password FROM users WHERE name=?', (user,))
        r = self.c.fetchone()
        if not r:
            return False

        hashed_pw = r[2]
        if bcrypt.checkpw(to_bytes(oldpw), hashed_pw):
            new_hpw = bcrypt.hashpw(to_bytes(newpw), bcrypt.gensalt())
            self.c.execute(
                'UPDATE users SET password=? WHERE name=?', (new_hpw, user))
            return True

        return False

    # TODO: update methods
    @async
    def remove_user_by_name(self, name):
        self.c.execute('SELECT uid FROM users WHERE name=?', (name,))
        uid = self.c.fetchone()
        if uid:
            # deletes user and all associated accounts
            self.c.execute('DELETE FROM users WHERE user=?', (uid[0],))


UserMethods.register()
