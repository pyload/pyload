# -*- coding: utf-8 -*-

import hashlib

from pyload.core.utils.convert import to_bytes, to_str

from ..base.account import BaseAccount
from ..downloaders.MegaCoNz import MegaClient, MegaCrypto


class MegaCoNz(BaseAccount):
    __name__ = "MegaCoNz"
    __type__ = "account"
    __version__ = "0.08"
    __status__ = "testing"

    __description__ = """Mega.co.nz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def grab_info(self, user, password, data):
        validuntil = -1
        trafficleft = None
        premium = False

        mega = MegaClient(self, None)

        res = mega.api_request(a="uq", xfer=1, pro=1)  #: user quota details
        if isinstance(res, dict):
            premium = res.get("utype", 0) > 0
            if premium:
                validuntil = res.get("suntil", None)
                trafficleft = (
                    res.get("mxfer", 0) - res.get("caxfer", 0) - res.get("csxfer", 0)
                )

            # if res['rtt']:
            #     self.log_debug(f"Tranfare history:{res['tah']}")

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        user = user.lower()
        mega = MegaClient(self, None)

        mega_session_cache = self.db.retrieve("mega_session_cache") or {}
        if user in mega_session_cache:
            data["mega_session_id"] = mega_session_cache[user]

            res = mega.api_request(a="ug", xfer=1, pro=1)  #: ug is for user details
            if isinstance(res, dict) and res.get("email", None) == user:
                self.skip_login()

            else:
                del mega_session_cache[user]
                self.db.store("mega_session_cache", mega_session_cache)

        sid = None
        data["mega_session_id"] = sid

        res = mega.api_request(a="us0", user=user)  #: us0 is `prelogin` command
        if res["v"] == 1:  #: v1 account
            password_key = self.get_password_key(password)
            user_hash = self.get_user_hash_v1(user, password_key)

        elif res["v"] == 2:  #: v2 account
            salt = MegaCrypto.base64_decode(res["s"])
            pbkdf = hashlib.pbkdf2_hmac("SHA512", to_bytes(password, "utf-8"), salt, 100_000, 32)

            password_key = MegaCrypto.bytes_to_a32(pbkdf[:16])
            user_hash = (
                to_str(MegaCrypto.base64_encode(pbkdf[16:]), "ascii").replace("=", "")
            )

        else:
            self.log_error(
                self._("Unsupported user account version ({})").format(res["v"])
            )
            self.fail_login()

        res = mega.api_request(a="us", user=user, uh=user_hash)  #: us if for user sign-in
        if isinstance(res, int) or isinstance(res, dict) and "e" in res:
            self.fail_login()

        master_key = MegaCrypto.decrypt_key(res["k"], password_key)

        if "tsid" in res:
            tsid = MegaCrypto.base64_decode(res["tsid"])
            if (
                MegaCrypto.a32_to_bytes(
                    MegaCrypto.encrypt_key(
                        MegaCrypto.bytes_to_a32(tsid[:16]), master_key
                    )
                )
                == tsid[-16:]
            ):
                sid = res["tsid"]

            else:
                self.fail_login()

        elif "csid" in res:
            privk = MegaCrypto.a32_to_bytes(
                MegaCrypto.decrypt_key(res["privk"], master_key)
            )
            rsa_private_key = [0, 0, 0, 0]

            for i in range(4):
                l = ((privk[0] * 256 + privk[1] + 7) // 8) + 2
                if l > len(privk):
                    self.fail_login()
                rsa_private_key[i] = self.mpi_to_int(privk[:l])
                privk = privk[l:]

            if len(privk) >= 16:
                self.fail_login()

            encrypted_sid = self.mpi_to_int(
                MegaCrypto.base64_decode(res["csid"])
            )
            sid = "{:x}".format(
                pow(
                    encrypted_sid,
                    rsa_private_key[2],
                    rsa_private_key[0] * rsa_private_key[1],
                )
            )
            sid = "0" * (-len(sid) % 2) + sid
            sid = bytes([(int(sid[i : i + 2], 16)) for i in range(0, len(sid), 2)])
            sid = to_str(MegaCrypto.base64_encode(sid[:43]), "ascii").replace("=", "")

        else:
            self.fail_login()

        data["mega_session_id"] = sid
        mega_session_cache[user] = sid
        self.db.store("mega_session_cache", mega_session_cache)

    def get_password_key(self, password):
        password_key = MegaCrypto.a32_to_bytes(
            [0x93C467E3, 0x7DB0C7A4, 0xD1BE3F81, 0x0152CB56]
        )
        password_a32 = MegaCrypto.bytes_to_a32(to_bytes(password, "utf-8"))
        for c in range(0x10000):
            for j in range(0, len(password_a32), 4):
                key = [0, 0, 0, 0]
                for i in range(4):
                    if i + j < len(password_a32):
                        key[i] = password_a32[i + j]
                password_key = MegaCrypto.cbc_encrypt(password_key, key)

        return MegaCrypto.bytes_to_a32(password_key)

    def get_user_hash_v1(self, user, password_key):
        user_a32 = MegaCrypto.bytes_to_a32(to_bytes(user, "utf-8"))
        user_hash = [0, 0, 0, 0]
        for i in range(len(user_a32)):
            user_hash[i % 4] ^= user_a32[i]

        user_hash = MegaCrypto.a32_to_bytes(user_hash)
        for i in range(0x4000):
            user_hash = MegaCrypto.cbc_encrypt(user_hash, password_key)

        user_hash = MegaCrypto.bytes_to_a32(user_hash)

        return to_str(MegaCrypto.a32_to_base64((user_hash[0], user_hash[2])), "ascii")

    def mpi_to_int(self, s):
        """
        Convert GCRYMPI_FMT_PGP bignum format to integer.
        """
        return int("".join("{:02x}".format(s[2:][x]) for x in range(len(s[2:]))), 16)
