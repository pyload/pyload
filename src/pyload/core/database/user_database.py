# -*- coding: utf-8 -*-

import hashlib
import os

from ..utils.struct.style import style


# TODO: rewrite using scrypt or argon2_cffi
def _salted_password(password, salt):
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100000)
    return salt + dk.hex()


def _gensalt():
    return os.urandom(16).hex()


def _check_password(hashed, clear):
    salt = hashed[:32]
    to_compare = _salted_password(clear, salt)

    return hashed == to_compare


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

        stored_password = r[2]
        if not _check_password(stored_password, password):
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
    def add_user(self, user, password, role=0, perms=0, reset=False):
        salt_pw = _salted_password(password, _gensalt())

        self.c.execute("SELECT name FROM users WHERE name=?", (user,))
        if self.c.fetchone() is not None:
            if reset:
                self.c.execute(
                    "UPDATE users SET password=?, role=?, permission=? WHERE name=?",
                    (salt_pw, role, perms, user),
                )
                return True
            else:
                return False
        else:
            self.c.execute(
                "INSERT INTO users (name, password, role, permission) VALUES (?, ?, ?, ?)",
                (user, salt_pw, role, perms),
            )
            return True

    @style.queue
    def change_password(self, user, old_password, new_password):
        self.c.execute("SELECT id, name, password FROM users WHERE name=?", (user,))
        r = self.c.fetchone()
        if not r:
            return False

        stored_password = r[2]
        if not _check_password(stored_password, old_password):
            return False

        newpw = _salted_password(new_password, _gensalt())

        self.c.execute("UPDATE users SET password=? WHERE name=?", (newpw, user))
        return True

    @style.async_
    def set_permission(self, user, perms):
        self.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, user))

    @style.async_
    def set_role(self, user, role):
        self.c.execute("UPDATE users SET role=? WHERE name=?", (role, user))

    @style.queue
    def user_exists(self, user):
        self.c.execute("SELECT name FROM users WHERE name=?", (user,))
        return self.c.fetchone() is not None

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
