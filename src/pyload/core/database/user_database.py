# -*- coding: utf-8 -*-

import random
from functools import reduce
from hashlib import sha1

from .database_thread import DatabaseThread, style


# TODO: move to utils and rewrite to use argon2_cffi
def _salted_password(password, salt):
    salt_pw = salt + password
    return sha1(salt_pw.encode()).hexdigest()


class UserDatabaseMethods:
    @style.queue
    def check_auth(self, user, password):
        self.c.execute(
            "SELECT id, name, password, role, permission, template, email FROM users WHERE name=?",
            (user,),
        )
        r = self.c.fetchone()
        if not r:
            return {}

        stored_salt = r[2][:5]
        stored_pw = r[2][5:]

        pw = _salted_password(password, stored_salt)
        if pw != stored_pw:
            return {}

        return {
            "id": r[0],
            "name": r[1],
            "role": r[3],
            "permission": r[4],
            "template": r[5],
            "email": r[6],
        }

    @style.queue
    def add_user(self, user, password):
        salt = reduce(lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(5)])
        salt_pw = salt + _salted_password(password, salt)

        self.c.execute("SELECT name FROM users WHERE name=?", (user,))
        if self.c.fetchone() is not None:
            self.c.execute("UPDATE users SET password=? WHERE name=?", (salt_pw, user))
        else:
            self.c.execute(
                "INSERT INTO users (name, password) VALUES (?, ?)", (user, salt_pw)
            )

    @style.queue
    def change_password(self, user, old_password, new_password):
        self.c.execute("SELECT id, name, password FROM users WHERE name=?", (user,))
        r = self.c.fetchone()
        if not r:
            return False

        stored_salt = r[2][:5]
        stored_pw = r[2][5:]

        oldpw = _salted_password(old_password, stored_salt)
        if oldpw != stored_pw:
            return False

        new_salt = reduce(
            lambda x, y: x + y, [str(random.randint(0, 9)) for i in range(5)]
        )
        newpw = _salted_password(new_password, new_salt)

        self.c.execute("UPDATE users SET password=? WHERE name=?", (newpw, user))
        return True

    @style.async_
    def set_permission(self, user, perms):
        self.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, user))

    @style.async_
    def set_role(self, user, role):
        self.c.execute("UPDATE users SET role=? WHERE name=?", (role, user))

    @style.queue
    def list_users(self):
        self.c.execute("SELECT name FROM users")
        users = []
        for row in self.c:
            users.append(row[0])
        return users

    @style.queue
    def get_all_user_data(self):
        self.c.execute("SELECT id, name, permission, role, template, email FROM users")
        user = {}
        for r in self.c:
            user[r[0]] = {
                "name": r[1],
                "permission": r[2],
                "role": r[3],
                "template": r[4],
                "email": r[5],
            }

        return user

    @style.queue
    def remove_user(self, user):
        self.c.execute("DELETE FROM users WHERE name=?", (user,))


DatabaseThread.register_sub(UserDatabaseMethods)
