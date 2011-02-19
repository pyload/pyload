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

from DatabaseBackend import DatabaseBackend
from DatabaseBackend import style

from hashlib import sha1
import random

class PERMS:
    ADD = 1  # can add packages
    DELETE = 2 # can delete packages
    STATUS = 4   # see and change server status
    SEE_DOWNLOADS = 16 # see queue and collector
    DOWNLOAD = 32  # can download from webinterface
    SETTINGS = 64 # can access settings

class ROLE:
    ADMIN = 0  #admin has all permissions implicit
    USER = 1

def has_permission(current, perms):
    # bytewise or perms before if needed
    return current == (current & perms)

class UserMethods():
    @style.queue
    def checkAuth(db, user, password):
        c = db.c
        c.execute('SELECT id, name, password, role, permission, template FROM "users" WHERE name=?', (user, ))
        r = c.fetchone()
        if not r:
            return {}
        
        salt = r[2][:5]
        pw = r[2][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return {"id": r[0], "name": r[1], "role": r[3], "permission": r[4], "template": r[5]}
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
    def setPermission(db, userid, perms):
        db.c.execute("UPDATE users SET permission=? WHERE id=?", (perms, userid))
    
    @style.queue
    def listUsers(db):
        c = db.c
        c.execute('SELECT name FROM users')
        users = []
        for row in c.fetchall():
            users.append(row[0])
        return users
    
    @style.queue
    def removeUser(db, user):
        db.c.execute('DELETE FROM users WHERE name=?', (user, ))
    

DatabaseBackend.registerSub(UserMethods)
