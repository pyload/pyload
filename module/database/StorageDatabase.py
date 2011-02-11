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

from module.database import style
from module.database import DatabaseBackend

class StorageMethods():
    @style.queue
    def setStorage(db, identifier, key, value):
        db.c.execute("SELECT id FROM storage WHERE identifier=? AND key=?", (identifier, key))
        if db.c.fetchone() is not None:
            db.c.execute("UPDATE storage SET value=? WHERE identifier=? AND key=?", (value, identifier, key))
        else:
            db.c.execute("INSERT INTO storage (identifier, key, value) VALUES (?, ?, ?)", (identifier, key, value))
    
    @style.queue
    def getStorage(db, identifier, key=None):
        if key is not None:
            db.c.execute("SELECT value FROM storage WHERE identifier=? AND key=?", (identifier, key))
            row = db.c.fetchone()
            if row is not None:
                return row[0]
        else:
            db.c.execute("SELECT key, value FROM storage WHERE identifier=?", (identifier, ))
            d = {}
            for row in db.c:
                d[row[0]] = row[1]
            return d
    
    @style.queue
    def delStorage(db, identifier, key):
        db.c.execute("DELETE FROM storage WHERE identifier=? AND key=?", (identifier, key))

DatabaseBackend.registerSub(StorageMethods)
