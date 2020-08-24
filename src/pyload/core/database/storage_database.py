# -*- coding: utf-8 -*-

from ..utils.struct.style import style


class StorageDatabaseMethods:
    @style.queue
    def set_storage(self, identifier, key, value):
        self.c.execute(
            "SELECT id FROM storage WHERE identifier=? AND key=?", (identifier, key)
        )
        if self.c.fetchone() is not None:
            self.c.execute(
                "UPDATE storage SET value=? WHERE identifier=? AND key=?",
                (value, identifier, key),
            )
        else:
            self.c.execute(
                "INSERT INTO storage (identifier, key, value) VALUES (?, ?, ?)",
                (identifier, key, value),
            )

    @style.queue
    def get_storage(self, identifier, key=None):
        if key is not None:
            self.c.execute(
                "SELECT value FROM storage WHERE identifier=? AND key=?",
                (identifier, key),
            )
            row = self.c.fetchone()
            if row is not None:
                return row[0]
        else:
            self.c.execute(
                "SELECT key, value FROM storage WHERE identifier=?", (identifier,)
            )
            d = {}
            for row in self.c:
                d[row[0]] = row[1]
            return d

    @style.queue
    def del_storage(self, identifier, key):
        self.c.execute(
            "DELETE FROM storage WHERE identifier=? AND key=?", (identifier, key)
        )
