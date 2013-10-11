from module.plugins.Crypter import Crypter as _Crypter


class DeadCrypter(_Crypter):
    __name__ = "DeadCrypter"
    __type__ = "crypter"
    __pattern__ = r""
    __version__ = "0.01"
    __description__ = """Crypter is no longer available"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")
    
    def setup(self):
        self.fail("Crypter is no longer available")
