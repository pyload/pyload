# -*- coding: utf-8 -*-

import random
import re

from Crypto.Cipher import AES
from Crypto.Util import Counter
from array import array
from base64 import standard_b64decode
from os import remove

from pyload.utils import json_loads, json_dumps
from pyload.plugins.Hoster import Hoster


class MegaNz(Hoster):
    __name__ = "MegaNz"
    __type__ = "hoster"
    __version__ = "0.14"

    __pattern__ = r'https?://([a-z0-9]+\.)?mega\.co\.nz/#!([a-zA-Z0-9!_\-]+)'

    __description__ = """Mega.co.nz hoster plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "ranan@pyload.org"

    API_URL = "https://g.api.mega.co.nz/cs?id=%d"
    FILE_SUFFIX = ".crypted"


    def b64_decode(self, data):
        data = data.replace("-", "+").replace("_", "/")
        return standard_b64decode(data + '=' * (-len(data) % 4))

    def getCipherKey(self, key):
        """ Construct the cipher key from the given data """
        a = array("I", key)
        key_array = array("I", [a[0] ^ a[4], a[1] ^ a[5], a[2] ^ a[6], a[3] ^ a[7]])
        return key_array

    def callApi(self, **kwargs):
        """ Dispatch a call to the api, see https://mega.co.nz/#developers """
        # generate a session id, no idea where to obtain elsewhere
        uid = random.randint(10 << 9, 10 ** 10)

        resp = self.load(self.API_URL % uid, post=json_dumps([kwargs]))
        self.logDebug("Api Response: " + resp)
        return json_loads(resp)

    def decryptAttr(self, data, key):

        cbc = AES.new(self.getCipherKey(key), AES.MODE_CBC, "\0" * 16)
        attr = cbc.decrypt(self.b64_decode(data))
        self.logDebug("Decrypted Attr: " + attr)
        if not attr.startswith("MEGA"):
            self.fail(_("Decryption failed"))

        # Data is padded, 0-bytes must be stripped
        return json_loads(attr.replace("MEGA", "").rstrip("\0").strip())

    def decryptFile(self, key):
        """  Decrypts the file at lastDownload` """

        # upper 64 bit of counter start
        n = key[16:24]

        # convert counter to long and shift bytes
        ctr = Counter.new(128, initial_value=long(n.encode("hex"), 16) << 64)
        cipher = AES.new(self.getCipherKey(key), AES.MODE_CTR, counter=ctr)

        self.pyfile.setStatus("decrypting")

        file_crypted = self.lastDownload
        file_decrypted = file_crypted.rsplit(self.FILE_SUFFIX)[0]
        f = open(file_crypted, "rb")
        df = open(file_decrypted, "wb")

        # TODO: calculate CBC-MAC for checksum

        size = 2 ** 15  # buffer size, 32k
        while True:
            buf = f.read(size)
            if not buf:
                break

            df.write(cipher.decrypt(buf))

        f.close()
        df.close()
        remove(file_crypted)

        self.lastDownload = file_decrypted

    def process(self, pyfile):

        key = None

        # match is guaranteed because plugin was chosen to handle url
        node = re.match(self.__pattern__, pyfile.url).group(2)
        if "!" in node:
            node, key = node.split("!")

        self.logDebug("File id: %s | Key: %s" % (node, key))

        if not key:
            self.fail(_("No file key provided in the URL"))

        # g is for requesting a download url
        # this is similar to the calls in the mega js app, documentation is very bad
        dl = self.callApi(a="g", g=1, p=node, ssl=1)[0]

        if "e" in dl:
            e = dl['e']
            # ETEMPUNAVAIL (-18): Resource temporarily not available, please try again later
            if e == -18:
                self.retry()
            else:
                self.fail(_("Error code:") + e)

        # TODO: map other error codes, e.g
        # EACCESS (-11): Access violation (e.g., trying to write to a read-only share)

        key = self.b64_decode(key)
        attr = self.decryptAttr(dl['at'], key)

        pyfile.name = attr['n'] + self.FILE_SUFFIX

        self.download(dl['g'])
        self.decryptFile(key)

        # Everything is finished and final name can be set
        pyfile.name = attr['n']
