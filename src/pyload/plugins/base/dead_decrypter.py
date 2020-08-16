# -*- coding: utf-8 -*-


from .decrypter import BaseDecrypter


class DeadDecrypter(BaseDecrypter):
    __name__ = "DeadDecrypter"
    __type__ = "decrypter"
    __version__ = "0.14"
    __status__ = "stable"

    __pattern__ = r"^unmatchable$"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Crypter is no longer available"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    @classmethod
    def get_info(cls, *args, **kwargs):
        info = super(DeadDecrypter, cls).get_info(*args, **kwargs)
        info["status"] = 1
        return info

    def setup(self):
        self.offline(self._("Crypter is no longer available"))
