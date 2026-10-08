import hmac  # Only imported for its secure string comparison function
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..utils.struct.style import style


# TODO: rewrite using scrypt or argon2_cffi
def _salted_password(password, salt):
    """
    Generate a salted password hash using PBKDF2-HMAC-SHA256.

    Uses 100,000 iterations to derive a 32-byte key from the password and salt.

    Parameters:
        password (str): Plain text password to hash.
        salt (str): Hexadecimal string representing the salt (32 characters).

    Returns:
        str: Concatenated salt and derived key as hexadecimal string.
    """
    # Use PBKDF2 via cryptography to derive a 32-byte key with 100,000 iterations (SHA-256)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=bytes.fromhex(salt),
        iterations=100000,
    )
    dk = kdf.derive(password.encode())
    return salt + dk.hex()


def _gensalt():
    """
    Generate a cryptographically secure random salt.

    Returns:
        str: 32-character hexadecimal string (16 random bytes).
    """
    return os.urandom(16).hex()


def _check_password(hashed, clear):
    """
    Verify a plain text password against a hashed password.

    Extracts the salt from the hashed password, rehashes the plain text
    password with the same salt, and compares the results.

    Parameters:
        hashed (str): Stored password hash (salt + derived key in hex).
        clear (str): Plain text password to verify.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    salt = hashed[:32]
    to_compare = _salted_password(clear, salt)

    # CRITICAL: Always use compare_digest instead of `==` to prevent timing attacks!
    return hmac.compare_digest(hashed, to_compare)


class UserDatabaseMethods:
    @style.queue
    def check_auth(self, username, password):
        """
        Authenticate a user by username and password.

        Retrieves user data from the database and verifies the provided
        password against the stored hash.

        Parameters:
            username (str): Username to authenticate.
            password (str): Plain text password to verify.

        Returns:
            dict: User data dictionary with keys: id, name, role, permission,
                  template, email. Returns empty dict if authentication fails.
        """
        self.c.execute(
            "SELECT id, name, password, role, permission, template, email FROM users WHERE name=?",
            (username,),
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
    def add_user(self, username, password, role=0, perms=0, reset=False):
        """
        Add a new user or update an existing user's credentials.

        Creates a new user with the specified credentials. If the user already
        exists and reset=True, updates their password, role, and permissions.

        Parameters:
            username (str): Username for the new or existing user.
            password (str): Plain text password (will be hashed).
            role (int): User role identifier. Defaults to 0.
            perms (int): User permission flags. Defaults to 0.
            reset (bool): If True, update existing user's credentials.
                         If False, fail if user exists. Defaults to False.

        Returns:
            bool: True if user was created or updated successfully,
                  False if user exists and reset=False.
        """
        salt_pw = _salted_password(password, _gensalt())

        self.c.execute("SELECT name FROM users WHERE name=?", (username,))
        if self.c.fetchone() is not None:
            if reset:
                self.c.execute(
                    "UPDATE users SET password=?, role=?, permission=? WHERE name=?",
                    (salt_pw, role, perms, username),
                )
                return True
            else:
                return False
        else:
            self.c.execute(
                "INSERT INTO users (name, password, role, permission) VALUES (?, ?, ?, ?)",
                (username, salt_pw, role, perms),
            )
            return True

    @style.queue
    def change_password(self, username, old_password, new_password):
        """
        Change a user's password after verifying the old password.

        Validates the old password before updating to the new password.
        The new password is salted and hashed before storage.

        Parameters:
            username (str): Username of the account to update.
            old_password (str): Current password for verification.
            new_password (str): New password to set (will be hashed).

        Returns:
            bool: True if password was changed successfully,
                  False if user not found or old password is incorrect.
        """
        self.c.execute("SELECT id, name, password FROM users WHERE name=?", (username,))
        r = self.c.fetchone()
        if not r:
            return False

        stored_password = r[2]
        if not _check_password(stored_password, old_password):
            return False

        newpw = _salted_password(new_password, _gensalt())

        self.c.execute("UPDATE users SET password=? WHERE name=?", (newpw, username))
        return True

    @style.async_
    def set_permission(self, username, perms):
        """
        Update a user's permission flags.

        This is an asynchronous operation that updates the permission field
        for the specified user.

        Parameters:
            username (str): Username of the account to update.
            perms (int): New permission flags to set.

        Returns:
            None
        """
        self.c.execute("UPDATE users SET permission=? WHERE name=?", (perms, username))

    @style.async_
    def set_role(self, username, role):
        """
        Update a user's role.

        This is an asynchronous operation that updates the role field
        for the specified user.

        Parameters:
            username (str): Username of the account to update.
            role (int): New role identifier to set.

        Returns:
            None
        """
        self.c.execute("UPDATE users SET role=? WHERE name=?", (role, username))

    @style.queue
    def set_user_permission(self, username, perms, role):
        """
        Update a user's permission flags and role atomically.

        Returns whether an existing user's authorization values changed.
        """
        self.c.execute(
            "SELECT permission, role FROM users WHERE name=?",
            (username,),
        )
        current = self.c.fetchone()
        if not current:
            return False

        if current == (perms, role):
            return False

        self.c.execute(
            "UPDATE users SET permission=?, role=? WHERE name=?",
            (perms, role, username),
        )
        return True

    @style.queue
    def user_exists(self, username):
        """
        Check if a user exists in the database.

        Parameters:
            username (str): Username to check.

        Returns:
            bool: True if user exists, False otherwise.
        """
        self.c.execute("SELECT name FROM users WHERE name=?", (username,))
        return self.c.fetchone() is not None

    @style.queue
    def list_users(self):
        """
        Retrieve a list of all usernames in the database.

        Returns:
            list: List of username strings.
        """
        self.c.execute("SELECT name FROM users")
        users = []
        for row in self.c:
            users.append(row[0])
        return users

    @style.queue
    def get_all_user_data(self):
        """
        Retrieve complete data for all users.

        Returns:
            dict: Dictionary mapping user IDs to user data dictionaries.
                  Each user data dict contains: name, permission, role,
                  template, email.
        """
        self.c.execute("SELECT id, name, permission, role, template, email FROM users")
        user_data = {}
        for r in self.c:
            user_data[r[0]] = {
                "name": r[1],
                "permission": r[2],
                "role": r[3],
                "template": r[4],
                "email": r[5],
            }

        return user_data

    @style.queue
    def get_user_id(self, username):
        """
        Retrieve the user ID for a given username.

        Parameters:
            username (str): Username to look up.

        Returns:
            int or bool: User ID if found, False if user does not exist.
        """
        self.c.execute("SELECT id, name FROM users WHERE name=?", (username,))
        r = self.c.fetchone()
        if not r:
            return False
        else:
            return r[0]

    @style.queue
    def get_user_by_id(self, user_id):
        """
        Get user data by user ID.

        Parameters:
            user_id (int): ID of the user to retrieve.

        Returns:
            dict: User data dictionary with keys: name, permission, role,
                  template, email. Returns empty dict if user not found.
        """
        self.c.execute(
            "SELECT id, name, permission, role, template, email FROM users WHERE id=?",
            (user_id,),
        )
        r = self.c.fetchone()
        if not r:
            return {}
        return {
            "id": r[0],
            "name": r[1],
            "permission": r[2],
            "role": r[3],
            "template": r[4],
            "email": r[5],
        }

    @style.queue
    def remove_user(self, username):
        """
        Delete a user from the database.

        Parameters:
            username (str): Username of the account to delete.

        Returns:
            bool: True if user was deleted (rowcount > 0),
                  False if user was not found.
        """
        self.c.execute("DELETE FROM users WHERE name=?", (username,))
        return self.c.rowcount > 0
