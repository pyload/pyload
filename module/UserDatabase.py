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

class UserMethods():
    @style.queue
    def checkAuth(db, user, password):
        c = db.createCursor()
        c.execute('SELECT name, password, role, permission, template FROM "users" WHERE name=?', (user, ))
        r = c.fetchone()
        if not r:
            return {}
        
        salt = r[1][:5]
        pw = r[1][5:]
        h = sha1(salt + password)
        if h.hexdigest() == pw:
            return {"name": r[0], "role": r[2], "permission": r[3], "template": r[4]}
    
    @style.queue
    def addUser(db, user, password):
        salt = reduce(lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(0, 5)])
        h = sha1(salt + password)
        password = salt + h.hexdigest()
        
        c = db.createCursor()
        c.execute('SELECT name FROM users WHERE name=?', (user, ))
        if c.fetchone() is not None:
            c.execute('UPDATE users SET password=? WHERE name=?', (password, user))
        else:
            c.execute('INSERT INTO users (name, password) VALUES (?, ?)', (user, password))

DatabaseBackend.registerSub(UserMethods)
