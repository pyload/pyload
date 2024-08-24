# -*- coding: utf-8 -*-
import re
import string
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from pyload.core.utils.misc import random_string

from ..base.account import BaseAccount


def md5_crypt(password, salt=None):
    MAGIC = "$1$"
    BASE64_CHARS = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    if salt is None:
        salt = random_string(8, valid_chars=string.ascii_letters + string.digits + "./")
    else:
        salt = salt[:8]

    salt = salt.encode("ascii")

    if isinstance(password, str):
        password = password.encode("utf-8")

    ctx_a = hashes.Hash(hashes.MD5(), backend=default_backend())
    ctx_a.update(password + MAGIC.encode("ascii") + salt)

    ctx_b = hashes.Hash(hashes.MD5(), backend=default_backend())
    ctx_b.update(password + salt + password)
    intermediate_hash = ctx_b.finalize()

    for i in range(len(password), 0, -16):
        ctx_a.update(intermediate_hash[:16 if i > 16 else i])

    i = len(password)
    while i:
        if i & 1:
            ctx_a.update(b"\0")
        else:
            ctx_a.update(password[0:1])
        i >>= 1

    final_hash = ctx_a.finalize()
    for i in range(1000):
        ctx_c = hashes.Hash(hashes.MD5(), backend=default_backend())
        if i & 1:
            ctx_c.update(password)
        else:
            ctx_c.update(final_hash)

        if i % 3:
            ctx_c.update(salt)

        if i % 7:
            ctx_c.update(password)

        if i & 1:
            ctx_c.update(final_hash)
        else:
            ctx_c.update(password)

        final_hash = ctx_c.finalize()

    encoded_hash = ""
    for a, b, c in ((0, 6, 12), (1, 7, 13), (2, 8, 14), (3, 9, 15), (4, 10, 5)):
        t = (final_hash[a] << 16) | (final_hash[b] << 8) | final_hash[c]
        for i in range(4):
            encoded_hash += BASE64_CHARS[t & 0x3f]
            t >>= 6
    t = final_hash[11]
    for i in range(2):
        encoded_hash += BASE64_CHARS[t & 0x3f]
        t >>= 6

    return f"{MAGIC}{salt.decode()}${encoded_hash}"


class WebshareCz(BaseAccount):
    __name__ = "WebshareCz"
    __type__ = "account"
    __version__ = "0.19"
    __status__ = "testing"

    __description__ = """Webshare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("rush", "radek.senfeld@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VALID_UNTIL_PATTERN = r"<vip_until>(.*)</vip_until>"

    TRAFFIC_LEFT_PATTERN = r"<bytes>(.+?)</bytes>"

    # see https://webshare.cz/apidoc/
    API_URL = "https://webshare.cz/api/"

    def api_request(self, method, **kwargs):
        return self.load(self.API_URL + method + "/", post=kwargs)

    def grab_info(self, user, password, data):
        user_data = self.api_request("user_data", wst=data["wst"])

        expire_date = re.search(self.VALID_UNTIL_PATTERN, user_data).group(1)
        if expire_date:
            validuntil = time.mktime(time.strptime(expire_date, "%Y-%m-%d %H:%M:%S"))
            premium = validuntil > time.time()

        else:
            validuntil = -1
            premium = False

        # trafficleft = self.parse_traffic(re.search(self.TRAFFIC_LEFT_PATTERN, user_data).group(1))

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        salt = self.api_request("salt", username_or_email=user)

        if "<status>OK</status>" not in salt:
            message = re.search(r"<message>(.+?)</message>", salt).group(1)
            self.log_warning(message)
            self.fail_login()

        salt = re.search("<salt>(.*?)</salt>", salt).group(1)
        salt_pw = salt + password

        ctx_sha1 = hashes.Hash(hashes.SHA1(), backend=default_backend())
        ctx_sha1.update(md5_crypt(password, salt=salt).encode())
        password = ctx_sha1.finalize().hex()
        login = self.api_request(
            "login",
            keep_logged_in=1,
            username_or_email=user,
            password=password,
        )

        if "<status>OK</status>" not in login:
            message = re.search(r"<message>(.+?)</message>", salt).group(1)
            self.log_warning(message)
            self.fail_login()

        data["wst"] = re.search("<token>(.+?)</token>", login).group(1)
