# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: mkaay
"""

from hashlib import sha1
import random

from DatabaseBackend import DatabaseBackend
from DatabaseBackend import style

class UserMethods():
    @style.queue
    def checkAuth(db, user, password):
        c = db.c
        c.execute('SELECT id, name, password, role, permission, template, email FROM "users" WHERE name=?', (user, ))
        r = c.fetchone()
        if not r:
            return {}

        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return {"id": r[0], "name": r[1], "role": r[3],
                    "permission": r[4], "template": r[5], "email": r[6]}
        else:
            return {}

    @style.queue
    def addUser(db, user, password):
        salt = reduce(lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(0, 5)])
        h = sha1(salt + password)
        password = salt + h.hexdigest()

        c = db.c
        c.execute('SELECT name FROM users WHERE name=?', (user, ))
        if c.fetchone() is not None:
            c.execute('UPDATE users SET password=? WHERE name=?', (password, user))
        else:
            c.execute('INSERT INTO users (name, password) VALUES (?, ?)', (user, password))


    @style.queue
    def changePassword(db, user, oldpw, newpw):
        db.c.execute('SELECT id, name, password FROM users WHERE name=?', (user, ))
        r = db.c.fetchone()
        if not r:
            return False

        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + oldpw)
        if h.hexdigest() == pw:
            salt = reduce(lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(0, 5)])
            h = sha1(salt + newpw)
            password = salt + h.hexdigest()

            db.c.execute("UPDATE users SET password=? WHERE name=?", (password, user))
            return True

        return False


    @style.async
    def setPermission(db, user, perms):
        db.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, user))

    @style.async
    def setRole(db, user, role):
        db.c.execute("UPDATE users SET role=? WHERE name=?", (role, user))


    @style.queue
    def listUsers(db):
        db.c.execute('SELECT name FROM users')
        users = []
        for row in db.c:
            users.append(row[0])
        return users

    @style.queue
    def getAllUserData(db):
        db.c.execute("SELECT name, permission, role, template, email FROM users")
        user = {}
        for r in db.c:
            user[r[0]] = {"permission": r[1], "role": r[2], "template": r[3], "email": r[4]}

        return user

    @style.queue
    def removeUser(db, user):
        db.c.execute('DELETE FROM users WHERE name=?', (user, ))

DatabaseBackend.registerSub(UserMethods)
