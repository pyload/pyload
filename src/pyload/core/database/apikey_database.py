import hmac  # Only imported for its secure string comparison function
import time
from typing import Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from wtforms.validators import Optional

from ..utils.struct.style import style


def _hashed_key(apikey: str) -> str:
    # Use SHA256 hashing for maximum speed (source apikey uses high entropy so no need for salt)
    hasher = hashes.Hash(hashes.SHA256(), backend=default_backend())
    hasher.update(apikey.encode())
    return hasher.finalize().hex()


def _check_key(hashed, clear) -> bool:
    to_compare = _hashed_key(clear)

    # CRITICAL: Always use compare_digest instead of `==` to prevent timing attacks!
    return hmac.compare_digest(hashed, to_compare)


class ApikeyDatabaseMethods:
    """Database methods for managing API keys"""

    @style.queue
    def create_user_apikey(self, user_id: int, name: str, expires: int, apikey: str) -> int:
        """
        Create a new API key for a user.

        :param user_id: ID of the user
        :param name: Name/description of the API key
        :param expires: Expiration timestamp or 0
        :param apikey: The API key
        :return: API key ID
        """
        key_hash = _hashed_key(apikey)
        self.c.execute(
            """INSERT INTO apikeys (id, user_id, name, key_hash, created_at, expires_at)
               VALUES (
                  (SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM apikeys WHERE id = 1)
                   UNION
                   SELECT t1.id + 1 FROM apikeys t1 LEFT JOIN apikeys t2 ON t1.id + 1 = t2.id WHERE t2.id IS NULL
                   ORDER BY 1 LIMIT 1),
                   ?, ?, ?, ?, ?
               )""",
            (user_id, name, key_hash, int(time.time() * 1000), expires),
        )
        return self.c.lastrowid

    @style.queue
    def get_user_apikeys(self, user_id: int) -> list[dict]:
        """
        Get all API keys for a user.

        :param user_id: ID of the user
        :return: list of API key dicts
        """
        self.c.execute(
            "SELECT id, user_id, name, created_at, expires_at, last_used FROM apikeys WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        )
        keys = []
        for r in self.c:
            keys.append({
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "created_at": r[3],
                "expires_at": r[4],
                "last_used": r[5],
            })
        return keys

    @style.queue
    def delete_user_apikey(self, user_id: int, key_id: int) -> bool:
        """
        Delete an API key belonging to a specific user.

        :param user_id: ID of the user
        :param key_id: ID of the API key
        :return: True if deleted, False otherwise
        """
        self.c.execute(
            "DELETE FROM apikeys WHERE id=? AND user_id=?",
            (key_id, user_id),
        )
        return self.c.rowcount > 0

    @style.queue
    def check_apikey(self, key_id: int, apikey: str) -> dict:
        """
        Get API key information by key hash.

        :param key_id: ID of the API key
        :param apikey: The API key
        :return: dict with key info or empty dict if not found
        """
        self.c.execute(
            "SELECT id, user_id, name, key_hash, created_at, expires_at, last_used FROM apikeys WHERE id=?",
            (key_id,),
        )
        r = self.c.fetchone()
        if not r:
            return {}

        stored_key_hash = r[3]
        if not _check_key(stored_key_hash, apikey):
            return {}

        return {
            "id": r[0],
            "user_id": r[1],
            "name": r[2],
            "created_at": r[4],
            "expires_at": r[5],
            "last_used": r[6],
        }

    @style.async_
    def update_apikey_last_used(self, key_id: int) -> None:
        """
        Update the last_used timestamp for an API key.

        :param key_id: ID of the API key
        """
        self.c.execute(
            "UPDATE apikeys SET last_used=? WHERE id=?",
            (int(time.time() * 1000), key_id),
        )
